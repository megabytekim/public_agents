# Utils PRD (Product Requirements Document)

> pykrx 기반 한국 주식 데이터 조회 및 기술지표 유틸리티

---

## 1. 목적

다른 에이전트(PI, MI, TI)가 사용할 **재사용 가능한 인프라 함수** 제공

```
PI/MI/TI 에이전트 → utils 함수 호출 → 분석 수행
```

---

## 2. 데이터 소스: pykrx

> https://github.com/sharebook-kr/pykrx

### 설치

```bash
pip install pykrx
```

### 기본 사용법

```python
from pykrx import stock

# 날짜 포맷: YYYYMMDD (문자열)
# 예: "20250107"
```

### 주요 파라미터

| 파라미터 | 옵션 | 기본값 |
|----------|------|--------|
| `market` | `"KOSPI"`, `"KOSDAQ"`, `"KONEX"`, `"ALL"` | `"KOSPI"` |
| `frequency` | `"d"` (일), `"m"` (월), `"y"` (연) | `"d"` |
| `adjusted` | `True` (수정주가), `False` (원주가) | `True` |

### ⚠️ 데이터 지연 제한

| 데이터 | 지연 |
|--------|------|
| 외국인 투자 | D-2 영업일 기준 |
| 공매도 | T+2일 지연 |

---

## 3. pykrx 함수별 반환 컬럼 (정확한 명세)

### OHLCV: `get_market_ohlcv()`

```python
stock.get_market_ohlcv(start, end, ticker, frequency='d', adjusted=True)
```

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `시가` | int | 시가 |
| `고가` | int | 고가 |
| `저가` | int | 저가 |
| `종가` | int | 종가 |
| `거래량` | int | 거래량 (주) |
| `거래대금` | int | 거래대금 (원) |
| `등락률` | float | 전일대비 등락률 (%) |

### 펀더멘털: `get_market_fundamental()`

```python
stock.get_market_fundamental(date, date, ticker)
```

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `BPS` | int | 주당순자산 |
| `PER` | float | 주가수익비율 |
| `PBR` | float | 주가순자산비율 |
| `EPS` | int | 주당순이익 |
| `DIV` | float | 배당수익률 (%) |
| `DPS` | int | 주당배당금 |

### 시가총액: `get_market_cap()`

```python
stock.get_market_cap(date, date, ticker)
```

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `시가총액` | int | 시가총액 (원) |
| `거래량` | int | 거래량 |
| `거래대금` | int | 거래대금 |
| `상장주식수` | int | 상장주식수 |
| `외국인보유주식수` | int | 외국인 보유 주식수 |

### 투자자별 거래: `get_market_trading_value_by_date()`

```python
stock.get_market_trading_value_by_date(start, end, ticker)
```

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `기관합계` | int | 기관 순매수 |
| `기타법인` | int | 기타법인 순매수 |
| `개인` | int | 개인 순매수 |
| `외국인합계` | int | 외국인 순매수 |
| `전체` | int | 전체 |

### 공매도: `get_shorting_status_by_date()`

```python
stock.get_shorting_status_by_date(start, end, ticker)
```

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `공매도` | int | 공매도량 (주) |
| `잔고` | int | 잔고량 (주) |
| `공매도금액` | int | 공매도금액 (원) |
| `잔고금액` | int | 잔고금액 (원) |

### 종목 리스트: `get_market_ticker_list()`

```python
stock.get_market_ticker_list(date, market="KOSPI")
# Returns: ['005930', '000660', '035420', ...]
```

### 종목명: `get_market_ticker_name()`

```python
stock.get_market_ticker_name("005930")
# Returns: "삼성전자"
```

---

## 4. 파일 구조

```
utils/
├── PRD.md              # 이 문서
├── __init__.py         # exports
├── data_fetcher.py     # pykrx 래퍼 함수
└── indicators.py       # 기술지표 함수
```

---

## 5. 구현 명세

### 5.1 data_fetcher.py

#### 공통 규칙

- **실패 시 `None` 반환** (예외 삼키기)
- **날짜 포맷**: `YYYYMMDD` (pykrx 기본)
- **Type Hints 필수**

#### 함수 목록

| 함수명 | pykrx 매핑 | 우선순위 |
|--------|-----------|----------|
| `get_ohlcv()` | `get_market_ohlcv` | P0 |
| `get_ticker_name()` | `get_market_ticker_name` | P1 |
| `get_ticker_list()` | `get_market_ticker_list` | P1 |
| `get_fundamental()` | `get_market_fundamental` | P1 |
| `get_market_cap()` | `get_market_cap` | P2 |
| `get_investor_trading()` | `get_market_trading_value_by_date` | P2 |
| `get_short_selling()` | `get_shorting_status_by_date` | P3 |

#### 상세 시그니처

