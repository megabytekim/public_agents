"""FnGuide 재무제표 스크래퍼 패키지

FnGuide에서 한국 주식 재무제표를 스크래핑합니다.
"""

import logging
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .parser import (
    extract_company_name,
    parse_fnguide_table,
    parse_numeric_value,
    INCOME_METRICS_QUARTERLY,
    INCOME_METRICS_ANNUAL,
    BALANCE_SHEET_METRICS,
    CASH_FLOW_METRICS,
    METRIC_MAPPINGS,
)

logger = logging.getLogger(__name__)

FNGUIDE_URL = "https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://comp.fnguide.com/",
}


def _fetch_fnguide_page(ticker: str) -> Optional[BeautifulSoup]:
    """FnGuide 페이지 가져오기"""
    url = f"{FNGUIDE_URL}?pGB=1&gicode=A{ticker}"
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        logger.warning("FnGuide 요청 실패 (ticker=%s): %s", ticker, e)
        return None


def _detect_accumulated_periods(annual_data: Optional[dict], quarterly_data: Optional[dict]) -> dict:
    """누적 기간 감지 (4분기 미완료 연도)

    Returns:
        {
            "2025": "3Q누적",  # 3분기까지만 있는 경우
        }
    """
    labels = {}
    if not annual_data:
        return labels

    # 연간 데이터의 최신 연도 확인
    latest_year = max(annual_data.keys())

    # 분기 데이터에서 해당 연도의 최신 분기 확인
    if quarterly_data:
        year_quarters = [q for q in quarterly_data.keys() if q.startswith(latest_year)]
        if year_quarters:
            latest_quarter = max(year_quarters)  # e.g., "2025Q3"
            quarter_num = latest_quarter[-1]  # "3"
            if quarter_num != "4":  # 4분기가 아니면 누적
                labels[latest_year] = f"{quarter_num}Q누적"

    return labels


def get_full_financials(ticker: str) -> Optional[dict]:
    """전체 재무제표 데이터 (단일 HTTP 요청)"""
    soup = _fetch_fnguide_page(ticker)
    if not soup:
        return None

    name = extract_company_name(soup)
    if not name:
        return None

    income_annual = parse_fnguide_table(soup, "divSonikY", INCOME_METRICS_ANNUAL)
    income_quarterly = parse_fnguide_table(soup, "divSonikQ", INCOME_METRICS_QUARTERLY)
    balance_annual = parse_fnguide_table(soup, "divDaechaY", BALANCE_SHEET_METRICS)
    cash_annual = parse_fnguide_table(soup, "divCashY", CASH_FLOW_METRICS)

    if not income_annual and not balance_annual and not cash_annual:
        return None

    # FCF 계산
    if cash_annual:
        for year, data in cash_annual.items():
            ocf = data.get("operating_cash_flow")
            icf = data.get("investing_cash_flow")
            if ocf is not None and icf is not None:
                data["fcf"] = ocf + icf

    # 당해연도 누적 기간 감지
    period_labels = _detect_accumulated_periods(income_annual, income_quarterly)

    # 재무비율 계산
    ratios = _calculate_ratios(income_annual, balance_annual)
    growth = _calculate_growth(income_annual, period_labels)

    return {
        "source": "FnGuide",
        "ticker": ticker,
        "name": name,
        "income_statement": {"annual": income_annual or {}, "quarterly": income_quarterly or {}},
        "balance_sheet": {"annual": balance_annual or {}},
        "cash_flow": {"annual": cash_annual or {}},
        "ratios": ratios,
        "growth": growth,
        "period_labels": period_labels,  # 누적 기간 라벨
    }


def get_annual_income(ticker: str) -> Optional[dict]:
    """연간 손익계산서"""
    soup = _fetch_fnguide_page(ticker)
    if not soup:
        return None

    name = extract_company_name(soup)
    if not name:
        return None

    annual_data = parse_fnguide_table(soup, "divSonikY", INCOME_METRICS_ANNUAL)
    if not annual_data:
        return None

    return {"source": "FnGuide", "ticker": ticker, "name": name, "annual": annual_data}


def get_quarterly_income(ticker: str) -> Optional[dict]:
    """분기 손익계산서"""
    soup = _fetch_fnguide_page(ticker)
    if not soup:
        return None

    name = extract_company_name(soup)
    if not name:
        return None

    quarterly_data = parse_fnguide_table(soup, "divSonikQ", INCOME_METRICS_QUARTERLY)
    if not quarterly_data:
        return None

    growth = _calculate_quarterly_growth(quarterly_data)
    return {"source": "FnGuide", "ticker": ticker, "name": name, "quarterly": quarterly_data, "growth": growth}


def get_annual_balance_sheet(ticker: str) -> Optional[dict]:
    """연간 재무상태표"""
    soup = _fetch_fnguide_page(ticker)
    if not soup:
        return None

    name = extract_company_name(soup)
    if not name:
        return None

    annual_data = parse_fnguide_table(soup, "divDaechaY", BALANCE_SHEET_METRICS)
    if not annual_data:
        return None

    ratios = _calculate_balance_ratios(annual_data)
    return {"source": "FnGuide", "ticker": ticker, "name": name, "annual": annual_data, "ratios": ratios}


