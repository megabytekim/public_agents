# pykrx KRX Fallback Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** KRX 로그인 필수화(2025-12-27~)로 인해 작동하지 않는 pykrx 함수들을 대안으로 교체하고, 대안 없는 함수는 제거

**Architecture:**
- 대안 있는 함수 → Naver Finance fallback 추가
- 대안 없는 함수 → `deprecated.py`로 이동 후 `data_fetcher.py`에서 제거
- 명확한 문서화로 사용자 혼란 방지

**Tech Stack:** Python, requests, BeautifulSoup, 기존 web_scraper.py 활용

---

## 검증 결과 요약 (2026-01-19)

### pykrx 함수 현황

| 함수 | 상태 | 데이터 소스 | 대안 | 조치 |
|------|------|------------|------|------|
| `get_market_ohlcv_by_date()` | ✅ 작동 | Naver | - | 유지 |
| `get_market_ticker_name()` | ✅ 작동 | Naver | - | 유지 |
| `get_market_ticker_list()` | ❌ 불가 | KRX | Naver | **Fallback 추가** |
| `get_market_fundamental()` | ❌ 불가 | KRX | Naver | **Fallback 추가** |
| `get_market_cap()` | ❌ 불가 | KRX | Naver | **Fallback 추가** |
| `get_market_trading_value_by_date()` | ❌ 불가 | KRX | ❌ 없음 | **제거** |
| `get_shorting_status_by_date()` | ❌ 불가 | KRX | ❌ 없음 | **제거** |

### 대안 불가능한 데이터 (KRX 전용)

다음 데이터는 KRX 로그인 없이는 수집 불가능합니다:

| 데이터 | 설명 | 이유 |
|--------|------|------|
| **투자자별 매매동향** | 기관/외국인/개인 순매수 | KRX 전용 데이터 |
| **공매도 현황** | 공매도량, 잔고 | KRX 전용 데이터 |
| **거래대금** | 일별 거래대금 | KRX 전용 (Naver는 거래량만) |
| **상장주식수** | 발행주식 총수 | KRX 전용 |
| **외국인보유주식수** | 외국인 보유 주식 수 | KRX 전용 (비율만 Naver 제공) |

> **Note:** 이 데이터가 필요한 경우 KRX Data Marketplace 유료 API 또는 증권사 API 사용 필요

---

## Task 1: 대안 없는 함수 deprecated.py로 이동

**Files:**
- Create: `utils/deprecated.py`
- Modify: `utils/data_fetcher.py`
- Modify: `utils/__init__.py`

**Step 1: deprecated.py 생성**

```python
# utils/deprecated.py
"""
Deprecated functions due to KRX login requirement (2025-12-27~)

These functions no longer work because KRX (Korea Exchange) now requires
authentication for data access. No alternative data source is available.

If you need this data, consider:
1. KRX Data Marketplace paid API
2. Securities company APIs (증권사 API)
3. Bloomberg/Refinitiv terminals
"""
from datetime import datetime, timedelta
from typing import Optional
import warnings

import pandas as pd
from pykrx import stock


def get_investor_trading(
    ticker: str,
    days: int = 20
) -> Optional[pd.DataFrame]:
    """
    [DEPRECATED] 투자자별 순매수 - 2025-12-27부터 작동 안함

    ⚠️ KRX 로그인 필수화로 더 이상 사용 불가
    ⚠️ 대안 데이터 소스 없음

    Args:
        ticker: 종목코드
        days: 조회 일수

    Returns:
        None (항상)
    """
    warnings.warn(
        "get_investor_trading() is deprecated since 2025-12-27. "
        "KRX now requires login. No alternative available.",
        DeprecationWarning,
        stacklevel=2
    )
    return None


def get_short_selling(
    ticker: str,
    days: int = 20
) -> Optional[pd.DataFrame]:
    """
    [DEPRECATED] 공매도 현황 - 2025-12-27부터 작동 안함

    ⚠️ KRX 로그인 필수화로 더 이상 사용 불가
    ⚠️ 대안 데이터 소스 없음

    Args:
        ticker: 종목코드
        days: 조회 일수

    Returns:
        None (항상)
    """
    warnings.warn(
        "get_short_selling() is deprecated since 2025-12-27. "
        "KRX now requires login. No alternative available.",
        DeprecationWarning,
        stacklevel=2
    )
    return None
```

