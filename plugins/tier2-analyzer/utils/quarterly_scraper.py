"""FnGuide 분기 재무 데이터 스크래퍼

FnGuide에서 분기별 재무 데이터를 스크래핑합니다.
"""

import logging
import re

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import Optional


logger = logging.getLogger(__name__)

# 분기 재무 데이터 추출 대상 항목
TARGET_METRICS = ["매출액", "영업이익", "당기순이익", "영업이익(발표기준)"]

# 연간 손익계산서 추출 대상 항목
ANNUAL_INCOME_METRICS = ["매출액", "영업이익", "영업이익(발표기준)", "당기순이익", "지배주주순이익"]

# 재무상태표 추출 대상 항목
BALANCE_SHEET_METRICS = ["자산", "유동자산", "부채", "유동부채", "자본"]

# 현금흐름표 추출 대상 항목
CASH_FLOW_METRICS = [
    "영업활동으로인한현금흐름",
    "투자활동으로인한현금흐름",
    "재무활동으로인한현금흐름",
]

# 월 -> 분기 변환 맵 (결산월 기준)
MONTH_TO_QUARTER = {3: 1, 6: 2, 9: 3, 12: 4}

# 테이블 타입별 한글→영문 키 매핑
METRIC_MAPPINGS = {
    # 손익계산서 (divSonikY, divSonikQ)
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
    # 재무상태표 (divDaechaY, divDaechaQ)
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
    # 현금흐름표 (divCashY, divCashQ)
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


def get_fnguide_quarterly(ticker: str) -> Optional[dict]:
    """FnGuide에서 분기 재무 데이터를 가져옵니다.

    Args:
        ticker: 종목코드 (예: "005930")

    Returns:
        분기 재무 데이터 딕셔너리 또는 None
        {
            "source": "FnGuide",
            "ticker": "005930",
            "name": "삼성전자",
            "quarterly": {
                "2024Q4": {"revenue": ..., "operating_profit": ..., "net_income": ...},
                ...
            },
            "growth": {
                "revenue_qoq": float,
                "revenue_yoy": float,
            }
        }
    """
    url = f"https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{ticker}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://comp.fnguide.com/",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning("FnGuide 요청 실패 (ticker=%s): %s", ticker, e)
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # 회사명 추출
    name = _extract_company_name(soup)
    if not name:
        return None

    # 분기 손익계산서 테이블 파싱 (divSonikQ)
    quarterly_data = _parse_quarterly_income_statement(soup)
    if not quarterly_data:
        return None

    # 성장률 계산
    growth = _calculate_growth(quarterly_data)

    return {
        "source": "FnGuide",
        "ticker": ticker,
        "name": name,
        "quarterly": quarterly_data,
        "growth": growth,
    }


def get_fnguide_annual_income(ticker: str) -> Optional[dict]:
    """FnGuide에서 연간 손익계산서 데이터를 가져옵니다.

    Args:
        ticker: 종목코드 (예: "005930")

    Returns:
        {
            "source": "FnGuide",
            "ticker": "005930",
            "name": "삼성전자",
            "annual": {
                "2024": {"revenue": ..., "operating_profit": ..., "net_income": ...},
                "2023": {...},
                "2022": {...}
            }
        }
    """
    url = f"https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{ticker}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://comp.fnguide.com/",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning("FnGuide 요청 실패 (ticker=%s): %s", ticker, e)
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    name = _extract_company_name(soup)
    if not name:
        return None

    annual_data = _parse_fnguide_table(soup, "divSonikY", ANNUAL_INCOME_METRICS)

    if not annual_data:
        return None

    return {
        "source": "FnGuide",
        "ticker": ticker,
        "name": name,
        "annual": annual_data,
    }


def _extract_company_name(soup: BeautifulSoup) -> Optional[str]:
    """회사명 추출"""
    # h1.giName 또는 span.name 등에서 추출 시도
    name_elem = soup.find("h1", class_="giName")
    if name_elem:
        return name_elem.text.strip()

    # 대체 방법: title에서 추출
    title = soup.find("title")
    if title:
        title_text = title.text.strip()
        # "삼성전자(A005930) | 재무제표 | ..." 형식에서 추출
        match = re.match(r"([^(]+)\(", title_text)
        if match:
            return match.group(1).strip()
        # "삼성전자 - FnGuide" 형식에서 추출
        if " - " in title_text:
            return title_text.split(" - ")[0].strip()
        # "FnGuide - 삼성전자" 형식
        if "FnGuide" in title_text:
            parts = title_text.replace("FnGuide", "").strip(" -")
            if parts:
                return parts

    return None


def _parse_quarterly_income_statement(soup: BeautifulSoup) -> Optional[dict]:
    """분기 손익계산서 파싱 (divSonikQ) - 하위 호환성"""
    return _parse_fnguide_table(soup, "divSonikQ", TARGET_METRICS)


def _parse_fnguide_table(
    soup: BeautifulSoup, div_id: str, target_metrics: list
) -> Optional[dict]:
    """FnGuide 테이블 공통 파싱 함수

    Args:
        soup: BeautifulSoup 객체
        div_id: 테이블 ID (divSonikY, divSonikQ, divDaechaY, divCashY 등)
        target_metrics: 추출할 항목명 리스트

    Returns:
        {기간키: {영문키: 값, ...}, ...} 또는 None
    """
    div_elem = soup.find("div", id=div_id)
    if not div_elem:
        return None

    table = div_elem.find("table")
    if not table:
        return None

    # 헤더에서 기간 정보 추출
    headers = _extract_headers(table)
    if len(headers) < 2:
        return None

    # 데이터 행 추출
    data_rows = _extract_data_rows_generic(table, target_metrics)
    if not data_rows:
        return None

    # 기간별 데이터 구조화
    result = {}

    for period_idx, period in enumerate(headers[1:], start=1):
        # 기간 형식 변환
        period_key = _convert_period_to_key(period, div_id)
        if not period_key:
            continue

        period_data = {}
        for row_name, values in data_rows.items():
            if period_idx - 1 < len(values):
                value = values[period_idx - 1]
                # 영문 키로 변환
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
    """요소의 첫 번째 직접 텍스트만 추출 (중첩 요소 제외)

    Args:
        element: BeautifulSoup 요소

    Returns:
        첫 번째 텍스트 내용 (예: "유동자산계산에 참여한 계정 펼치기" → "유동자산")
    """
    for content in element.stripped_strings:
        return content
    return element.text.strip()


def _extract_data_rows(table) -> dict:
    """데이터 행 추출 - 주요 항목만 (하위 호환성)"""
    return _extract_data_rows_generic(table, TARGET_METRICS)


def _extract_data_rows_generic(table, target_metrics: list) -> dict:
    """데이터 행 추출 (지정된 항목만)

    Args:
        table: BeautifulSoup 테이블 요소
        target_metrics: 추출할 항목명 리스트

    Returns:
        {항목명: [값1, 값2, ...], ...}
    """
    data_rows = {}
    tbody = table.find("tbody")
    if not tbody:
        return data_rows

    for tr in tbody.find_all("tr"):
        # rowBold 클래스 확인 (주요 항목)
        row_classes = tr.get("class", [])
        is_bold = "rowBold" in row_classes

        cells = tr.find_all(["th", "td"])
        if len(cells) < 2:
            continue

        # 항목명 (첫 번째 셀) - 첫 번째 직접 텍스트만 추출
        row_name = _extract_first_text(cells[0])
        row_name = row_name.replace("\xa0", "").strip()

        # 주요 항목만 추출
        if not is_bold:
            # 주요 항목이 아니어도 필요한 항목은 포함
            if row_name not in target_metrics:
                continue

        # 값 추출 (2번째 셀부터)
        values = []
        for cell in cells[1:]:
            # title 속성에서 정확한 값 추출
            value_str = cell.get("title") or cell.text.strip()
            value = _parse_numeric_value(value_str)
            values.append(value)

        if row_name and values:
            data_rows[row_name] = values

    return data_rows


def _parse_numeric_value(value_str: str) -> Optional[float]:
    """숫자 값 파싱

    지원 형식:
        - 일반 숫자: "1234", "1,234", "1234.56"
        - 한국어 단위: "1,234.56억원", "100만원", "1.5억"
    """
    if not value_str:
        return None

    # 공백 제거
    value_str = value_str.strip()

    # 빈 값 또는 N/A 처리
    if not value_str or value_str in ["-", "N/A", "NA", ""]:
        return None

    # 한국어 단위 처리
    multiplier = 1.0
    if "억" in value_str:
        multiplier = 100_000_000  # 1억 = 100,000,000
        value_str = value_str.replace("억", "")
    elif "만" in value_str:
        multiplier = 10_000  # 1만 = 10,000
        value_str = value_str.replace("만", "")

    # "원" 단위 제거
    value_str = value_str.replace("원", "")

    # 쉼표, 공백 제거
    value_str = value_str.replace(",", "").replace(" ", "").strip()

    if not value_str:
        return None

    try:
        return float(value_str) * multiplier
    except ValueError:
        return None


def _convert_period_to_quarter_key(period: str) -> Optional[str]:
    """기간을 분기 키로 변환 (하위 호환성)

    Args:
        period: "2024/12", "2024/09" 등

    Returns:
        "2024Q4", "2024Q3" 등
    """
    return _convert_period_to_key(period, "divSonikQ")


def _convert_period_to_key(period: str, div_id: str) -> Optional[str]:
    """기간을 키로 변환 (연간: "2024", 분기: "2024Q4")

    Args:
        period: "2024/12", "2024/09", "2024" 등
        div_id: 테이블 ID (Y로 끝나면 연간, Q로 끝나면 분기)

    Returns:
        연간 테이블: "2024"
        분기 테이블: "2024Q4"
    """
    # "전년동기", "전년동기(%)" 등 무시
    if "전년" in period or "%" in period:
        return None

    # YYYY/MM 형식 파싱
    match = re.match(r"(\d{4})/(\d{2})", period)
    if not match:
        # 연간: YYYY 형식 처리
        year_match = re.match(r"(\d{4})$", period.strip())
        if year_match and div_id.endswith("Y"):
            return year_match.group(1)
        return None

    year = match.group(1)
    month = int(match.group(2))

    # 연간 테이블 (Y로 끝남)
    if div_id.endswith("Y"):
        return year

    # 분기 테이블 (Q로 끝남)
    quarter = MONTH_TO_QUARTER.get(month)
    if quarter:
        return f"{year}Q{quarter}"

    return None


def _convert_to_english_key(korean_name: str) -> Optional[str]:
    """한글 항목명을 영문 키로 변환 (손익계산서용, 하위 호환성)"""
    return _get_english_key(korean_name, "divSonikQ")


def _get_english_key(korean_name: str, div_id: str) -> Optional[str]:
    """테이블 타입별 한글→영문 키 매핑

    Args:
        korean_name: 한글 항목명
        div_id: 테이블 ID (divSonikY, divSonikQ, divDaechaY, divCashY 등)

    Returns:
        영문 키 또는 None
    """
    mapping = METRIC_MAPPINGS.get(div_id, {})
    return mapping.get(korean_name)


def _calculate_growth(quarterly: dict) -> dict:
    """성장률 계산 (QoQ, YoY)"""
    growth = {
        "revenue_qoq": None,
        "revenue_yoy": None,
    }

    if not quarterly:
        return growth

    # 분기 키 정렬 (최신 순)
    sorted_quarters = sorted(quarterly.keys(), reverse=True)
    if len(sorted_quarters) < 2:
        return growth

    # 최신 분기와 이전 분기
    latest_q = sorted_quarters[0]
    prev_q = sorted_quarters[1]

    latest_revenue = quarterly[latest_q].get("revenue")
    prev_revenue = quarterly[prev_q].get("revenue")

    # QoQ 계산
    if latest_revenue and prev_revenue and prev_revenue != 0:
        growth["revenue_qoq"] = round(
            (latest_revenue - prev_revenue) / abs(prev_revenue) * 100, 2
        )

    # YoY 계산 (4분기 전 데이터 필요)
    if len(sorted_quarters) >= 5:
        yoy_q = sorted_quarters[4]
        yoy_revenue = quarterly[yoy_q].get("revenue")

        if latest_revenue and yoy_revenue and yoy_revenue != 0:
            growth["revenue_yoy"] = round(
                (latest_revenue - yoy_revenue) / abs(yoy_revenue) * 100, 2
            )

    return growth


def get_fnguide_annual_balance_sheet(ticker: str) -> Optional[dict]:
    """FnGuide에서 연간 재무상태표 데이터를 가져옵니다.

    Args:
        ticker: 종목코드 (예: "005930")

    Returns:
        {
            "source": "FnGuide",
            "ticker": "005930",
            "name": "삼성전자",
            "annual": {
                "2024": {
                    "total_assets": ...,
                    "current_assets": ...,
                    "total_liabilities": ...,
                    "current_liabilities": ...,
                    "total_equity": ...
                },
                ...
            },
            "ratios": {
                "debt_ratio": float,     # 부채비율 = 부채/자본 * 100
                "current_ratio": float   # 유동비율 = 유동자산/유동부채 * 100
            }
        }
    """
    url = f"https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{ticker}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://comp.fnguide.com/",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning("FnGuide 요청 실패 (ticker=%s): %s", ticker, e)
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    name = _extract_company_name(soup)
    if not name:
        return None

    annual_data = _parse_fnguide_table(soup, "divDaechaY", BALANCE_SHEET_METRICS)

    if not annual_data:
        return None

    # 최신 연도의 재무비율 계산
    ratios = _calculate_balance_sheet_ratios(annual_data)

    return {
        "source": "FnGuide",
        "ticker": ticker,
        "name": name,
        "annual": annual_data,
        "ratios": ratios,
    }


def _calculate_balance_sheet_ratios(annual_data: dict) -> dict:
    """재무상태표 기반 재무비율 계산

    Args:
        annual_data: 연간 재무상태표 데이터

    Returns:
        {
            "debt_ratio": float,     # 부채비율 = 부채/자본 * 100
            "current_ratio": float   # 유동비율 = 유동자산/유동부채 * 100
        }
    """
    ratios = {"debt_ratio": None, "current_ratio": None}

    if not annual_data:
        return ratios

    latest_year = max(annual_data.keys())
    latest = annual_data[latest_year]

    # 부채비율 = 부채 / 자본 * 100
    total_liabilities = latest.get("total_liabilities")
    total_equity = latest.get("total_equity")
    if total_liabilities and total_equity and total_equity != 0:
        ratios["debt_ratio"] = round(total_liabilities / total_equity * 100, 2)

    # 유동비율 = 유동자산 / 유동부채 * 100
    current_assets = latest.get("current_assets")
    current_liabilities = latest.get("current_liabilities")
    if current_assets and current_liabilities and current_liabilities != 0:
        ratios["current_ratio"] = round(current_assets / current_liabilities * 100, 2)

    return ratios


def get_fnguide_annual_cash_flow(ticker: str) -> Optional[dict]:
    """FnGuide에서 연간 현금흐름표 데이터를 가져옵니다.

    Args:
        ticker: 종목코드 (예: "005930")

    Returns:
        {
            "source": "FnGuide",
            "ticker": "005930",
            "name": "삼성전자",
            "annual": {
                "2024": {
                    "operating_cash_flow": ...,
                    "investing_cash_flow": ...,
                    "financing_cash_flow": ...,
                    "fcf": ...  # 계산됨: operating_cash_flow + investing_cash_flow
                },
                ...
            }
        }
    """
    url = f"https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{ticker}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://comp.fnguide.com/",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning("FnGuide 요청 실패 (ticker=%s): %s", ticker, e)
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    name = _extract_company_name(soup)
    if not name:
        return None

    annual_data = _parse_fnguide_table(soup, "divCashY", CASH_FLOW_METRICS)

    if not annual_data:
        return None

    # FCF 계산: operating_cash_flow + investing_cash_flow
    for year, data in annual_data.items():
        operating_cf = data.get("operating_cash_flow")
        investing_cf = data.get("investing_cash_flow")
        if operating_cf is not None and investing_cf is not None:
            data["fcf"] = operating_cf + investing_cf

    return {
        "source": "FnGuide",
        "ticker": ticker,
        "name": name,
        "annual": annual_data,
    }
