# Stock Analyzer Advanced - 버그 및 개선사항 목록

> 2026-01-19 업데이트

---

## 🔴 Critical (시스템 장애)

### 1. pykrx KRX 데이터 접근 불가 (2025-12-27~)

**근본 원인**: KRX(한국거래소)가 2025-12-27부터 **로그인 필수**로 정책 변경
- AI 봇 무단 데이터 수집으로 서버 과부하 → 보안 강화 조치
- pykrx의 KRX 기반 함수들 전면 작동 중단

**GitHub 이슈**:
- [#244](https://github.com/sharebook-kr/pykrx/issues/244) - KRX 로그인 필수화 공지
- [#247](https://github.com/sharebook-kr/pykrx/issues/247) - get_market_ticker_list 에러
- [#242](https://github.com/sharebook-kr/pykrx/issues/242) - 결과값 없음
- [#236](https://github.com/sharebook-kr/pykrx/issues/236) - get_market_fundamental 0값 반환

**영향받는 함수** (`utils/data_fetcher.py`, 2026-01-19 테스트):

| 함수 | 상태 | 비고 |
|------|------|------|
| `get_market_ohlcv_by_date()` | ✅ 작동 | Naver 소스 |
| `get_market_ticker_name()` | ✅ 작동 | |
| `get_market_ticker_list()` | ❌ 불가 | KRX 의존 |
| `get_market_fundamental()` | ❌ 불가 | KRX 의존 |
| `get_market_cap()` | ❌ 불가 | KRX 의존 |
| `get_market_trading_value_by_date()` | ❌ 불가 | KRX 의존 |
| `get_shorting_status_by_date()` | ❌ 불가 | KRX 의존 |

**수정 완료** (2026-01-19):
1. ✅ `get_market_cap()` - Naver fallback 추가
2. ✅ `get_ticker_list()` - Naver fallback 추가
3. ✅ `get_fundamental()` - Naver fallback 검증
4. ⚠️ `get_investor_trading()` - deprecated.py로 이동 (대안 없음)
5. ⚠️ `get_short_selling()` - deprecated.py로 이동 (대안 없음)

---

### 2. Portfolio Intelligence 에이전트 미구현

**파일**: `agents/portfolio-intelligence.md` (존재하지 않음)

**영향**:
- `overview.md`와 `REFACTOR_PLAN.md`에서 PI를 오케스트레이터로 설명
- 실제로는 `stock-analyze` 커맨드가 직접 오케스트레이션
- 아키텍처 문서와 실제 구현 불일치

**수정 방법**:
- Option A: PI 에이전트 구현
- Option B: 문서 업데이트 (현재 구조 반영)

---

## 🟠 High (주요 기능 결함)

### 3. web_scraper.py 파싱 버그 가능성

**파일**: `utils/web_scraper.py:111-116`

```python
# 현재 (위험)
elif "PER" in label:      # "PER", "추정PER", "PERl" 모두 매칭
elif "외국인" in label:   # "외국인한도", "외국인보유", "외국인소진율" 모두 매칭
```

**영향**: 잘못된 값이 저장될 수 있음

**수정 방법**:
```python
# 더 안전한 패턴
elif label == "PER" or label.startswith("PER배"):
elif "외국인소진율" in label:  # 가장 구체적인 것 먼저
```

---

### 4. 분기 재무 데이터 미지원

**파일**: `utils/financial_scraper.py:254`

```python
# 현재: 연간 데이터만 파싱
match = re.search(r'(\d{4})/\d{2}', text)  # "2024/12" 형식
```

**영향**: 2025년 분기 실적 (Q1, Q2, Q3) 반영 불가

**수정 방법**: FnGuide 분기 테이블 파싱 로직 추가 (Tier 2 FI+로 이관 예정)

---

### 5. US 주식 지원 미비

**파일**: 전체

| 기능 | 한국 주식 | US 주식 |
|------|----------|---------|
| OHLCV | pykrx ✅ | ❌ 없음 |
| 재무제표 | FnGuide ✅ | yfinance (문서만) |
| 센티먼트 | Naver 종토방 ✅ | Reddit (수동 검색만) |
| 기술지표 | pykrx 기반 ✅ | ❌ 없음 |

**수정 방법**: yfinance MCP 연동 구현 필요

---

## 🟡 Medium (품질 저하)

### 6. 센티먼트 제목만 수집

**파일**: `utils/web_scraper.py:173-220`

```python
# get_naver_discussion() 반환값
{"title": "...", "date": "...", "url": "..."}  # 본문 없음
```

**영향**: 제목만으로는 진정한 센티먼트 파악 어려움

**수정 방법**:
- Option A: 개별 글 본문 fetch (N+1 문제)
- Option B: Playwright로 상세 수집 (70K+ 반환)
- Option C: 제목 키워드 분석 강화 (현재 방식 유지)

---

### 7. 뉴스 요약 없음

**파일**: `utils/web_scraper.py:124-170`

```python
# get_naver_stock_news() 반환값
{"title": "...", "date": "...", "url": "..."}  # 요약/본문 없음
```

**영향**: MI가 각 뉴스 URL을 개별 fetch 해야 함

**수정 방법**: WebFetch로 본문 수집 후 LLM 요약 (MI 에이전트 로직)

---

### 8. 캐싱 없음

**파일**: 전체 utils

**영향**:
- 동일 종목 재분석 시 모든 데이터 재수집
- API 호출 증가, 속도 저하

**수정 방법**:
```python
# 간단한 파일 캐시
import json
from pathlib import Path

CACHE_DIR = Path("./cache")
CACHE_TTL = 3600  # 1시간

def get_cached(key: str) -> Optional[dict]:
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        # TTL 체크 후 반환
        pass
    return None
```

---

### 9. 배치 처리 없음

**파일**: `commands/stock-analyze.md`

**영향**: 다종목 동시 분석 불가

**수정 방법**: `/stock-analyze-batch` 커맨드 추가 (Tier 1 개선)

---

### 10. 에러 복구 미정의

**파일**: `commands/stock-analyze.md`

| Worker | 실패 시 동작 |
|--------|-------------|
| TI | Naver fallback (문서화됨) |
| FI | yfinance fallback (문서화됨) |
| MI | ❓ 정의 안됨 |
| SI | ❓ 정의 안됨 |

**수정 방법**: 각 워커별 fallback 전략 명시

---

### 11. 타임스탬프 동기화 없음

**파일**: `utils/ti_analyzer.py`

```python
# 현재: 각 소스에서 개별 수집
naver_info = get_naver_stock_info(ticker)  # 시점 A
df_year = get_ohlcv(ticker, days=252)       # 시점 B
```

**영향**: Naver 현재가와 pykrx OHLCV 시점 불일치 가능

**수정 방법**: 수집 시점 기록 및 검증 로직 추가

---

## 🟢 Low (개선 사항)

### 12. 테스트 커버리지 부족

| 모듈 | 테스트 상태 |
|------|------------|
| `data_fetcher.py` | ✅ 있음 |
| `indicators.py` | ✅ 있음 |
| `web_scraper.py` | ❌ 없음 |
| `financial_scraper.py` | ❌ 없음 |
| `ti_analyzer.py` | ⚠️ 부분적 |

**수정 방법**: `tests/test_web_scraper.py`, `tests/test_financial_scraper.py` 추가

---

### 13. 출력 경로 불일치

**파일**: `commands/stock-analyze.md` vs 실제 파일

```
문서: stock_checklist/{종목명}_{종목코드}/
실제: watchlist/stocks/{ticker}/
```

**수정 방법**: 문서와 실제 경로 일치시키기

---

### 14. 기술지표 Edge Case 미처리

**파일**: `utils/indicators.py`

| 함수 | Edge Case |
|------|-----------|
| `rsi()` | avg_loss = 0 → division by zero |
| `bollinger()` | std = 0 → division by zero |
| `stochastic()` | high == low → division by zero |

**수정 방법**: 0 체크 추가
```python
if avg_loss == 0:
    return 100.0  # 무한 상승 = RSI 100
```

---

## 📋 우선순위 정리

| 순위 | 항목 | 난이도 | 영향도 |
|------|------|--------|--------|
| P0 | pykrx fallback 추가 | 중간 | 높음 |
| P1 | web_scraper 파싱 개선 | 낮음 | 중간 |
| P1 | US 주식 yfinance 연동 | 높음 | 높음 |
| P2 | 센티먼트 본문 수집 | 중간 | 중간 |
| P2 | 캐싱 추가 | 중간 | 중간 |
| P3 | 테스트 추가 | 중간 | 낮음 |
| P3 | Edge case 처리 | 낮음 | 낮음 |

---

## 참고

- 분석 일시: 2026-01-17
- 분석 범위: agents/, utils/, commands/, tests/
- 관련 문서: `todo.md`, `REFACTOR_PLAN.md`