**Step 2: data_fetcher.py에서 해당 함수 제거**

`utils/data_fetcher.py`에서 `get_investor_trading()`과 `get_short_selling()` 함수 삭제 (라인 212-276)

**Step 3: __init__.py 업데이트 (있는 경우)**

```python
# utils/__init__.py
from utils.data_fetcher import (
    get_ohlcv,
    get_ticker_name,
    get_ticker_list,
    get_fundamental,
    get_market_cap,
)

# Deprecated - import with warning
from utils.deprecated import (
    get_investor_trading,
    get_short_selling,
)
```

**Step 4: Commit**

```bash
git add utils/deprecated.py utils/data_fetcher.py utils/__init__.py
git commit -m "refactor: move unsupported KRX functions to deprecated.py"
```

---

## Task 2: web_scraper.py에 시가총액 파싱 추가

**Files:**
- Modify: `utils/web_scraper.py`
- Test: `tests/test_web_scraper.py` (신규)

**Step 1: 기존 get_naver_stock_info 확인**

현재 반환 필드:
- `price`, `change`, `change_percent`
- `per`, `pbr`
- `volume`, `trade_value`
- `foreign_ratio`

**Step 2: 시가총액 파싱 추가**

```python
# web_scraper.py의 get_naver_stock_info() 함수에 추가
market_cap_elem = soup.select_one('em#_market_sum')
if market_cap_elem:
    market_cap_text = market_cap_elem.get_text(strip=True).replace(',', '')
    if '조' in market_cap_text:
        parts = market_cap_text.replace('조', ' ').replace('억', '').split()
        jo = int(parts[0]) if parts[0] else 0
        eok = int(parts[1]) if len(parts) > 1 and parts[1] else 0
        result['market_cap'] = jo * 10000 + eok  # 억 단위
    elif '억' in market_cap_text:
        result['market_cap'] = int(market_cap_text.replace('억', ''))
```

**Step 3: 테스트 작성**

```python
# tests/test_web_scraper.py
def test_get_naver_stock_info_market_cap():
    """시가총액 파싱 테스트"""
    from utils.web_scraper import get_naver_stock_info
    result = get_naver_stock_info("005930")

    assert result is not None
    assert 'market_cap' in result
    assert result['market_cap'] > 0
```

**Step 4: 테스트 실행**

```bash
pytest tests/test_web_scraper.py::test_get_naver_stock_info_market_cap -v
```

**Step 5: Commit**

```bash
git add utils/web_scraper.py tests/test_web_scraper.py
git commit -m "feat: add market_cap parsing to get_naver_stock_info"
```

---

## Task 3: get_market_cap()에 Naver fallback 추가

**Files:**
- Modify: `utils/data_fetcher.py`
- Test: `tests/test_data_fetcher.py`

**Step 1: 실패 테스트 작성**

```python
def test_get_market_cap_with_fallback():
    """get_market_cap이 pykrx 실패 시 Naver fallback 사용"""
    from utils.data_fetcher import get_market_cap
    result = get_market_cap("005930")

    assert result is not None
    assert "시가총액" in result
    assert result["시가총액"] > 0
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
pytest tests/test_data_fetcher.py::test_get_market_cap_with_fallback -v
```

**Step 3: Naver fallback 구현**

```python
def get_market_cap(
    ticker: str,
    date: Optional[str] = None
) -> Optional[dict]:
    """시가총액 정보 조회 (pykrx 우선, 실패 시 Naver fallback)"""
    # 1차: pykrx
    try:
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        df = stock.get_market_cap(date, date, ticker)
        if not df.empty:
            row = df.iloc[-1]
            return {
                "시가총액": int(row["시가총액"]),
                "거래량": int(row["거래량"]),
                "거래대금": int(row["거래대금"]),
                "상장주식수": int(row["상장주식수"]),
                "외국인보유주식수": int(row.get("외국인보유주식수", 0)),
            }
    except Exception:
        pass

    # 2차: Naver fallback
    try:
        from utils.web_scraper import get_naver_stock_info
        info = get_naver_stock_info(ticker)
        if info and info.get("market_cap"):
            return {
                "시가총액": int(info["market_cap"]) * 100000000,  # 억→원
                "거래량": int(info.get("volume", 0) or 0),
                "거래대금": None,  # Naver 미제공
                "상장주식수": None,  # Naver 미제공
                "외국인보유주식수": None,  # Naver 미제공
            }
    except Exception:
        pass
    return None
```

