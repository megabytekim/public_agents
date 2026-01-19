"""FnGuide 테이블 공통 파싱 로직

FnGuide 재무제표 테이블을 파싱하기 위한 공통 함수들
"""

import logging
import re
from typing import Optional
from bs4 import BeautifulSoup
from bs4.element import Tag

logger = logging.getLogger(__name__)

# 월 -> 분기 변환 맵 (결산월 기준)
MONTH_TO_QUARTER = {3: 1, 6: 2, 9: 3, 12: 4}

# 테이블 타입별 한글→영문 키 매핑
METRIC_MAPPINGS = {
    "divSonikY": {
        "매출액": "revenue",
        "영업이익": "operating_profit",
        "영업이익(발표기준)": "operating_profit",
        "당기순이익": "net_income",
        "세전계속사업이익": "pretax_income",
    },
    "divSonikQ": {
        "매출액": "revenue",
        "영업이익": "operating_profit",
        "영업이익(발표기준)": "operating_profit",
        "당기순이익": "net_income",
        "세전계속사업이익": "pretax_income",
    },
    "divDaechaY": {
        "자산": "total_assets",
        "유동자산": "current_assets",
        "부채": "total_liabilities",
        "유동부채": "current_liabilities",
        "자본": "total_equity",
    },
    "divDaechaQ": {
        "자산": "total_assets",
        "유동자산": "current_assets",
        "부채": "total_liabilities",
        "유동부채": "current_liabilities",
        "자본": "total_equity",
    },
    "divCashY": {
        "영업활동으로인한현금흐름": "operating_cash_flow",
        "투자활동으로인한현금흐름": "investing_cash_flow",
        "재무활동으로인한현금흐름": "financing_cash_flow",
    },
    "divCashQ": {
        "영업활동으로인한현금흐름": "operating_cash_flow",
        "투자활동으로인한현금흐름": "investing_cash_flow",
        "재무활동으로인한현금흐름": "financing_cash_flow",
    },
}

# 추출 대상 메트릭
INCOME_METRICS_QUARTERLY = ["매출액", "영업이익", "당기순이익", "영업이익(발표기준)"]
INCOME_METRICS_ANNUAL = ["매출액", "영업이익", "영업이익(발표기준)", "당기순이익", "지배주주순이익"]
BALANCE_SHEET_METRICS = ["자산", "유동자산", "부채", "유동부채", "자본"]
CASH_FLOW_METRICS = ["영업활동으로인한현금흐름", "투자활동으로인한현금흐름", "재무활동으로인한현금흐름"]


def extract_company_name(soup: BeautifulSoup) -> Optional[str]:
    """회사명 추출"""
    name_elem = soup.find("h1", class_="giName")
    if name_elem:
        return name_elem.text.strip()

    title = soup.find("title")
    if title:
        title_text = title.text.strip()
        match = re.match(r"([^(]+)\(", title_text)
        if match:
            return match.group(1).strip()
        if " - " in title_text:
            return title_text.split(" - ")[0].strip()
        if "FnGuide" in title_text:
            parts = title_text.replace("FnGuide", "").strip(" -")
            if parts:
                return parts

    return None


def parse_fnguide_table(
    soup: BeautifulSoup, div_id: str, target_metrics: list
) -> Optional[dict]:
    """FnGuide 테이블 공통 파싱 함수"""
    div_elem = soup.find("div", id=div_id)
    if not div_elem:
        return None

    table = div_elem.find("table")
    if not table:
        return None

    headers = _extract_headers(table)
    if len(headers) < 2:
        return None

    data_rows = _extract_data_rows(table, target_metrics)
    if not data_rows:
        return None

    result = {}
    for period_idx, period in enumerate(headers[1:], start=1):
        period_key = _convert_period_to_key(period, div_id)
        if not period_key:
            continue

        period_data = {}
        for row_name, values in data_rows.items():
            if period_idx - 1 < len(values):
                value = values[period_idx - 1]
                eng_key = _get_english_key(row_name, div_id)
                if eng_key:
                    period_data[eng_key] = value

        if period_data:
            result[period_key] = period_data

    return result if result else None


def _extract_headers(table: Optional[Tag]) -> list:
    """테이블 헤더 추출"""
    headers = []
    thead = table.find("thead")
    if thead:
        for th in thead.find_all("th"):
            text = th.text.strip()
            if text:
                headers.append(text)
    return headers


def _extract_first_text(element: Tag) -> str:
    """요소의 첫 번째 직접 텍스트만 추출"""
    for content in element.stripped_strings:
        return content
    return element.text.strip()


def _extract_data_rows(table, target_metrics: list) -> dict:
    """데이터 행 추출"""
    data_rows = {}
    tbody = table.find("tbody")
    if not tbody:
        return data_rows

    for tr in tbody.find_all("tr"):
        row_classes = tr.get("class", [])
        is_bold = "rowBold" in row_classes

        cells = tr.find_all(["th", "td"])
        if len(cells) < 2:
            continue

        row_name = _extract_first_text(cells[0])
        row_name = row_name.replace("\xa0", "").strip()

        if not is_bold and row_name not in target_metrics:
            continue

        values = []
        for cell in cells[1:]:
            value_str = cell.get("title") or cell.text.strip()
            value = parse_numeric_value(value_str)
            values.append(value)

        if row_name and values:
            data_rows[row_name] = values

    return data_rows


def parse_numeric_value(value_str: str) -> Optional[float]:
    """숫자 값 파싱"""
    if not value_str:
        return None

    value_str = value_str.strip()
    if not value_str or value_str in ["-", "N/A", "NA", ""]:
        return None

    multiplier = 1.0
    if "억" in value_str:
        multiplier = 100_000_000
        value_str = value_str.replace("억", "")
    elif "만" in value_str:
        multiplier = 10_000
        value_str = value_str.replace("만", "")

    value_str = value_str.replace("원", "").replace(",", "").replace(" ", "").strip()

    if not value_str:
        return None

    try:
        return float(value_str) * multiplier
    except ValueError:
        return None


def _convert_period_to_key(period: str, div_id: str) -> Optional[str]:
    """기간을 키로 변환"""
    if "전년" in period or "%" in period:
        return None

    match = re.match(r"(\d{4})/(\d{2})", period)
    if not match:
        year_match = re.match(r"(\d{4})$", period.strip())
        if year_match and div_id.endswith("Y"):
            return year_match.group(1)
        return None

    year = match.group(1)
    month = int(match.group(2))

    if div_id.endswith("Y"):
        return year

    quarter = MONTH_TO_QUARTER.get(month)
    if quarter:
        return f"{year}Q{quarter}"

    return None


def _get_english_key(korean_name: str, div_id: str) -> Optional[str]:
    """한글→영문 키 매핑"""
    mapping = METRIC_MAPPINGS.get(div_id, {})
    return mapping.get(korean_name)
