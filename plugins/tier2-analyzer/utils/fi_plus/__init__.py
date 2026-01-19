"""FI+ (Financial Intelligence Plus) 패키지

한국 주식 재무 분석을 위한 Tier 2 모듈
"""

from .fnguide import (
    get_full_financials,
    get_annual_income,
    get_quarterly_income,
    get_annual_balance_sheet,
    get_annual_cash_flow,
    format_period_label,
    # 하위 호환성
    get_fnguide_full_financials,
    get_fnguide_annual_income,
    get_fnguide_quarterly,
    get_fnguide_annual_balance_sheet,
    get_fnguide_annual_cash_flow,
)

from .peer_comparison import (
    get_peer_comparison,
    get_sector_average,
)

__all__ = [
    "get_full_financials",
    "get_annual_income",
    "get_quarterly_income",
    "get_annual_balance_sheet",
    "get_annual_cash_flow",
    "format_period_label",
    "get_fnguide_full_financials",
    "get_fnguide_annual_income",
    "get_fnguide_quarterly",
    "get_fnguide_annual_balance_sheet",
    "get_fnguide_annual_cash_flow",
    "get_peer_comparison",
    "get_sector_average",
]
