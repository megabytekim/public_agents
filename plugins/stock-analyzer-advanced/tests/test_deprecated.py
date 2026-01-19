"""deprecated.py 테스트"""
import pytest
import warnings


class TestGetInvestorTradingDeprecated:
    """get_investor_trading() deprecated 테스트"""

    def test_returns_none(self):
        """항상 None 반환"""
        from utils.deprecated import get_investor_trading

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = get_investor_trading("005930")

        assert result is None

    def test_emits_deprecation_warning(self):
        """DeprecationWarning 발생"""
        from utils.deprecated import get_investor_trading

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_investor_trading("005930")

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()
            assert "2025-12-27" in str(w[0].message)


class TestGetShortSellingDeprecated:
    """get_short_selling() deprecated 테스트"""

    def test_returns_none(self):
        """항상 None 반환"""
        from utils.deprecated import get_short_selling

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = get_short_selling("005930")

        assert result is None

    def test_emits_deprecation_warning(self):
        """DeprecationWarning 발생"""
        from utils.deprecated import get_short_selling

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_short_selling("005930")

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()
            assert "2025-12-27" in str(w[0].message)
