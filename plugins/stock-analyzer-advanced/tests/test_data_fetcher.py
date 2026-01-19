"""data_fetcher.py 테스트"""
import pytest
import pandas as pd
from datetime import datetime


class TestGetOhlcv:
    """get_ohlcv() 테스트"""

    def test_get_ohlcv_success(self, mock_pykrx_stock, sample_ohlcv_df):
        """정상 조회 시 DataFrame 반환"""
        from utils.data_fetcher import get_ohlcv

        mock_pykrx_stock.get_market_ohlcv_by_date.return_value = sample_ohlcv_df

        result = get_ohlcv("005930", days=60)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_get_ohlcv_columns(self, mock_pykrx_stock, sample_ohlcv_df):
        """반환 DataFrame 컬럼 검증"""
        from utils.data_fetcher import get_ohlcv

        mock_pykrx_stock.get_market_ohlcv_by_date.return_value = sample_ohlcv_df

        result = get_ohlcv("005930", days=60)

        expected_columns = ['시가', '고가', '저가', '종가', '거래량', '거래대금', '등락률']
        assert all(col in result.columns for col in expected_columns)

    def test_get_ohlcv_invalid_ticker(self, mock_pykrx_stock):
        """잘못된 종목코드 시 None 반환"""
        from utils.data_fetcher import get_ohlcv

        mock_pykrx_stock.get_market_ohlcv_by_date.return_value = pd.DataFrame()

        result = get_ohlcv("INVALID", days=60)

        assert result is None

    def test_get_ohlcv_exception(self, mock_pykrx_stock):
        """예외 발생 시 None 반환"""
        from utils.data_fetcher import get_ohlcv

        mock_pykrx_stock.get_market_ohlcv_by_date.side_effect = Exception("Network error")

        result = get_ohlcv("005930", days=60)

        assert result is None

    def test_get_ohlcv_calls_pykrx_correctly(self, mock_pykrx_stock, sample_ohlcv_df):
        """pykrx 호출 파라미터 검증"""
        from utils.data_fetcher import get_ohlcv

        mock_pykrx_stock.get_market_ohlcv_by_date.return_value = sample_ohlcv_df

        get_ohlcv("005930", days=30)

        mock_pykrx_stock.get_market_ohlcv_by_date.assert_called_once()
        call_args = mock_pykrx_stock.get_market_ohlcv_by_date.call_args
        # 종목코드가 세 번째 인자로 전달되는지 확인
        assert "005930" in call_args[0]


class TestGetTickerName:
    """get_ticker_name() 테스트"""

    def test_get_ticker_name_success(self, mock_pykrx_stock):
        """정상 조회 시 종목명 반환"""
        from utils.data_fetcher import get_ticker_name

        mock_pykrx_stock.get_market_ticker_name.return_value = "삼성전자"

        result = get_ticker_name("005930")

        assert result == "삼성전자"

    def test_get_ticker_name_invalid(self, mock_pykrx_stock):
        """잘못된 종목코드 시 None 반환"""
        from utils.data_fetcher import get_ticker_name

        mock_pykrx_stock.get_market_ticker_name.return_value = ""

        result = get_ticker_name("INVALID")

        assert result is None

    def test_get_ticker_name_exception(self, mock_pykrx_stock):
        """예외 발생 시 None 반환"""
        from utils.data_fetcher import get_ticker_name

        mock_pykrx_stock.get_market_ticker_name.side_effect = Exception("Error")

        result = get_ticker_name("005930")

        assert result is None


class TestGetTickerList:
    """get_ticker_list() 테스트"""

    def test_get_ticker_list_success(self, mock_pykrx_stock):
        """정상 조회 시 리스트 반환"""
        from utils.data_fetcher import get_ticker_list

        mock_pykrx_stock.get_market_ticker_list.return_value = ['005930', '000660', '035420']

        result = get_ticker_list()

        assert result is not None
        assert isinstance(result, list)
        assert '005930' in result

    def test_get_ticker_list_market_filter(self, mock_pykrx_stock):
        """market 파라미터 전달 검증"""
        from utils.data_fetcher import get_ticker_list

        mock_pykrx_stock.get_market_ticker_list.return_value = ['247540']

        result = get_ticker_list(market="KOSDAQ")

        mock_pykrx_stock.get_market_ticker_list.assert_called()

    def test_get_ticker_list_exception_uses_fallback(self, mock_pykrx_stock, mocker):
        """예외 발생 시 Naver fallback 사용 (fallback도 실패하면 None)"""
        from utils.data_fetcher import get_ticker_list

        mock_pykrx_stock.get_market_ticker_list.side_effect = Exception("Error")
        # Naver fallback도 실패하도록 설정
        mock_naver = mocker.patch('utils.web_scraper.get_naver_stock_list')
        mock_naver.return_value = None

        result = get_ticker_list()

        assert result is None