def get_annual_cash_flow(ticker: str) -> Optional[dict]:
    """연간 현금흐름표"""
    soup = _fetch_fnguide_page(ticker)
    if not soup:
        return None

    name = extract_company_name(soup)
    if not name:
        return None

    annual_data = parse_fnguide_table(soup, "divCashY", CASH_FLOW_METRICS)
    if not annual_data:
        return None

    for year, data in annual_data.items():
        ocf = data.get("operating_cash_flow")
        icf = data.get("investing_cash_flow")
        if ocf is not None and icf is not None:
            data["fcf"] = ocf + icf

    return {"source": "FnGuide", "ticker": ticker, "name": name, "annual": annual_data}


def _calculate_ratios(income_data: Optional[dict], balance_data: Optional[dict]) -> dict:
    """전체 재무비율 계산"""
    ratios = {"debt_ratio": None, "current_ratio": None, "roe": None, "roa": None}

    if not balance_data:
        return ratios

    latest_year = max(balance_data.keys())
    balance = balance_data[latest_year]

    tl = balance.get("total_liabilities")
    te = balance.get("total_equity")
    if tl and te and te != 0:
        ratios["debt_ratio"] = round(tl / te * 100, 2)

    ca = balance.get("current_assets")
    cl = balance.get("current_liabilities")
    if ca and cl and cl != 0:
        ratios["current_ratio"] = round(ca / cl * 100, 2)

    if income_data and latest_year in income_data:
        ni = income_data[latest_year].get("net_income")
        ta = balance.get("total_assets")

        if ni is not None and te and te != 0:
            ratios["roe"] = round(ni / te * 100, 2)
        if ni is not None and ta and ta != 0:
            ratios["roa"] = round(ni / ta * 100, 2)

    return ratios


def _calculate_balance_ratios(annual_data: dict) -> dict:
    """재무상태표 비율"""
    ratios = {"debt_ratio": None, "current_ratio": None}
    if not annual_data:
        return ratios

    latest = annual_data[max(annual_data.keys())]

    tl = latest.get("total_liabilities")
    te = latest.get("total_equity")
    if tl and te and te != 0:
        ratios["debt_ratio"] = round(tl / te * 100, 2)

    ca = latest.get("current_assets")
    cl = latest.get("current_liabilities")
    if ca and cl and cl != 0:
        ratios["current_ratio"] = round(ca / cl * 100, 2)

    return ratios


def _calculate_growth(income_data: Optional[dict], period_labels: Optional[dict] = None) -> dict:
    """연간 성장률 (완결 연도 기준)

    누적 데이터가 있는 경우, 완결된 연도끼리 비교합니다.
    예: 2025(3Q누적)이 있으면 2024 vs 2023 비교
    """
    growth = {"revenue_yoy": None, "operating_profit_yoy": None, "comparison": None}
    if not income_data or len(income_data) < 2:
        return growth

    years = sorted(income_data.keys(), reverse=True)

    # 누적 연도가 있으면 제외하고 완결 연도끼리 비교
    if period_labels:
        complete_years = [y for y in years if y not in period_labels]
    else:
        complete_years = years

    if len(complete_years) < 2:
        return growth

    latest_year, prev_year = complete_years[0], complete_years[1]
    latest, prev = income_data[latest_year], income_data[prev_year]

    # 비교 대상 기록
    growth["comparison"] = f"{latest_year} vs {prev_year}"

    lr, pr = latest.get("revenue"), prev.get("revenue")
    if lr is not None and pr is not None and pr != 0:
        growth["revenue_yoy"] = round((lr - pr) / abs(pr) * 100, 2)

    lo, po = latest.get("operating_profit"), prev.get("operating_profit")
    if lo is not None and po is not None and po != 0:
        growth["operating_profit_yoy"] = round((lo - po) / abs(po) * 100, 2)

    return growth


def _calculate_quarterly_growth(quarterly: dict) -> dict:
    """분기 성장률"""
    growth = {"revenue_qoq": None, "revenue_yoy": None}
    if not quarterly:
        return growth

    quarters = sorted(quarterly.keys(), reverse=True)
    if len(quarters) < 2:
        return growth

    latest_rev = quarterly[quarters[0]].get("revenue")
    prev_rev = quarterly[quarters[1]].get("revenue")

    if latest_rev and prev_rev and prev_rev != 0:
        growth["revenue_qoq"] = round((latest_rev - prev_rev) / abs(prev_rev) * 100, 2)

    if len(quarters) >= 5:
        yoy_rev = quarterly[quarters[4]].get("revenue")
        if latest_rev and yoy_rev and yoy_rev != 0:
            growth["revenue_yoy"] = round((latest_rev - yoy_rev) / abs(yoy_rev) * 100, 2)

    return growth


def format_period_label(year: str, period_labels: dict) -> str:
    """연도 키를 표시용 라벨로 변환

    Args:
        year: "2025"
        period_labels: {"2025": "3Q누적"}

    Returns:
        "2025(3Q누적)" or "2025"
    """
    if year in period_labels:
        return f"{year}({period_labels[year]})"
    return year


# 하위 호환성 별칭
get_fnguide_full_financials = get_full_financials
get_fnguide_annual_income = get_annual_income
get_fnguide_quarterly = get_quarterly_income
get_fnguide_annual_balance_sheet = get_annual_balance_sheet
get_fnguide_annual_cash_flow = get_annual_cash_flow

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
]
