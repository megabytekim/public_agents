"""Utils 모듈 통합 테스트

TDD RED 단계: 모든 함수의 동작 여부 검증
"""
import pytest
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, '/Users/newyork/public_agents/plugins/stock-analyzer-advanced')


# ============================================================
# data_fetcher.py 테스트
# ============================================================

class TestDataFetcher:
    """pykrx 래퍼 함수 테스트"""

    def test_get_ohlcv_returns_dataframe(self):
        """get_ohlcv: DataFrame 반환 확인"""
        from utils.data_fetcher import get_ohlcv
        df = get_ohlcv("005930", days=10)  # 삼성전자
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_get_ohlcv_has_required_columns(self):
        """get_ohlcv: 필수 컬럼 확인"""
        from utils.data_fetcher import get_ohlcv
        df = get_ohlcv("005930", days=10)
        required_cols = ['시가', '고가', '저가', '종가', '거래량']
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_get_ohlcv_invalid_ticker(self):
        """get_ohlcv: 잘못된 티커 처리"""
        from utils.data_fetcher import get_ohlcv
        df = get_ohlcv("999999", days=10)
        assert df is None

    def test_get_ticker_name_returns_string(self):
        """get_ticker_name: 문자열 반환 확인"""
        from utils.data_fetcher import get_ticker_name
        name = get_ticker_name("005930")
        assert name is not None
        assert isinstance(name, str)
        assert "삼성전자" in name

    def test_get_ticker_name_invalid(self):
        """get_ticker_name: 잘못된 티커 처리"""
        from utils.data_fetcher import get_ticker_name
        name = get_ticker_name("999999")
        assert name is None or name == ""

    def test_get_ticker_list_returns_list(self):
        """get_ticker_list: 리스트 반환 확인 (pykrx API 불안정 - skip if None)"""
        from utils.data_fetcher import get_ticker_list
        tickers = get_ticker_list(market="KOSPI")
        # pykrx API가 불안정하여 None 반환 가능
        if tickers is None:
            pytest.skip("pykrx get_market_ticker_list API unavailable")
        assert isinstance(tickers, list)
        assert len(tickers) > 100  # KOSPI에 100개 이상 종목

    def test_get_ticker_list_contains_samsung(self):
        """get_ticker_list: 삼성전자 포함 확인 (pykrx API 불안정 - skip if None)"""
        from utils.data_fetcher import get_ticker_list
        tickers = get_ticker_list(market="KOSPI")
        if tickers is None:
            pytest.skip("pykrx get_market_ticker_list API unavailable")
        assert "005930" in tickers

    def test_get_fundamental_returns_dict(self):
        """get_fundamental: dict 반환 확인"""
        from utils.data_fetcher import get_fundamental
        fund = get_fundamental("005930")
        assert fund is not None
        assert isinstance(fund, dict)

    def test_get_fundamental_has_per_pbr(self):
        """get_fundamental: PER, PBR 포함 확인"""
        from utils.data_fetcher import get_fundamental
        fund = get_fundamental("005930")
        if fund:
            assert "PER" in fund
            assert "PBR" in fund

    def test_get_market_cap_returns_dict(self):
        """get_market_cap: dict 반환 확인 (pykrx API 불안정 - skip if None)"""
        from utils.data_fetcher import get_market_cap
        cap = get_market_cap("005930")
        # pykrx API가 불안정하여 None 반환 가능
        if cap is None:
            pytest.skip("pykrx get_market_cap API unavailable")
        assert isinstance(cap, dict)

    def test_get_market_cap_has_value(self):
        """get_market_cap: 시가총액 값 확인 (pykrx API 불안정 - skip if None)"""
        from utils.data_fetcher import get_market_cap
        cap = get_market_cap("005930")
        if cap is None:
            pytest.skip("pykrx get_market_cap API unavailable")
        assert "시가총액" in cap
        assert cap["시가총액"] > 0

    def test_get_investor_trading_returns_dataframe(self):
        """get_investor_trading: DataFrame 반환 확인 (pykrx API 불안정 - skip if None)"""
        from utils.data_fetcher import get_investor_trading
        df = get_investor_trading("005930", days=5)
        # pykrx API가 불안정하여 None 반환 가능
        if df is None:
            pytest.skip("pykrx get_market_trading_value_by_date API unavailable")
        assert isinstance(df, pd.DataFrame)

    def test_get_short_selling_returns_dataframe(self):
        """get_short_selling: DataFrame 반환 확인"""
        from utils.data_fetcher import get_short_selling
        df = get_short_selling("005930", days=5)
        # 공매도 데이터는 없을 수도 있음
        assert df is None or isinstance(df, pd.DataFrame)