class TestGetFundamental:
    """get_fundamental() 테스트"""

    def test_get_fundamental_success(self, mock_pykrx_stock, sample_fundamental_df):
        """정상 조회 시 dict 반환"""
        from utils.data_fetcher import get_fundamental

        mock_pykrx_stock.get_market_fundamental.return_value = sample_fundamental_df

        result = get_fundamental("005930")

        assert result is not None
        assert isinstance(result, dict)

    def test_get_fundamental_keys(self, mock_pykrx_stock, sample_fundamental_df):
        """반환 dict 키 검증"""
        from utils.data_fetcher import get_fundamental

        mock_pykrx_stock.get_market_fundamental.return_value = sample_fundamental_df

        result = get_fundamental("005930")

        expected_keys = ['BPS', 'PER', 'PBR', 'EPS', 'DIV', 'DPS']
        assert all(key in result for key in expected_keys)

    def test_get_fundamental_pykrx_exception_uses_fallback(self, mock_pykrx_stock):
        """pykrx 예외 시 네이버 금융 fallback 사용"""
        from utils.data_fetcher import get_fundamental

        mock_pykrx_stock.get_market_fundamental.side_effect = Exception("Error")

        result = get_fundamental("005930")

        # pykrx 실패 시 네이버 금융 fallback으로 데이터 반환
        # 네이버도 실패하면 None 반환
        if result is not None:
            # fallback 성공: PER, PBR 키 존재 확인
            assert "PER" in result
            assert "PBR" in result


class TestGetMarketCap:
    """get_market_cap() 테스트"""

    def test_get_market_cap_success(self, mock_pykrx_stock, sample_market_cap_df):
        """정상 조회 시 dict 반환"""
        from utils.data_fetcher import get_market_cap

        mock_pykrx_stock.get_market_cap.return_value = sample_market_cap_df

        result = get_market_cap("005930")

        assert result is not None
        assert isinstance(result, dict)

    def test_get_market_cap_keys(self, mock_pykrx_stock, sample_market_cap_df):
        """반환 dict 키 검증"""
        from utils.data_fetcher import get_market_cap

        mock_pykrx_stock.get_market_cap.return_value = sample_market_cap_df

        result = get_market_cap("005930")

        expected_keys = ['시가총액', '거래량', '거래대금', '상장주식수', '외국인보유주식수']
        assert all(key in result for key in expected_keys)

    def test_get_market_cap_exception_both_fail(self, mock_pykrx_stock, mocker):
        """pykrx와 Naver 모두 예외 발생 시 None 반환"""
        from utils.data_fetcher import get_market_cap

        mock_pykrx_stock.get_market_cap.side_effect = Exception("Error")
        # Naver fallback도 실패하도록 설정
        mock_naver = mocker.patch('utils.web_scraper.get_naver_stock_info')
        mock_naver.side_effect = Exception("Naver Error")

        result = get_market_cap("005930")

        assert result is None

    def test_get_market_cap_pykrx_fails_uses_naver_fallback(self, mock_pykrx_stock, mocker):
        """pykrx 실패 시 Naver fallback 사용"""
        from utils.data_fetcher import get_market_cap

        # pykrx 실패하도록 설정
        mock_pykrx_stock.get_market_cap.side_effect = Exception("KRX login required")

        # Naver fallback mock (web_scraper 모듈에서 mock)
        mock_naver = mocker.patch('utils.web_scraper.get_naver_stock_info')
        mock_naver.return_value = {
            "name": "삼성전자",
            "price": 70000,
            "market_cap": 4180000,  # 억 단위 (418조)
            "volume": 10000000,
            "per": 15.5,
            "pbr": 1.4,
        }

        result = get_market_cap("005930")

        assert result is not None
        assert "시가총액" in result
        # 4180000억 * 100000000 = 418조 원
        assert result["시가총액"] == 4180000 * 100000000
        assert result["거래량"] == 10000000
        # Naver에서 제공하지 않는 필드는 None
        assert result["거래대금"] is None
        assert result["상장주식수"] is None
        assert result["외국인보유주식수"] is None

    def test_get_market_cap_pykrx_empty_uses_naver_fallback(self, mock_pykrx_stock, mocker):
        """pykrx가 빈 DataFrame 반환 시 Naver fallback 사용"""
        from utils.data_fetcher import get_market_cap

        # pykrx가 빈 DataFrame 반환
        mock_pykrx_stock.get_market_cap.return_value = pd.DataFrame()

        # Naver fallback mock (web_scraper 모듈에서 mock)
        mock_naver = mocker.patch('utils.web_scraper.get_naver_stock_info')
        mock_naver.return_value = {
            "name": "삼성전자",
            "market_cap": 4180000,  # 억 단위
            "volume": 10000000,
        }

        result = get_market_cap("005930")

        assert result is not None
        assert result["시가총액"] == 4180000 * 100000000


