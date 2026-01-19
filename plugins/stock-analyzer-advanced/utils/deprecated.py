# utils/deprecated.py
"""
Deprecated functions due to KRX login requirement (2025-12-27~)

These functions no longer work because KRX (Korea Exchange) now requires
authentication for data access. No alternative data source is available.

If you need this data, consider:
1. KRX Data Marketplace paid API
2. Securities company APIs (증권사 API)
3. Bloomberg/Refinitiv terminals
"""
from datetime import datetime, timedelta
from typing import Optional
import warnings

import pandas as pd


def get_investor_trading(
    ticker: str,
    days: int = 20
) -> Optional[pd.DataFrame]:
    """
    [DEPRECATED] 투자자별 순매수 - 2025-12-27부터 작동 안함

    ⚠️ KRX 로그인 필수화로 더 이상 사용 불가
    ⚠️ 대안 데이터 소스 없음

    Args:
        ticker: 종목코드
        days: 조회 일수

    Returns:
        None (항상)
    """
    warnings.warn(
        "get_investor_trading() is deprecated since 2025-12-27. "
        "KRX now requires login. No alternative available.",
        DeprecationWarning,
        stacklevel=2
    )
    return None


def get_short_selling(
    ticker: str,
    days: int = 20
) -> Optional[pd.DataFrame]:
    """
    [DEPRECATED] 공매도 현황 - 2025-12-27부터 작동 안함

    ⚠️ KRX 로그인 필수화로 더 이상 사용 불가
    ⚠️ 대안 데이터 소스 없음

    Args:
        ticker: 종목코드
        days: 조회 일수

    Returns:
        None (항상)
    """
    warnings.warn(
        "get_short_selling() is deprecated since 2025-12-27. "
        "KRX now requires login. No alternative available.",
        DeprecationWarning,
        stacklevel=2
    )
    return None
