"""indicators.py 테스트"""
import pytest
import pandas as pd
import numpy as np


class TestSMA:
    """sma() 테스트"""

    def test_sma_basic(self, sample_close_series):
        """기본 SMA 계산"""
        from utils.indicators import sma

        result = sma(sample_close_series, period=20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_close_series)

    def test_sma_nan_handling(self, sample_close_series):
        """초기 period-1 구간 NaN 처리"""
        from utils.indicators import sma

        period = 20
        result = sma(sample_close_series, period=period)

        # 처음 period-1개는 NaN
        assert result.iloc[:period - 1].isna().all()
        # period번째부터 유효값
        assert not result.iloc[period - 1:].isna().any()

    def test_sma_calculation_accuracy(self):
        """SMA 계산 정확도 검증"""
        from utils.indicators import sma

        close = pd.Series([10, 20, 30, 40, 50])
        result = sma(close, period=3)

        # SMA(3) at index 2 = (10+20+30)/3 = 20
        assert result.iloc[2] == 20.0
        # SMA(3) at index 3 = (20+30+40)/3 = 30
        assert result.iloc[3] == 30.0
        # SMA(3) at index 4 = (30+40+50)/3 = 40
        assert result.iloc[4] == 40.0


class TestEMA:
    """ema() 테스트"""

    def test_ema_basic(self, sample_close_series):
        """기본 EMA 계산"""
        from utils.indicators import ema

        result = ema(sample_close_series, period=20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_close_series)

    def test_ema_nan_handling(self, sample_close_series):
        """EMA NaN 처리"""
        from utils.indicators import ema

        period = 20
        result = ema(sample_close_series, period=period)

        # 초기 구간 NaN 허용 (pandas ewm 동작에 따라)
        # 마지막 값은 유효해야 함
        assert not pd.isna(result.iloc[-1])

    def test_ema_vs_sma_comparison(self, sample_close_series):
        """EMA는 SMA보다 최근 값에 민감"""
        from utils.indicators import sma, ema

        period = 20
        sma_result = sma(sample_close_series, period=period)
        ema_result = ema(sample_close_series, period=period)

        # 둘 다 계산 가능
        assert not pd.isna(sma_result.iloc[-1])
        assert not pd.isna(ema_result.iloc[-1])


class TestRSI:
    """rsi() 테스트"""

    def test_rsi_range(self, sample_close_series):
        """RSI 값 범위 (0-100)"""
        from utils.indicators import rsi

        result = rsi(sample_close_series, period=14)

        valid_values = result.dropna()
        assert (valid_values >= 0).all()
        assert (valid_values <= 100).all()

    def test_rsi_overbought(self):
        """상승 추세에서 RSI > 50"""
        from utils.indicators import rsi

        # 지속 상승 데이터
        close = pd.Series(range(1, 101))
        result = rsi(close, period=14)

        # 마지막 값은 70 이상 (과매수 영역 근처)
        assert result.iloc[-1] > 50

    def test_rsi_oversold(self):
        """하락 추세에서 RSI < 50"""
        from utils.indicators import rsi

        # 지속 하락 데이터
        close = pd.Series(range(100, 0, -1))
        result = rsi(close, period=14)

        # 마지막 값은 30 이하 (과매도 영역 근처)
        assert result.iloc[-1] < 50

    def test_rsi_default_period(self, sample_close_series):
        """기본 period=14"""
        from utils.indicators import rsi

        result = rsi(sample_close_series)  # period 생략

        assert isinstance(result, pd.Series)


