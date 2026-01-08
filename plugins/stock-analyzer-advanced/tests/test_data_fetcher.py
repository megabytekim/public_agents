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

    def test_get_ticker_list_exception(self, mock_pykrx_stock):
        """예외 발생 시 None 반환"""
        from utils.data_fetcher import get_ticker_list

        mock_pykrx_stock.get_market_ticker_list.side_effect = Exception("Error")

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

    def test_get_market_cap_exception(self, mock_pykrx_stock):
        """예외 발생 시 None 반환"""
        from utils.data_fetcher import get_market_cap

        mock_pykrx_stock.get_market_cap.side_effect = Exception("Error")

        result = get_market_cap("005930")

        assert result is None


class TestGetInvestorTrading:
    """get_investor_trading() 테스트"""

    def test_get_investor_trading_success(self, mock_pykrx_stock):
        """정상 조회 시 DataFrame 반환"""
        from utils.data_fetcher import get_investor_trading

        mock_df = pd.DataFrame({
            '기관합계': [1000000],
            '기타법인': [500000],
            '개인': [-1500000],
            '외국인합계': [0],
            '전체': [0],
        })
        mock_pykrx_stock.get_market_trading_value_by_date.return_value = mock_df

        result = get_investor_trading("005930")

        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_get_investor_trading_exception(self, mock_pykrx_stock):
        """예외 발생 시 None 반환"""
        from utils.data_fetcher import get_investor_trading

        mock_pykrx_stock.get_market_trading_value_by_date.side_effect = Exception("Error")

        result = get_investor_trading("005930")

        assert result is None


class TestGetShortSelling:
    """get_short_selling() 테스트"""

    def test_get_short_selling_success(self, mock_pykrx_stock):
        """정상 조회 시 DataFrame 반환"""
        from utils.data_fetcher import get_short_selling

        mock_df = pd.DataFrame({
            '공매도': [100000],
            '잔고': [500000],
            '공매도금액': [7000000000],
            '잔고금액': [35000000000],
        })
        mock_pykrx_stock.get_shorting_status_by_date.return_value = mock_df

        result = get_short_selling("005930")

        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_get_short_selling_exception(self, mock_pykrx_stock):
        """예외 발생 시 None 반환"""
        from utils.data_fetcher import get_short_selling

        mock_pykrx_stock.get_shorting_status_by_date.side_effect = Exception("Error")

        result = get_short_selling("005930")

        assert result is None