```python
def get_ohlcv(
    ticker: str,
    days: int = 60,
    end_date: str | None = None,
    frequency: str = "d",
    adjusted: bool = True
) -> pd.DataFrame | None:
    """
    OHLCV 데이터 조회

    Args:
        ticker: 종목코드 (예: "005930")
        days: 조회 일수 (기본 60)
        end_date: 종료일 YYYYMMDD (기본 오늘)
        frequency: "d"(일), "m"(월), "y"(연)
        adjusted: True=수정주가, False=원주가

    Returns:
        DataFrame or None (실패 시)

    Columns:
        시가, 고가, 저가, 종가, 거래량, 거래대금, 등락률

    Example:
        >>> df = get_ohlcv("005930", days=30)
        >>> df.columns
        Index(['시가', '고가', '저가', '종가', '거래량', '거래대금', '등락률'])
    """


def get_ticker_name(ticker: str) -> str | None:
    """
    종목명 조회

    Example:
        >>> get_ticker_name("005930")
        "삼성전자"
    """


def get_ticker_list(
    date: str | None = None,
    market: str = "KOSPI"
) -> list[str] | None:
    """
    전체 종목 리스트 조회

    Args:
        date: 조회일 YYYYMMDD (기본 오늘)
        market: "KOSPI", "KOSDAQ", "KONEX", "ALL"

    Returns:
        ['005930', '000660', ...]
    """


def get_fundamental(
    ticker: str,
    date: str | None = None
) -> dict | None:
    """
    펀더멘털 지표 조회

    Returns:
        {
            "BPS": int,      # 주당순자산
            "PER": float,    # 주가수익비율
            "PBR": float,    # 주가순자산비율
            "EPS": int,      # 주당순이익
            "DIV": float,    # 배당수익률 (%)
            "DPS": int       # 주당배당금
        }
    """


def get_market_cap(
    ticker: str,
    date: str | None = None
) -> dict | None:
    """
    시가총액 정보 조회

    Returns:
        {
            "시가총액": int,
            "거래량": int,
            "거래대금": int,
            "상장주식수": int,
            "외국인보유주식수": int
        }
    """


def get_investor_trading(
    ticker: str,
    days: int = 20
) -> pd.DataFrame | None:
    """
    투자자별 순매수

    Columns:
        기관합계, 기타법인, 개인, 외국인합계, 전체
    """


def get_short_selling(
    ticker: str,
    days: int = 20
) -> pd.DataFrame | None:
    """
    공매도 현황 (T+2일 지연)

    Columns:
        공매도, 잔고, 공매도금액, 잔고금액
    """
```

---

### 5.2 indicators.py

#### 공통 규칙

- **순수 함수**: 입력만으로 출력 결정
- **pandas Series 기반**: DataFrame 컬럼 직접 전달
- **NaN 처리**: 초기 구간은 NaN 허용

#### 함수 목록

| 함수명 | 입력 | 출력 | 우선순위 |
|--------|------|------|----------|
| `sma()` | close, period | Series | P0 |
| `ema()` | close, period | Series | P0 |
| `rsi()` | close, period=14 | Series | P0 |
| `macd()` | close, fast, slow, signal | Tuple[3] | P1 |
| `bollinger()` | close, period, std | Tuple[3] | P1 |
| `stochastic()` | high, low, close, k, d | Tuple[2] | P2 |
| `support_resistance()` | high, low, close, lookback | dict | P2 |

#### 상세 시그니처

```python
def sma(close: pd.Series, period: int) -> pd.Series:
    """
    단순이동평균 (Simple Moving Average)

    Formula:
        SMA = sum(close[n-period:n]) / period
    """


def ema(close: pd.Series, period: int) -> pd.Series:
    """
    지수이동평균 (Exponential Moving Average)

    Formula:
        EMA = close * k + EMA_prev * (1-k)
        k = 2 / (period + 1)
    """


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    RSI (Relative Strength Index)

    Returns:
        Series (0-100)

    해석:
        > 70: 과매수 (매도 고려)
        < 30: 과매도 (매수 고려)
        50 기준 상승/하락 추세 판단
    """


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD (Moving Average Convergence Divergence)

    Returns:
        (macd_line, signal_line, histogram)

    해석:
        macd > signal (골든크로스): 매수 신호
        macd < signal (데드크로스): 매도 신호
        histogram 방향: 모멘텀 강도
    """


def bollinger(
    close: pd.Series,
    period: int = 20,
    std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    볼린저 밴드

    Returns:
        (upper, middle, lower)

    해석:
        가격 > upper: 과매수, 하락 가능
        가격 < lower: 과매도, 반등 가능
        밴드 수축: 변동성 감소, 돌파 임박
        밴드 확장: 변동성 증가
    """


def stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3
) -> tuple[pd.Series, pd.Series]:
    """
    스토캐스틱 오실레이터

    Returns:
        (%K, %D)

    해석:
        > 80: 과매수
        < 20: 과매도
        %K > %D 상향돌파: 매수
        %K < %D 하향돌파: 매도
    """


def support_resistance(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    lookback: int = 20
) -> dict:
    """
    지지/저항선 (피봇 포인트 기반)

    Returns:
        {
            "pivot": float,  # 피봇 포인트
            "r1": float,     # 저항선 1
            "r2": float,     # 저항선 2
            "s1": float,     # 지지선 1
            "s2": float      # 지지선 2
        }

    Formula:
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
    """
```