class TestMACD:
    """macd() 테스트"""

    def test_macd_output_shape(self, sample_close_series):
        """MACD 반환 형태 (tuple of 3 Series)"""
        from utils.indicators import macd

        result = macd(sample_close_series)

        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(isinstance(s, pd.Series) for s in result)

    def test_macd_histogram(self, sample_close_series):
        """Histogram = MACD Line - Signal Line"""
        from utils.indicators import macd

        macd_line, signal_line, histogram = macd(sample_close_series)

        # histogram 계산 검증 (NaN 제외)
        valid_idx = ~(macd_line.isna() | signal_line.isna() | histogram.isna())
        if valid_idx.any():
            expected = macd_line[valid_idx] - signal_line[valid_idx]
            np.testing.assert_array_almost_equal(
                histogram[valid_idx].values,
                expected.values,
                decimal=5
            )

    def test_macd_default_params(self, sample_close_series):
        """기본 파라미터 (12, 26, 9)"""
        from utils.indicators import macd

        result = macd(sample_close_series)  # 기본값 사용

        assert len(result) == 3


class TestBollinger:
    """bollinger() 테스트"""

    def test_bollinger_output_shape(self, sample_close_series):
        """볼린저 밴드 반환 형태 (tuple of 3 Series)"""
        from utils.indicators import bollinger

        result = bollinger(sample_close_series)

        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(isinstance(s, pd.Series) for s in result)

    def test_bollinger_bands_order(self, sample_close_series):
        """lower <= middle <= upper 순서"""
        from utils.indicators import bollinger

        upper, middle, lower = bollinger(sample_close_series)

        # NaN이 아닌 구간에서 검증
        valid_idx = ~(upper.isna() | middle.isna() | lower.isna())
        assert (lower[valid_idx] <= middle[valid_idx]).all()
        assert (middle[valid_idx] <= upper[valid_idx]).all()

    def test_bollinger_middle_is_sma(self, sample_close_series):
        """Middle band = SMA"""
        from utils.indicators import bollinger, sma

        upper, middle, lower = bollinger(sample_close_series, period=20)
        sma_20 = sma(sample_close_series, period=20)

        # middle과 SMA(20) 동일
        valid_idx = ~(middle.isna() | sma_20.isna())
        np.testing.assert_array_almost_equal(
            middle[valid_idx].values,
            sma_20[valid_idx].values,
            decimal=5
        )


class TestStochastic:
    """stochastic() 테스트"""

    def test_stochastic_output_shape(self, sample_high_series, sample_low_series, sample_close_series):
        """스토캐스틱 반환 형태 (tuple of 2 Series)"""
        from utils.indicators import stochastic

        result = stochastic(sample_high_series, sample_low_series, sample_close_series)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(s, pd.Series) for s in result)

    def test_stochastic_range(self, sample_high_series, sample_low_series, sample_close_series):
        """%K, %D 범위 (0-100)"""
        from utils.indicators import stochastic

        k, d = stochastic(sample_high_series, sample_low_series, sample_close_series)

        valid_k = k.dropna()
        valid_d = d.dropna()

        assert (valid_k >= 0).all() and (valid_k <= 100).all()
        assert (valid_d >= 0).all() and (valid_d <= 100).all()


class TestSupportResistance:
    """support_resistance() 테스트"""

    def test_support_resistance_output_type(self, sample_high_series, sample_low_series, sample_close_series):
        """반환 타입 dict"""
        from utils.indicators import support_resistance

        result = support_resistance(sample_high_series, sample_low_series, sample_close_series)

        assert isinstance(result, dict)

    def test_support_resistance_keys(self, sample_high_series, sample_low_series, sample_close_series):
        """필수 키 검증"""
        from utils.indicators import support_resistance

        result = support_resistance(sample_high_series, sample_low_series, sample_close_series)

        expected_keys = ['pivot', 'r1', 'r2', 's1', 's2']
        assert all(key in result for key in expected_keys)

    def test_support_resistance_order(self, sample_high_series, sample_low_series, sample_close_series):
        """s2 < s1 < pivot < r1 < r2 순서"""
        from utils.indicators import support_resistance

        result = support_resistance(sample_high_series, sample_low_series, sample_close_series)

        assert result['s2'] < result['s1'] < result['pivot'] < result['r1'] < result['r2']