# ============================================================
# indicators.py 테스트
# ============================================================

class TestIndicators:
    """기술지표 함수 테스트"""

    @pytest.fixture
    def sample_data(self):
        """테스트용 샘플 데이터"""
        np.random.seed(42)
        n = 100
        close = pd.Series(100 + np.cumsum(np.random.randn(n) * 2))
        high = close + np.abs(np.random.randn(n))
        low = close - np.abs(np.random.randn(n))
        return close, high, low

    def test_sma_length(self, sample_data):
        """sma: 길이 유지 확인"""
        from utils.indicators import sma
        close, _, _ = sample_data
        result = sma(close, 20)
        assert len(result) == len(close)

    def test_sma_values(self, sample_data):
        """sma: 값 범위 확인"""
        from utils.indicators import sma
        close, _, _ = sample_data
        result = sma(close, 20)
        # NaN 제외하고 값 확인
        valid = result.dropna()
        assert valid.min() > 0
        assert valid.max() < close.max() * 2

    def test_ema_length(self, sample_data):
        """ema: 길이 유지 확인"""
        from utils.indicators import ema
        close, _, _ = sample_data
        result = ema(close, 12)
        assert len(result) == len(close)

    def test_rsi_range(self, sample_data):
        """rsi: 0-100 범위 확인"""
        from utils.indicators import rsi
        close, _, _ = sample_data
        result = rsi(close, 14)
        valid = result.dropna()
        assert valid.min() >= 0
        assert valid.max() <= 100

    def test_macd_returns_tuple(self, sample_data):
        """macd: 3개 Series 반환 확인"""
        from utils.indicators import macd
        close, _, _ = sample_data
        macd_line, signal_line, histogram = macd(close)
        assert isinstance(macd_line, pd.Series)
        assert isinstance(signal_line, pd.Series)
        assert isinstance(histogram, pd.Series)

    def test_bollinger_returns_tuple(self, sample_data):
        """bollinger: 3개 Series 반환 확인"""
        from utils.indicators import bollinger
        close, _, _ = sample_data
        upper, middle, lower = bollinger(close)
        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)

    def test_bollinger_order(self, sample_data):
        """bollinger: upper > middle > lower 확인"""
        from utils.indicators import bollinger
        close, _, _ = sample_data
        upper, middle, lower = bollinger(close)
        valid_idx = ~(upper.isna() | middle.isna() | lower.isna())
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_stochastic_returns_tuple(self, sample_data):
        """stochastic: 2개 Series 반환 확인"""
        from utils.indicators import stochastic
        close, high, low = sample_data
        k, d = stochastic(high, low, close)
        assert isinstance(k, pd.Series)
        assert isinstance(d, pd.Series)

    def test_stochastic_range(self, sample_data):
        """stochastic: 0-100 범위 확인"""
        from utils.indicators import stochastic
        close, high, low = sample_data
        k, d = stochastic(high, low, close)
        valid_k = k.dropna()
        valid_d = d.dropna()
        assert valid_k.min() >= 0
        assert valid_k.max() <= 100
        assert valid_d.min() >= 0
        assert valid_d.max() <= 100

    def test_support_resistance_returns_dict(self, sample_data):
        """support_resistance: dict 반환 확인"""
        from utils.indicators import support_resistance
        close, high, low = sample_data
        sr = support_resistance(high, low, close)
        assert isinstance(sr, dict)
        assert "pivot" in sr
        assert "r1" in sr
        assert "r2" in sr
        assert "s1" in sr
        assert "s2" in sr

    def test_support_resistance_order(self, sample_data):
        """support_resistance: r2 > r1 > pivot > s1 > s2 확인"""
        from utils.indicators import support_resistance
        close, high, low = sample_data
        sr = support_resistance(high, low, close)
        assert sr["r2"] >= sr["r1"]
        assert sr["r1"] >= sr["pivot"]
        assert sr["pivot"] >= sr["s1"]
        assert sr["s1"] >= sr["s2"]


# ============================================================
# web_scraper.py 테스트
# ============================================================