**Step 4: 테스트 실행**

```bash
pytest tests/test_data_fetcher.py::test_get_market_cap_with_fallback -v
```

**Step 5: Commit**

```bash
git add utils/data_fetcher.py tests/test_data_fetcher.py
git commit -m "feat: add Naver fallback to get_market_cap"
```

---

## Task 4: get_ticker_list() Naver fallback 추가

**Files:**
- Modify: `utils/web_scraper.py`
- Modify: `utils/data_fetcher.py`
- Test: `tests/test_data_fetcher.py`

**Step 1: web_scraper.py에 종목 리스트 함수 추가**

```python
def get_naver_stock_list(market: str = "KOSPI") -> Optional[list]:
    """
    네이버 금융에서 종목 리스트 조회

    Args:
        market: "KOSPI" 또는 "KOSDAQ"

    Returns:
        [{"code": "005930", "name": "삼성전자"}, ...]
    """
    market_code = "0" if market == "KOSPI" else "1"
    url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={market_code}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        all_stocks = []
        for page in range(1, 50):
            resp = requests.get(f"{url}&page={page}", headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select("table.type_2 tr")
            page_stocks = []

            for row in rows:
                link = row.select_one("a.tltle")
                if link:
                    href = link.get("href", "")
                    code = href.split("code=")[-1] if "code=" in href else ""
                    if code and len(code) == 6:
                        page_stocks.append({"code": code, "name": link.get_text(strip=True)})

            if not page_stocks:
                break
            all_stocks.extend(page_stocks)

        return all_stocks if all_stocks else None
    except Exception:
        return None
```

**Step 2: data_fetcher.py에 fallback 추가**

```python
def get_ticker_list(
    date: Optional[str] = None,
    market: str = "KOSPI"
) -> Optional[list]:
    """전체 종목 리스트 조회 (pykrx 우선, 실패 시 Naver fallback)"""
    # 1차: pykrx
    try:
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        tickers = stock.get_market_ticker_list(date, market=market)
        if tickers:
            return list(tickers)
    except Exception:
        pass

    # 2차: Naver fallback
    try:
        from utils.web_scraper import get_naver_stock_list
        stocks = get_naver_stock_list(market)
        if stocks:
            return [s["code"] for s in stocks]
    except Exception:
        pass
    return None
```

**Step 3: 테스트**

```python
def test_get_ticker_list_with_fallback():
    from utils.data_fetcher import get_ticker_list
    result = get_ticker_list(market="KOSPI")

    assert result is not None
    assert len(result) > 100
    assert "005930" in result
```

```bash
pytest tests/test_data_fetcher.py::test_get_ticker_list_with_fallback -v
```

**Step 4: Commit**

```bash
git add utils/data_fetcher.py utils/web_scraper.py tests/test_data_fetcher.py
git commit -m "feat: add Naver fallback to get_ticker_list"
```

---

## Task 5: get_fundamental() fallback 검증

**Files:**
- Test: `tests/test_data_fetcher.py`

**현재 상태:** 이미 Naver fallback 구현됨

**Step 1: 테스트 작성**

```python
def test_get_fundamental_returns_data():
    from utils.data_fetcher import get_fundamental
    result = get_fundamental("005930")

    assert result is not None
    assert result["PER"] > 0 or result["PBR"] > 0
```

**Step 2: 테스트 실행**

```bash
pytest tests/test_data_fetcher.py::test_get_fundamental_returns_data -v
```

**Step 3: Commit**

```bash
git add tests/test_data_fetcher.py
git commit -m "test: verify get_fundamental Naver fallback works"
```

---

## Task 6: 문서 업데이트

**Files:**
- Modify: `BUGS_TO_FIX.md`
- Modify: `README.md`

**Step 1: BUGS_TO_FIX.md 업데이트**

Bug #1 수정 방법 섹션 변경:

```markdown
**수정 완료** (2026-01-19):
1. ✅ `get_market_cap()` - Naver fallback 추가
2. ✅ `get_ticker_list()` - Naver fallback 추가
3. ✅ `get_fundamental()` - Naver fallback 검증
4. ⚠️ `get_investor_trading()` - deprecated.py로 이동 (대안 없음)
5. ⚠️ `get_short_selling()` - deprecated.py로 이동 (대안 없음)
```

