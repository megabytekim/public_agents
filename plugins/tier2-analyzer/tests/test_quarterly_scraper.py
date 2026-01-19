"""FI+ 분기 재무 스크래퍼 테스트"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetFnguideQuarterly:
    """get_fnguide_quarterly() 함수 테스트"""

    def test_returns_quarterly_data_structure(self):
        """분기 데이터 구조 반환 확인"""
        from utils.fi_plus import get_fnguide_quarterly

        # 삼성전자 테스트 (실제 API 호출)
        result = get_fnguide_quarterly("005930")

        assert result is not None
        assert "quarterly" in result
        assert "source" in result
        assert result["source"] == "FnGuide"

    def test_quarterly_has_recent_quarters(self):
        """최근 분기 데이터 포함 확인"""
        from utils.fi_plus import get_fnguide_quarterly

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
        from utils.fi_plus import get_fnguide_quarterly

        result = get_fnguide_quarterly("005930")

        assert result is not None
        quarterly = result.get("quarterly", {})

        # 첫 번째 분기 데이터 확인
        first_quarter = list(quarterly.values())[0] if quarterly else {}

        assert "revenue" in first_quarter or "매출액" in str(first_quarter)

    def test_invalid_ticker_returns_none(self):
        """잘못된 티커는 None 반환"""
        from utils.fi_plus import get_fnguide_quarterly

        result = get_fnguide_quarterly("999999")

        assert result is None


class TestGetFnguideAnnualIncome:
    """get_fnguide_annual_income() 함수 테스트"""

    def test_get_fnguide_annual_income_returns_three_years(self):
        """연간 손익계산서가 최근 3년 데이터를 반환하는지 확인"""
        from utils.fi_plus import get_fnguide_annual_income

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


class TestGetFnguideAnnualBalanceSheet:
    """get_fnguide_annual_balance_sheet() 함수 테스트"""

    def test_get_fnguide_annual_balance_sheet_returns_three_years(self):
        """연간 재무상태표가 최근 3년 데이터를 반환하는지 확인"""
        from utils.fi_plus import get_fnguide_annual_balance_sheet

        result = get_fnguide_annual_balance_sheet("005930")  # 삼성전자

        assert result is not None
        assert "annual" in result

        annual = result["annual"]
        assert len(annual) >= 3

        for year, data in list(annual.items())[:3]:
            assert "total_assets" in data
            assert "total_liabilities" in data
            assert "total_equity" in data
            assert data["total_assets"] is not None

    def test_get_fnguide_annual_balance_sheet_calculates_ratios(self):
        """재무상태표에서 재무비율이 계산되는지 확인"""
        from utils.fi_plus import get_fnguide_annual_balance_sheet

        result = get_fnguide_annual_balance_sheet("005930")

        assert result is not None
        assert "ratios" in result

        ratios = result["ratios"]
        assert "debt_ratio" in ratios  # 부채비율
        assert "current_ratio" in ratios  # 유동비율


class TestGetFnguideAnnualCashFlow:
    """get_fnguide_annual_cash_flow() 함수 테스트"""

    def test_get_fnguide_annual_cash_flow_returns_three_years(self):
        """연간 현금흐름표가 최근 3년 데이터를 반환하는지 확인"""
        from utils.fi_plus import get_fnguide_annual_cash_flow

        result = get_fnguide_annual_cash_flow("005930")  # 삼성전자

        assert result is not None
        assert "annual" in result

        annual = result["annual"]
        assert len(annual) >= 3

        for year, data in list(annual.items())[:3]:
            assert "operating_cash_flow" in data
            assert "investing_cash_flow" in data
            assert "financing_cash_flow" in data

    def test_get_fnguide_annual_cash_flow_calculates_fcf(self):
        """현금흐름표에서 FCF가 계산되는지 확인"""
        from utils.fi_plus import get_fnguide_annual_cash_flow

        result = get_fnguide_annual_cash_flow("005930")

        assert result is not None

        # FCF = 영업CF + 투자CF (투자CF는 보통 음수)
        annual = result["annual"]
        latest_year = max(annual.keys())
        latest = annual[latest_year]

        if latest.get("operating_cash_flow") and latest.get("investing_cash_flow"):
            expected_fcf = latest["operating_cash_flow"] + latest["investing_cash_flow"]
            assert "fcf" in latest
            assert abs(latest["fcf"] - expected_fcf) < 1  # 반올림 오차 허용


class TestGetFnguideFullFinancials:
    """get_fnguide_full_financials() 통합 함수 테스트"""

    def test_get_fnguide_full_financials_returns_all_statements(self):
        """통합 함수가 모든 재무제표를 반환하는지 확인"""
        from utils.fi_plus import get_fnguide_full_financials

        result = get_fnguide_full_financials("005930")

        assert result is not None
        assert "ticker" in result
        assert "name" in result

        # 손익계산서
        assert "income_statement" in result
        assert "annual" in result["income_statement"]
        assert "quarterly" in result["income_statement"]

        # 재무상태표
        assert "balance_sheet" in result
        assert "annual" in result["balance_sheet"]

        # 현금흐름표
        assert "cash_flow" in result
        assert "annual" in result["cash_flow"]

        # 재무비율
        assert "ratios" in result

        # 성장률
        assert "growth" in result

    def test_get_fnguide_full_financials_ratios(self):
        """통합 함수가 재무비율을 올바르게 계산하는지 확인"""
        from utils.fi_plus import get_fnguide_full_financials

        result = get_fnguide_full_financials("005930")

        assert result is not None
        ratios = result["ratios"]

        # 모든 비율 키 존재
        assert "debt_ratio" in ratios
        assert "current_ratio" in ratios
        assert "roe" in ratios
        assert "roa" in ratios

    def test_get_fnguide_full_financials_growth(self):
        """통합 함수가 성장률을 올바르게 계산하는지 확인"""
        from utils.fi_plus import get_fnguide_full_financials

        result = get_fnguide_full_financials("005930")

        assert result is not None
        growth = result["growth"]

        # 성장률 키 존재
        assert "revenue_yoy" in growth
        assert "operating_profit_yoy" in growth

    def test_get_fnguide_full_financials_fcf_calculated(self):
        """통합 함수가 FCF를 계산하는지 확인"""
        from utils.fi_plus import get_fnguide_full_financials

        result = get_fnguide_full_financials("005930")

        assert result is not None
        cash_flow = result["cash_flow"]["annual"]

        # 최신 연도에 FCF 포함
        latest_year = max(cash_flow.keys())
        latest = cash_flow[latest_year]
        assert "fcf" in latest

    def test_get_fnguide_full_financials_invalid_ticker(self):
        """잘못된 티커는 None 반환"""
        from utils.fi_plus import get_fnguide_full_financials

        result = get_fnguide_full_financials("999999")

        assert result is None