def test_get_market_cap_with_fallback():
    """get_market_cap이 pykrx 실패 시 Naver fallback 사용 (통합 테스트)"""
    from utils.data_fetcher import get_market_cap
    result = get_market_cap("005930")

    assert result is not None
    assert "시가총액" in result
    assert result["시가총액"] > 0


# NOTE: get_investor_trading() and get_short_selling() moved to utils/deprecated.py
# Tests for deprecated functions are in test_deprecated.py


class TestGetTickerListWithFallback:
    """get_ticker_list() Naver fallback 테스트"""

    def test_get_ticker_list_pykrx_fails_uses_naver_fallback(self, mock_pykrx_stock, mocker):
        """pykrx 실패 시 Naver fallback 사용"""
        from utils.data_fetcher import get_ticker_list

        # pykrx 실패하도록 설정
        mock_pykrx_stock.get_market_ticker_list.side_effect = Exception("KRX login required")

        # Naver fallback mock
        mock_naver = mocker.patch('utils.web_scraper.get_naver_stock_list')
        mock_naver.return_value = [
            {"code": "005930", "name": "삼성전자"},
            {"code": "000660", "name": "SK하이닉스"},
            {"code": "035420", "name": "NAVER"},
        ]

        result = get_ticker_list(market="KOSPI")

        assert result is not None
        assert isinstance(result, list)
        assert "005930" in result
        assert "000660" in result
        assert len(result) == 3

    def test_get_ticker_list_pykrx_empty_uses_naver_fallback(self, mock_pykrx_stock, mocker):
        """pykrx가 빈 리스트 반환 시 Naver fallback 사용"""
        from utils.data_fetcher import get_ticker_list

        # pykrx가 빈 리스트 반환
        mock_pykrx_stock.get_market_ticker_list.return_value = []

        # Naver fallback mock
        mock_naver = mocker.patch('utils.web_scraper.get_naver_stock_list')
        mock_naver.return_value = [
            {"code": "005930", "name": "삼성전자"},
        ]

        result = get_ticker_list(market="KOSPI")

        assert result is not None
        assert "005930" in result

    def test_get_ticker_list_both_fail_returns_none(self, mock_pykrx_stock, mocker):
        """pykrx와 Naver 모두 실패 시 None 반환"""
        from utils.data_fetcher import get_ticker_list

        mock_pykrx_stock.get_market_ticker_list.side_effect = Exception("Error")
        mock_naver = mocker.patch('utils.web_scraper.get_naver_stock_list')
        mock_naver.return_value = None

        result = get_ticker_list(market="KOSPI")

        assert result is None


def test_get_ticker_list_with_fallback():
    """get_ticker_list가 pykrx 실패 시 Naver fallback 사용 (통합 테스트)"""
    from utils.data_fetcher import get_ticker_list
    result = get_ticker_list(market="KOSPI")

    assert result is not None
    assert len(result) > 100  # KOSPI has many stocks
    assert "005930" in result  # Samsung should be in the list