**Step 2: README.md 업데이트**

```markdown
## ⚠️ 알려진 이슈

### pykrx KRX 데이터 접근 불가 (2025-12-27~)

**상태**: 🟡 부분 해결

| 함수 | 상태 | 비고 |
|------|------|------|
| `get_market_ohlcv_by_date()` | ✅ 작동 | Naver 소스 |
| `get_market_ticker_name()` | ✅ 작동 | Naver 소스 |
| `get_market_ticker_list()` | ✅ 해결 | Naver fallback |
| `get_market_fundamental()` | ✅ 해결 | Naver fallback |
| `get_market_cap()` | ✅ 해결 | Naver fallback |
| `get_investor_trading()` | ❌ 제거 | 대안 없음, deprecated.py |
| `get_short_selling()` | ❌ 제거 | 대안 없음, deprecated.py |

**대안 없는 데이터:**
- 투자자별 매매동향 (기관/외국인/개인)
- 공매도 현황
- 거래대금, 상장주식수, 외국인보유주식수

> 이 데이터가 필요하면 KRX Data Marketplace 유료 API 또는 증권사 API 사용
```

**Step 3: Commit**

```bash
git add BUGS_TO_FIX.md README.md
git commit -m "docs: update pykrx issue status and removed functions"
```

---

## Task 7: 통합 테스트 및 검증

**Step 1: 전체 테스트 실행**

```bash
pytest tests/ -v
```

**Step 2: 수동 검증 스크립트**

```python
import warnings
from utils.data_fetcher import (
    get_ohlcv, get_ticker_name, get_ticker_list,
    get_fundamental, get_market_cap,
)
from utils.deprecated import get_investor_trading, get_short_selling

ticker = "005930"

print("=== pykrx 대안 구현 검증 ===\n")

print("[ 작동하는 함수 ]")
print(f"1. get_ohlcv:        {'✅' if get_ohlcv(ticker) is not None else '❌'}")
print(f"2. get_ticker_name:  {'✅' if get_ticker_name(ticker) else '❌'}")
print(f"3. get_ticker_list:  {'✅' if get_ticker_list() else '❌'}")
print(f"4. get_fundamental:  {'✅' if get_fundamental(ticker) else '❌'}")
print(f"5. get_market_cap:   {'✅' if get_market_cap(ticker) else '❌'}")

print("\n[ Deprecated 함수 (경고 발생 예상) ]")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    result1 = get_investor_trading(ticker)
    result2 = get_short_selling(ticker)
    print(f"6. get_investor_trading: {'⚠️ Deprecated' if len(w) > 0 else '❌'}")
    print(f"7. get_short_selling:    {'⚠️ Deprecated' if len(w) > 1 else '❌'}")

print("\n=== 검증 완료 ===")
```

**Step 3: 최종 Commit**

```bash
git add .
git commit -m "feat: complete pykrx KRX fallback and deprecation"
```

---

## 최종 결과 요약

### 구현 완료
| 함수 | 변경 사항 |
|------|----------|
| `get_ticker_list()` | Naver fallback 추가 |
| `get_fundamental()` | Naver fallback 검증 |
| `get_market_cap()` | Naver fallback 추가 |

### 제거 (deprecated.py로 이동)
| 함수 | 이유 |
|------|------|
| `get_investor_trading()` | KRX 전용 데이터, 대안 없음 |
| `get_short_selling()` | KRX 전용 데이터, 대안 없음 |

### 대안 불가능한 데이터
- 투자자별 매매동향 (기관/외국인/개인 순매수)
- 공매도 현황 (공매도량, 잔고)
- 거래대금
- 상장주식수
- 외국인보유주식수 (비율은 Naver 제공)

---

## 참고 자료

- [pykrx GitHub Issues](https://github.com/sharebook-kr/pykrx/issues)
- [FinanceDataReader](https://financedata.github.io/posts/finance-data-reader-users-guide.html)
- [DART OpenAPI](https://opendart.fss.or.kr/intro/main.do)
- [공공데이터포털](https://www.data.go.kr/data/15094808/openapi.do)
- [KRX Data Marketplace](https://data.krx.co.kr/)