---

## 6. 우선순위

### P0 (필수) - 기본 분석

- [ ] `get_ohlcv()` - 모든 분석의 기반
- [ ] `sma()` - 단순이동평균
- [ ] `ema()` - 지수이동평균
- [ ] `rsi()` - 가장 많이 쓰는 지표

### P1 (높음) - 핵심 분석

- [ ] `get_ticker_name()` - 종목명 표시
- [ ] `get_ticker_list()` - 종목 검색
- [ ] `get_fundamental()` - 밸류에이션
- [ ] `macd()` - 트렌드 분석
- [ ] `bollinger()` - 변동성 분석

### P2 (보통) - 확장 분석

- [ ] `get_market_cap()` - 시총 정보
- [ ] `get_investor_trading()` - 수급 분석
- [ ] `stochastic()` - 모멘텀
- [ ] `support_resistance()` - 가격대

### P3 (낮음) - 고급 분석

- [ ] `get_short_selling()` - 공매도 (T+2 지연)

---

## 7. 의존성

```
pykrx>=1.0.0
pandas>=1.5.0
numpy>=1.20.0
```

---

## 8. 테스트 케이스

### 기본 테스트 종목

| 종목코드 | 종목명 | 시장 | 특성 |
|----------|--------|------|------|
| 005930 | 삼성전자 | KOSPI | 거래량 최대, 기준 종목 |
| 000660 | SK하이닉스 | KOSPI | 반도체, 변동성 |
| 035420 | NAVER | KOSPI | 플랫폼, 성장주 |
| 247540 | 에코프로비엠 | KOSDAQ | 2차전지, 고변동성 |

### 검증 항목

```python
# OHLCV
def test_get_ohlcv():
    df = get_ohlcv("005930", days=30)
    assert df is not None
    assert len(df) > 0
    assert all(col in df.columns for col in [
        '시가', '고가', '저가', '종가', '거래량', '거래대금', '등락률'
    ])
    assert df['종가'].dtype in [int, 'int64']

# RSI
def test_rsi():
    rsi_series = rsi(df['종가'])
    assert rsi_series.min() >= 0
    assert rsi_series.max() <= 100

# Bollinger
def test_bollinger():
    upper, middle, lower = bollinger(df['종가'])
    assert (lower <= middle).all()
    assert (middle <= upper).all()

# 실패 케이스
def test_invalid_ticker():
    result = get_ohlcv("INVALID")
    assert result is None
```

---

## 9. 사용 예시

```python
from utils import get_ohlcv, get_ticker_name, rsi, macd, bollinger

# 종목 정보
ticker = "005930"
name = get_ticker_name(ticker)
print(f"종목: {name} ({ticker})")

# 데이터 조회
df = get_ohlcv(ticker, days=60)
if df is None:
    print("조회 실패")
    exit()

print(f"조회 기간: {df.index[0]} ~ {df.index[-1]}")
print(f"데이터 수: {len(df)}일")

# 기술지표 계산
close = df['종가']

rsi_values = rsi(close)
macd_line, signal, hist = macd(close)
upper, mid, lower = bollinger(close)

# 현재 상태 출력
current = close.iloc[-1]
print(f"\n현재가: ₩{current:,.0f}")
print(f"RSI(14): {rsi_values.iloc[-1]:.1f}")
print(f"MACD: {macd_line.iloc[-1]:.0f} (Signal: {signal.iloc[-1]:.0f})")
print(f"볼린저: 하단 ₩{lower.iloc[-1]:,.0f} ~ 상단 ₩{upper.iloc[-1]:,.0f}")
```

---

## 10. 주의사항

### pykrx 제한

1. **KRX 서버 의존**: 거래소 서버 상태에 따라 조회 실패 가능
2. **요청 제한**: 과도한 요청 시 일시 차단 가능
3. **데이터 지연**: 일부 데이터는 실시간이 아님
4. **주말/공휴일**: 시장 휴장일에는 데이터 없음

### 코드 작성 규칙

1. **예외 처리**: 모든 pykrx 호출을 try-except로 감싸기
2. **빈 데이터 체크**: `df.empty` 확인 필수
3. **날짜 유효성**: 미래 날짜, 휴장일 체크
4. **타입 일관성**: int/float 혼용 주의

---

## Changelog

- 2025-01-07: 초안 작성
- 2025-01-07: pykrx 문서 기반 컬럼명 수정, 파라미터 옵션 추가, 데이터 지연 정보 추가
