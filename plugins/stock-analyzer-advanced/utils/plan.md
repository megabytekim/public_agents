# Utils 구현 계획 (TDD)

> PRD 기반 단계별 구현 계획

---

## 구현 순서

TDD 사이클: **Red → Green → Refactor**

### Phase 1: P0 (필수) - 기본 인프라

#### Step 1.1: data_fetcher.py - get_ohlcv()

```
[Red]   test_data_fetcher.py::test_get_ohlcv_success
[Red]   test_data_fetcher.py::test_get_ohlcv_invalid_ticker
[Red]   test_data_fetcher.py::test_get_ohlcv_columns
[Green] data_fetcher.py::get_ohlcv 구현
[Refactor] 코드 정리
```

#### Step 1.2: indicators.py - sma(), ema()

```
[Red]   test_indicators.py::test_sma_basic
[Red]   test_indicators.py::test_sma_nan_handling
[Red]   test_indicators.py::test_ema_basic
[Red]   test_indicators.py::test_ema_nan_handling
[Green] indicators.py::sma, ema 구현
[Refactor] 코드 정리
```

#### Step 1.3: indicators.py - rsi()

```
[Red]   test_indicators.py::test_rsi_range
[Red]   test_indicators.py::test_rsi_overbought
[Red]   test_indicators.py::test_rsi_oversold
[Green] indicators.py::rsi 구현
[Refactor] 코드 정리
```

---

### Phase 2: P1 (높음) - 핵심 분석

#### Step 2.1: data_fetcher.py - get_ticker_name(), get_ticker_list()

```
[Red]   test_data_fetcher.py::test_get_ticker_name
[Red]   test_data_fetcher.py::test_get_ticker_list
[Green] data_fetcher.py 구현
[Refactor] 코드 정리
```

#### Step 2.2: data_fetcher.py - get_fundamental()

```
[Red]   test_data_fetcher.py::test_get_fundamental
[Red]   test_data_fetcher.py::test_get_fundamental_keys
[Green] data_fetcher.py::get_fundamental 구현
[Refactor] 코드 정리
```

#### Step 2.3: indicators.py - macd()

```
[Red]   test_indicators.py::test_macd_output_shape
[Red]   test_indicators.py::test_macd_histogram
[Green] indicators.py::macd 구현
[Refactor] 코드 정리
```

#### Step 2.4: indicators.py - bollinger()

```
[Red]   test_indicators.py::test_bollinger_bands_order
[Red]   test_indicators.py::test_bollinger_middle_is_sma
[Green] indicators.py::bollinger 구현
[Refactor] 코드 정리
```

---

### Phase 3: P2 (보통) - 확장 분석

#### Step 3.1: data_fetcher.py - get_market_cap(), get_investor_trading()

```
[Red]   테스트 작성
[Green] 구현
[Refactor] 정리
```

#### Step 3.2: indicators.py - stochastic(), support_resistance()

```
[Red]   테스트 작성
[Green] 구현
[Refactor] 정리
```

---

### Phase 4: P3 (낮음) - 고급 분석

#### Step 4.1: data_fetcher.py - get_short_selling()

```
[Red]   테스트 작성
[Green] 구현
[Refactor] 정리
```

---

## 파일 생성 순서

```
1. tests/conftest.py           # pytest fixtures
2. tests/test_data_fetcher.py  # data_fetcher 테스트
3. tests/test_indicators.py    # indicators 테스트
4. utils/__init__.py           # exports
5. utils/data_fetcher.py       # pykrx 래퍼
6. utils/indicators.py         # 기술지표
```

---

## 테스트 전략

### Unit Tests

- **Mock 사용**: pykrx 호출은 mock으로 대체 (네트워크 의존성 제거)
- **Edge Cases**: 빈 데이터, 잘못된 ticker, None 반환

### Integration Tests (수동)

- 실제 pykrx 호출 테스트 (Jupyter에서 수동 검증)
- 테스트 종목: 005930 (삼성전자), 000660 (SK하이닉스)

---

## 의존성

```bash
pip install pykrx pandas numpy pytest pytest-mock
```

---

## 체크리스트

### Phase 1 (P0)

- [x] get_ohlcv() + 테스트
- [x] sma() + 테스트
- [x] ema() + 테스트
- [x] rsi() + 테스트

### Phase 2 (P1)

- [x] get_ticker_name() + 테스트
- [x] get_ticker_list() + 테스트
- [x] get_fundamental() + 테스트
- [x] macd() + 테스트
- [x] bollinger() + 테스트

### Phase 3 (P2)

- [x] get_market_cap() + 테스트
- [x] get_investor_trading() + 테스트
- [x] stochastic() + 테스트
- [x] support_resistance() + 테스트

### Phase 4 (P3)

- [x] get_short_selling() + 테스트

---

## 예상 소요

- Phase 1: P0 필수 함수 4개
- Phase 2: P1 함수 5개
- Phase 3: P2 함수 4개
- Phase 4: P3 함수 1개

**총 14개 함수**