class TestWebScraper:
    """웹 스크래핑 함수 테스트"""

    def test_get_naver_stock_info_returns_dict(self):
        """get_naver_stock_info: dict 반환 확인"""
        from utils.web_scraper import get_naver_stock_info
        info = get_naver_stock_info("005930")  # 삼성전자
        assert info is not None
        assert isinstance(info, dict)

    def test_get_naver_stock_info_has_price(self):
        """get_naver_stock_info: 가격 정보 포함 확인"""
        from utils.web_scraper import get_naver_stock_info
        info = get_naver_stock_info("005930")
        if info:
            assert "price" in info
            assert info["price"] > 0

    def test_get_naver_stock_info_has_name(self):
        """get_naver_stock_info: 종목명 포함 확인"""
        from utils.web_scraper import get_naver_stock_info
        info = get_naver_stock_info("005930")
        if info:
            assert "name" in info
            assert "삼성전자" in info["name"]

    def test_get_naver_stock_news_returns_list(self):
        """get_naver_stock_news: 리스트 반환 확인"""
        from utils.web_scraper import get_naver_stock_news
        news = get_naver_stock_news("005930", limit=3)
        assert news is None or isinstance(news, list)

    def test_get_naver_stock_news_has_title(self):
        """get_naver_stock_news: 뉴스 제목 포함 확인"""
        from utils.web_scraper import get_naver_stock_news
        news = get_naver_stock_news("005930", limit=3)
        if news and len(news) > 0:
            assert "title" in news[0]
            assert len(news[0]["title"]) > 0

    def test_get_naver_discussion_returns_list(self):
        """get_naver_discussion: 리스트 반환 확인"""
        from utils.web_scraper import get_naver_discussion
        posts = get_naver_discussion("005930", limit=3)
        assert posts is None or isinstance(posts, list)

    def test_get_naver_discussion_has_title(self):
        """get_naver_discussion: 게시글 제목 포함 확인"""
        from utils.web_scraper import get_naver_discussion
        posts = get_naver_discussion("005930", limit=3)
        if posts and len(posts) > 0:
            assert "title" in posts[0]

    def test_clean_playwright_result_removes_refs(self):
        """clean_playwright_result: [ref=eXXX] 제거 확인"""
        from utils.web_scraper import clean_playwright_result
        text = "Hello [ref=e123] World [ref=e456]"
        result = clean_playwright_result(text)
        assert "[ref=" not in result
        assert "Hello" in result
        assert "World" in result


# ============================================================
# __init__.py export 테스트
# ============================================================

class TestExports:
    """export된 함수 접근 가능 여부 테스트"""

    def test_data_fetcher_exports(self):
        """data_fetcher 함수들 export 확인"""
        from utils import (
            get_ohlcv, get_ticker_name, get_ticker_list,
            get_fundamental, get_market_cap,
            get_investor_trading, get_short_selling
        )
        assert callable(get_ohlcv)
        assert callable(get_ticker_name)
        assert callable(get_ticker_list)
        assert callable(get_fundamental)
        assert callable(get_market_cap)
        assert callable(get_investor_trading)
        assert callable(get_short_selling)

    def test_indicators_exports(self):
        """indicators 함수들 export 확인"""
        from utils import (
            sma, ema, rsi, macd, bollinger, stochastic, support_resistance
        )
        assert callable(sma)
        assert callable(ema)
        assert callable(rsi)
        assert callable(macd)
        assert callable(bollinger)
        assert callable(stochastic)
        assert callable(support_resistance)

    def test_web_scraper_exports(self):
        """web_scraper 함수들 export 확인"""
        from utils import (
            get_naver_stock_info, get_naver_discussion, clean_playwright_result
        )
        assert callable(get_naver_stock_info)
        assert callable(get_naver_discussion)
        assert callable(clean_playwright_result)

    def test_naver_stock_news_export(self):
        """get_naver_stock_news export 확인 (현재 누락됨)"""
        from utils import get_naver_stock_news
        assert callable(get_naver_stock_news)

    def test_ti_analyzer_exports(self):
        """ti_analyzer 함수들 export 확인"""
        from utils import (
            get_ti_full_analysis, print_ti_report,
            get_rsi_signal, get_ma_alignment
        )
        assert callable(get_ti_full_analysis)
        assert callable(print_ti_report)
        assert callable(get_rsi_signal)
        assert callable(get_ma_alignment)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
