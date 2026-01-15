# Stock Analyzer 버그 및 개선사항

> 2026-01-15 분석 중 발견된 이슈

---

## ✅ 완료

### 1. web_scraper.py 시가총액 파싱 버그
- **파일**: `utils/web_scraper.py:109`
- **증상**: 시가총액이 실제 값(1,431억) 대신 순위(623)로 출력
- **원인**:
  ```python
  # Before (버그)
  if "시가총액" in label:  # "시가총액순위"도 매칭됨!
  ```
  - `"시가총액" in "시가총액순위"` = True
  - 루프에서 시가총액(1,431) 먼저 저장 → 시가총액순위(623)가 덮어씀
- **수정**:
  ```python
  # After
  if label == "시가총액":  # 정확 매칭
  ```
- **커밋**: 24df32c

---

## 🔴 TODO: pykrx 시가총액 함수 문제

### 문제 상황
pykrx 라이브러리의 여러 함수가 **모든 날짜에서 Empty 반환**

| 함수 | 상태 | 비고 |
|------|------|------|
| `get_market_ohlcv_by_date()` | ✅ 작동 | 개별 종목 OHLCV 조회 가능 |
| `get_market_cap()` | ❌ Empty | 시가총액 조회 실패 |
| `get_market_ticker_list()` | ❌ 0개 | 종목 리스트 조회 실패 |
| `get_market_fundamental()` | ❌ Empty | PER/PBR 등 조회 실패 |
| `get_market_cap_by_ticker()` | ❌ Error | 컬럼 매핑 에러 |

### 테스트 결과
```python
# 2024~2026 모든 날짜에서 실패
stock.get_market_ticker_list('20260114', market='KOSDAQ')  # → 0개
stock.get_market_ticker_list('20240601', market='KOSPI')   # → 0개
stock.get_market_cap('20260114', '20260114', '049720')     # → Empty DataFrame
```

### 영향
- `data_fetcher.py`의 `get_market_cap()` 함수가 항상 None 반환
- `get_fundamental()` 함수의 pykrx 1차 시도 항상 실패 → Naver fallback 의존

### 해결 방안

#### Option A: Naver Finance Fallback 추가 (권장)
`data_fetcher.py`의 `get_market_cap()` 함수 수정:

```python
def get_market_cap(ticker: str, date: Optional[str] = None) -> Optional[dict]:
    """시가총액 정보 조회 (pykrx 우선, Naver fallback)"""

    # 1차: pykrx 시도
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

    # 2차: Naver Finance fallback
    try:
        from utils.web_scraper import get_naver_stock_info
        info = get_naver_stock_info(ticker)
        if info and info.get("market_cap"):
            # "1,431" 형태를 억원 단위 정수로 변환
            cap_str = info["market_cap"].replace(",", "")
            cap_억 = int(cap_str) if cap_str.isdigit() else 0
            return {
                "시가총액": cap_억 * 100000000,  # 억원 → 원
                "거래량": info.get("volume", 0),
                "거래대금": 0,  # Naver에서 미제공
                "상장주식수": 0,  # Naver에서 미제공
                "외국인보유주식수": 0,
            }
    except Exception:
        pass

    return None
```

#### Option B: pykrx 이슈 리포트
- GitHub: https://github.com/sharebook-kr/pykrx/issues
- 버전: 1.0.51
- KRX API 변경 가능성 조사 필요

---

## 🟡 추가 점검 필요

### web_scraper.py 유사 패턴 점검
동일한 substring 매칭 버그 가능성:

| 현재 코드 | 잠재적 충돌 | 상태 |
|----------|------------|------|
| `"PER" in label` | PER vs 추정PER | ⚠️ 점검 필요 |
| `"PBR" in label` | 단독 사용 | ✅ OK |
| `"외국인" in label` | 외국인한도 vs 외국인보유 vs 외국인소진율 | ⚠️ 점검 필요 |

### 권장 수정
```python
# 안전한 정확 매칭으로 변경
if label == "PER" or label.startswith("PERl"):  # "PERlEPS" 형태
if label == "PBR" or label.startswith("PBRl"):
if "외국인소진율" in label:  # 가장 구체적인 것 먼저
```

---

## 📋 작업 우선순위

1. **[HIGH]** `data_fetcher.py` get_market_cap Naver fallback 추가
2. **[MEDIUM]** web_scraper.py PER/외국인 매칭 패턴 점검
3. **[LOW]** pykrx GitHub 이슈 확인 또는 리포트

---

## 참고: 정상 작동 확인된 함수

```python
# pykrx - 작동함
stock.get_market_ohlcv_by_date(start, end, ticker)  # ✅ OHLCV
stock.get_market_ticker_name(ticker)                 # ✅ 종목명

# Naver scraper - 작동함 (버그 수정 후)
get_naver_stock_info(ticker)  # ✅ 가격, 시총, PER, PBR, 외국인비율
```
