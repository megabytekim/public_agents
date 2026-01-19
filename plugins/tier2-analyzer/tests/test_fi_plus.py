"""FI+ 패키지 테스트

utils/fi_plus 패키지의 import 및 기본 기능 테스트
"""

import pytest


class TestFiPlusImports:
    """FI+ 패키지 import 테스트"""

    def test_import_from_utils(self):
        """utils에서 fi_plus 함수 import 테스트"""
        from utils import (
            get_full_financials,
            get_fnguide_quarterly,
            get_peer_comparison,
        )
        assert callable(get_full_financials)
        assert callable(get_fnguide_quarterly)
        assert callable(get_peer_comparison)

    def test_import_fi_plus_directly(self):
        """fi_plus 직접 import 테스트"""
        from utils.fi_plus import get_full_financials
        from utils.fi_plus.fnguide import parser
        from utils.fi_plus.peer_comparison import get_peer_comparison
        assert callable(get_full_financials)
        assert hasattr(parser, "parse_numeric_value")

    def test_import_fnguide_parser(self):
        """fnguide parser 모듈 import 테스트"""
        from utils.fi_plus.fnguide.parser import (
            parse_numeric_value,
            METRIC_MAPPINGS,
            INCOME_METRICS_ANNUAL,
        )
        assert callable(parse_numeric_value)
        assert "divSonikY" in METRIC_MAPPINGS


class TestParserModule:
    """parser 모듈 테스트"""

    def test_parse_numeric_value_basic(self):
        """기본 숫자 파싱 테스트"""
        from utils.fi_plus.fnguide.parser import parse_numeric_value

        assert parse_numeric_value("1234") == 1234.0
        assert parse_numeric_value("1,234") == 1234.0
        assert parse_numeric_value("1234.56") == 1234.56

    def test_parse_numeric_value_korean_units(self):
        """한국어 단위 파싱 테스트"""
        from utils.fi_plus.fnguide.parser import parse_numeric_value

        assert parse_numeric_value("1억") == 100_000_000.0
        assert parse_numeric_value("1.5억") == 150_000_000.0
        assert parse_numeric_value("100만원") == 1_000_000.0

    def test_parse_numeric_value_empty(self):
        """빈 값 파싱 테스트"""
        from utils.fi_plus.fnguide.parser import parse_numeric_value

        assert parse_numeric_value("") is None
        assert parse_numeric_value("-") is None
        assert parse_numeric_value("N/A") is None


class TestMetricMappings:
    """메트릭 매핑 테스트"""

    def test_income_statement_mappings(self):
        """손익계산서 매핑 테스트"""
        from utils.fi_plus.fnguide.parser import METRIC_MAPPINGS

        assert "divSonikY" in METRIC_MAPPINGS
        assert "divSonikQ" in METRIC_MAPPINGS
        assert METRIC_MAPPINGS["divSonikY"]["매출액"] == "revenue"
        assert METRIC_MAPPINGS["divSonikY"]["영업이익"] == "operating_profit"

    def test_balance_sheet_mappings(self):
        """재무상태표 매핑 테스트"""
        from utils.fi_plus.fnguide.parser import METRIC_MAPPINGS

        assert "divDaechaY" in METRIC_MAPPINGS
        assert METRIC_MAPPINGS["divDaechaY"]["자산"] == "total_assets"
        assert METRIC_MAPPINGS["divDaechaY"]["부채"] == "total_liabilities"

    def test_cash_flow_mappings(self):
        """현금흐름표 매핑 테스트"""
        from utils.fi_plus.fnguide.parser import METRIC_MAPPINGS

        assert "divCashY" in METRIC_MAPPINGS
        assert METRIC_MAPPINGS["divCashY"]["영업활동으로인한현금흐름"] == "operating_cash_flow"
