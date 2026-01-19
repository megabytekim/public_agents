"""FI+ 분기 재무 스크래퍼 테스트"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetFnguideQuarterly:
    """get_fnguide_quarterly() 함수 테스트"""

    def test_returns_quarterly_data_structure(self):
        """분기 데이터 구조 반환 확인"""
        from utils.quarterly_scraper import get_fnguide_quarterly

        # 삼성전자 테스트 (실제 API 호출)
        result = get_fnguide_quarterly("005930")

        assert result is not None
        assert "quarterly" in result
        assert "source" in result
        assert result["source"] == "FnGuide"

    def test_quarterly_has_recent_quarters(self):
        """최근 분기 데이터 포함 확인"""
        from utils.quarterly_scraper import get_fnguide_quarterly

        result = get_fnguide_quarterly("005930")

        assert result is not None
        quarterly = result.get("quarterly", {})

        # 최소 4개 분기 데이터 확인
        assert len(quarterly) >= 4

        # 분기 키 형식 확인 (예: "2024Q3", "2024Q2")
        for key in quarterly.keys():
            assert "Q" in key or "/" in key

    def test_quarterly_has_financial_metrics(self):
        """분기별 재무 지표 포함 확인"""
        from utils.quarterly_scraper import get_fnguide_quarterly

        result = get_fnguide_quarterly("005930")

        assert result is not None
        quarterly = result.get("quarterly", {})

        # 첫 번째 분기 데이터 확인
        first_quarter = list(quarterly.values())[0] if quarterly else {}

        assert "revenue" in first_quarter or "매출액" in str(first_quarter)

    def test_invalid_ticker_returns_none(self):
        """잘못된 티커는 None 반환"""
        from utils.quarterly_scraper import get_fnguide_quarterly

        result = get_fnguide_quarterly("999999")

        assert result is None


class TestGetFnguideAnnualIncome:
    """get_fnguide_annual_income() 함수 테스트"""

    def test_get_fnguide_annual_income_returns_three_years(self):
        """연간 손익계산서가 최근 3년 데이터를 반환하는지 확인"""
        from utils.quarterly_scraper import get_fnguide_annual_income

        result = get_fnguide_annual_income("005930")  # 삼성전자

        assert result is not None
        assert "annual" in result

        annual = result["annual"]
        # 최소 3개년 데이터 존재
        assert len(annual) >= 3

        # 각 연도에 필수 항목 존재
        for year, data in list(annual.items())[:3]:
            assert "revenue" in data
            assert "operating_profit" in data
            assert "net_income" in data
            assert data["revenue"] is not None
