"""TI Analyzer 테스트

TDD RED 단계: 테스트 먼저 작성
"""
import pytest
import sys
sys.path.insert(0, '/Users/newyork/public_agents/plugins/stock-analyzer-advanced')


class TestGetTiFullAnalysis:
    """get_ti_full_analysis 함수 테스트"""

    def test_returns_dict(self):
        """dict 반환 확인"""
        from utils.ti_analyzer import get_ti_full_analysis
        result = get_ti_full_analysis("005930")  # 삼성전자
        assert isinstance(result, dict)

    def test_has_meta_section(self):
        """meta 섹션 존재 확인"""
        from utils.ti_analyzer import get_ti_full_analysis
        result = get_ti_full_analysis("005930")
        assert "meta" in result
        assert "ticker" in result["meta"]
        assert "name" in result["meta"]
        assert "timestamp" in result["meta"]

    def test_has_price_info_section(self):
        """price_info 섹션 확인"""
        from utils.ti_analyzer import get_ti_full_analysis
        result = get_ti_full_analysis("005930")
        assert "price_info" in result

        price = result["price_info"]
        # 필수 필드
        assert "price" in price or price is None
        if price:
            assert "change" in price
            assert "change_pct" in price

    def test_has_week52_section(self):
        """52주 고저 섹션 확인"""
        from utils.ti_analyzer import get_ti_full_analysis
        result = get_ti_full_analysis("005930")
        assert "week52" in result

        w52 = result["week52"]
        if w52:
            assert "high" in w52
            assert "low" in w52
            assert "position_pct" in w52

    def test_has_indicators_section(self):
        """기술지표 섹션 확인"""
        from utils.ti_analyzer import get_ti_full_analysis
        result = get_ti_full_analysis("005930")
        assert "indicators" in result

        ind = result["indicators"]
        if ind:
            # 모멘텀 지표
            assert "rsi" in ind
            assert "stochastic" in ind
            # 추세 지표
            assert "macd" in ind
            assert "bollinger" in ind
            # 이동평균
            assert "ma" in ind

    def test_has_support_resistance_section(self):
        """지지/저항선 섹션 확인"""
        from utils.ti_analyzer import get_ti_full_analysis
        result = get_ti_full_analysis("005930")
        assert "support_resistance" in result

        sr = result["support_resistance"]
        if sr:
            assert "s1" in sr
            assert "s2" in sr
            assert "r1" in sr
            assert "r2" in sr

    def test_has_signals_section(self):
        """종합 신호 섹션 확인"""
        from utils.ti_analyzer import get_ti_full_analysis
        result = get_ti_full_analysis("005930")
        assert "signals" in result

        signals = result["signals"]
        if signals:
            assert "rsi_signal" in signals
            assert "macd_signal" in signals
            assert "ma_alignment" in signals

    def test_invalid_ticker_returns_error(self):
        """잘못된 티커 처리"""
        from utils.ti_analyzer import get_ti_full_analysis
        result = get_ti_full_analysis("999999")  # 존재하지 않는 종목
        assert result is not None  # 에러가 아닌 결과 반환
        assert "error" in result or result.get("price_info") is None


class TestRsiSignal:
    """RSI 신호 판단 테스트"""

    def test_overbought_signal(self):
        """과매수 신호 (RSI > 70)"""
        from utils.ti_analyzer import get_rsi_signal
        assert get_rsi_signal(75) == "과매수"
        assert get_rsi_signal(85) == "과매수"

    def test_oversold_signal(self):
        """과매도 신호 (RSI < 30)"""
        from utils.ti_analyzer import get_rsi_signal
        assert get_rsi_signal(25) == "과매도"
        assert get_rsi_signal(10) == "과매도"

    def test_neutral_signal(self):
        """중립 신호 (30 <= RSI <= 70)"""
        from utils.ti_analyzer import get_rsi_signal
        assert get_rsi_signal(50) == "중립"
        assert get_rsi_signal(30) == "중립"
        assert get_rsi_signal(70) == "중립"


class TestMaAlignment:
    """이동평균 배열 판단 테스트"""

    def test_perfect_bullish(self):
        """완전 정배열"""
        from utils.ti_analyzer import get_ma_alignment
        # 현재가 > MA5 > MA20 > MA60
        assert get_ma_alignment(100, 95, 90, 85) == "완전 정배열"

    def test_perfect_bearish(self):
        """완전 역배열"""
        from utils.ti_analyzer import get_ma_alignment
        # 현재가 < MA5 < MA20 < MA60
        assert get_ma_alignment(80, 85, 90, 95) == "완전 역배열"

    def test_mixed(self):
        """혼조"""
        from utils.ti_analyzer import get_ma_alignment
        assert get_ma_alignment(90, 95, 85, 88) == "혼조"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
