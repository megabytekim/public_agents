"""재무제표 스크래핑 유틸리티

FnGuide 우선 (div ID 기반 파싱)
모든 숫자에 출처 명시
"""
import re
import time
from typing import Optional
import requests
from bs4 import BeautifulSoup

# FnGuide 테이블 ID
FNGUIDE_URL = "https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp"
FNGUIDE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://comp.fnguide.com/",
}

# 테이블 ID → 재무제표 유형 매핑
FNGUIDE_TABLE_IDS = {
    "divSonikY": "income_annual",      # 연간 손익계산서
    "divSonikQ": "income_quarterly",   # 분기 손익계산서
    "divDaechaY": "balance_annual",    # 연간 재무상태표
    "divCashY": "cash_flow_annual",    # 연간 현금흐름표
}

# 한글 → 영문 메트릭 매핑
INCOME_METRICS = {
    "매출액": "revenue",
    "영업이익": "operating_profit",
    "영업이익(발표기준)": "operating_profit",
    "당기순이익": "net_income",
}

BALANCE_METRICS = {
    "자산": "total_assets",
    "유동자산": "current_assets",
    "부채": "total_liabilities",
    "유동부채": "current_liabilities",
    "자본": "total_equity",
}

CASH_FLOW_METRICS = {
    "영업활동으로인한현금흐름": "operating_cash_flow",
    "투자활동으로인한현금흐름": "investing_cash_flow",
    "재무활동으로인한현금흐름": "financing_cash_flow",
}


def _parse_fnguide_number(text: str) -> Optional[float]:
    """FnGuide 숫자 파싱 (억원 단위)

    Args:
        text: 셀 텍스트 또는 title 속성값

    Returns:
        float (억원) or None
    """
    if not text:
        return None
    text = text.strip()
    if not text or text in ["-", "N/A", "NA", ""]:
        return None

    # 콤마 제거
    clean = re.sub(r'[,\s]', '', text)

    try:
        return float(clean)
    except ValueError:
        return None


def _parse_fnguide_table(soup: BeautifulSoup, div_id: str, metrics: dict) -> Optional[dict]:
    """FnGuide 테이블 파싱 (div ID 기반)

    Args:
        soup: BeautifulSoup 객체
        div_id: 테이블 div ID (예: "divSonikY")
        metrics: 한글→영문 메트릭 매핑

    Returns:
        {
            "2024": {"revenue": 123.4, "operating_profit": 45.6, ...},
            "2023": {...},
            ...
        }
    """
    div_elem = soup.find("div", id=div_id)
    if not div_elem:
        return None

    table = div_elem.find("table")
    if not table:
        return None

    # 헤더에서 기간 추출
    headers = []
    thead = table.find("thead")
    if thead:
        for th in thead.find_all("th"):
            text = th.text.strip()
            if text:
                headers.append(text)

    if len(headers) < 2:
        return None

    # 기간 컬럼 추출 (YYYY/MM 형식 → YYYY 키)
    periods = []
    for h in headers[1:]:
        match = re.match(r"(\d{4})/(\d{2})", h)
        if match:
            year = match.group(1)
            if div_id.endswith("Y"):  # 연간
                periods.append(year)
            else:  # 분기
                month = int(match.group(2))
                quarter = {3: 1, 6: 2, 9: 3, 12: 4}.get(month, month // 3)
                periods.append(f"{year}Q{quarter}")
        elif "전년" not in h and "%" not in h:
            periods.append(None)
        else:
            periods.append(None)

    # 데이터 행 파싱
    result = {p: {} for p in periods if p}
    tbody = table.find("tbody")
    if not tbody:
        return None

    for tr in tbody.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) < 2:
            continue

        # 행 이름 (첫 번째 셀)
        row_name = cells[0].text.strip().replace("\xa0", "").strip()

        # rowBold 클래스 또는 대상 메트릭인 경우만 파싱
        is_bold = "rowBold" in tr.get("class", [])
        if not is_bold and row_name not in metrics:
            continue

        eng_key = metrics.get(row_name)
        if not eng_key:
            continue

        # 값 추출
        for i, cell in enumerate(cells[1:]):
            if i >= len(periods) or not periods[i]:
                continue
            # title 속성 우선 (정밀값), 없으면 텍스트
            value_str = cell.get("title") or cell.text.strip()
            value = _parse_fnguide_number(value_str)
            if value is not None:
                result[periods[i]][eng_key] = value

    # 빈 기간 제거
    return {k: v for k, v in result.items() if v} or None


def get_fnguide_financial(ticker: str, retry: int = 2) -> Optional[dict]:
    """
    FnGuide에서 재무제표 스크래핑

    Args:
        ticker: 종목코드 (예: "005930")
        retry: 실패 시 재시도 횟수 (기본 2)

    Returns:
        {
            "source": "FnGuide",
            "ticker": "005930",
            "name": "삼성전자",
            "period": "2024/12",
            "annual": {
                "2022": {"revenue": ..., "operating_profit": ..., "net_income": ...},
                "2023": {...},
                "2024": {...}
            },
            "latest": {
                "revenue": int,
                "operating_profit": int,
                "net_income": int,
                "total_assets": int,
                "total_liabilities": int,
                "total_equity": int
            },
            "growth": {
                "revenue_yoy": float,  # 전년대비 매출 성장률 (%)
                "operating_profit_yoy": float
            }
        }
        or None (실패 시)
    """
    url = f"https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{ticker}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    for attempt in range(retry + 1):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 종목명 추출 (title에서 파싱)
            title = soup.find("title")
            name = None
            if title:
                # "삼성전자(A005930) | 재무제표..." 형식에서 종목명 추출
                title_text = title.get_text(strip=True)
                match = re.match(r'^([^(]+)\(', title_text)
                if match:
                    name = match.group(1).strip()

            # um_table div들 찾기
            tables = soup.find_all("div", class_="um_table")
            if len(tables) < 3:
                raise ValueError("Required tables not found")

            # Table 1: 연간 손익계산서
            income_table = tables[0]
            annual_data = _parse_income_table(income_table)

            # Table 3 또는 4: 재무상태표 (자산/부채/자본)
            balance_table = None
            for t in tables[2:]:
                headers = t.find_all("th")
                if any("자산" in h.get_text() for h in headers):
                    balance_table = t
                    break

            balance_data = _parse_balance_table(balance_table) if balance_table else {}

            if not annual_data:
                raise ValueError("Failed to parse income data")

            # 최신 연도 데이터
            years = sorted(annual_data.keys(), reverse=True)
            latest_year = years[0] if years else None
            prev_year = years[1] if len(years) > 1 else None

            # 성장률 계산
            growth = {}
            if latest_year and prev_year:
                latest = annual_data[latest_year]
                prev = annual_data[prev_year]

                if prev.get("revenue") and prev["revenue"] != 0:
                    growth["revenue_yoy"] = round(
                        (latest.get("revenue", 0) - prev["revenue"]) / prev["revenue"] * 100, 2
                    )
                if prev.get("operating_profit") and prev["operating_profit"] != 0:
                    growth["operating_profit_yoy"] = round(
                        (latest.get("operating_profit", 0) - prev["operating_profit"]) / prev["operating_profit"] * 100, 2
                    )

            result = {
                "source": "FnGuide",
                "ticker": ticker,
                "name": name,
                "period": f"{latest_year}/12" if latest_year else None,
                "annual": annual_data,
                "latest": {
                    "revenue": annual_data.get(latest_year, {}).get("revenue"),
                    "operating_profit": annual_data.get(latest_year, {}).get("operating_profit"),
                    "net_income": annual_data.get(latest_year, {}).get("net_income"),
                    "total_assets": balance_data.get("total_assets"),
                    "total_liabilities": balance_data.get("total_liabilities"),
                    "total_equity": balance_data.get("total_equity"),
                },
                "growth": growth,
            }

            return result

        except Exception as e:
            if attempt < retry:
                time.sleep(1)  # 재시도 전 대기
                continue
            # 모든 재시도 실패
            return None

    return None


def get_naver_financial(ticker: str) -> Optional[dict]:
    """
    네이버 파이낸스에서 재무제표 스크래핑 (fallback용)

    Args:
        ticker: 종목코드

    Returns:
        {
            "source": "Naver Finance",
            "ticker": "005930",
            "name": "삼성전자",
            ...
        }
        or None (실패 시)
    """
    try:
        # 네이버 기업정보 페이지
        url = f"https://finance.naver.com/item/coinfo.naver?code={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # iframe 내부에 실제 데이터가 있을 수 있음
        # 네이버 파이낸스는 구조가 복잡하므로 기본 정보만 추출

        # 종목명
        name_elem = soup.select_one("div.wrap_company h2 a")
        name = name_elem.get_text(strip=True) if name_elem else None

        # 네이버 파이낸스의 재무제표는 iframe 내부에 있어 직접 접근 어려움
        # 대신 요약 정보에서 추출 시도
        result = {
            "source": "Naver Finance",
            "ticker": ticker,
            "name": name,
            "period": None,
            "annual": {},
            "latest": {},
            "growth": {},
            "note": "Limited data from Naver Finance summary"
        }

        return result if name else None

    except Exception:
        return None


def get_financial_data(ticker: str, retry: int = 2) -> Optional[dict]:
    """
    재무제표 데이터 조회 (FnGuide requests만 사용)

    Args:
        ticker: 종목코드
        retry: FnGuide 재시도 횟수

    Returns:
        재무제표 dict (source 필드에 출처 명시)
        or None (실패 시 - FI 에이전트에서 Playwright/yfinance fallback 처리)

    Note:
        이 함수가 None 반환 시, FI 에이전트는 다음 fallback을 시도해야 함:
        1. Playwright MCP로 FnGuide 크롤링
        2. yfinance MCP 활용 (US stocks)
        모두 실패 시 fail 처리
    """
    # 1순위: FnGuide (requests)
    result = get_fnguide_financial(ticker, retry=retry)
    if result:
        return result

    # 2순위 이상은 에이전트 레벨에서 MCP 도구로 처리
    # (Playwright, yfinance는 Python에서 직접 호출 불가)
    return None


def calculate_peg(per: float, eps_growth: float) -> Optional[float]:
    """
    PEG 계산

    Args:
        per: PER (주가수익비율)
        eps_growth: EPS 성장률 (%)

    Returns:
        PEG = PER / EPS 성장률
        or None (계산 불가 시)
    """
    if per is None or eps_growth is None or eps_growth == 0:
        return None
    return round(per / eps_growth, 2)


def _parse_income_table(table) -> dict:
    """손익계산서 테이블 파싱"""
    result = {}

    try:
        rows = table.find_all("tr")

        # 헤더에서 연도 추출
        header_row = rows[0] if rows else None
        years = []
        if header_row:
            ths = header_row.find_all("th")
            for th in ths:
                text = th.get_text(strip=True)
                # "2024/12" 형식에서 연도 추출
                match = re.search(r'(\d{4})/\d{2}', text)
                if match:
                    years.append(match.group(1))

        # 연도별 데이터 초기화
        for year in years[:3]:  # 최근 3년만
            result[year] = {}

        # 데이터 행 파싱
        for row in rows:
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue

            label = cells[0].get_text(strip=True)
            values = [_parse_number(c.get_text(strip=True)) for c in cells[1:]]

            # 매출액
            if label == "매출액":
                for i, year in enumerate(years[:3]):
                    if i < len(values):
                        result[year]["revenue"] = values[i]

            # 영업이익
            elif label == "영업이익":
                for i, year in enumerate(years[:3]):
                    if i < len(values):
                        result[year]["operating_profit"] = values[i]

            # 당기순이익
            elif "당기순이익" in label and "지배" not in label:
                for i, year in enumerate(years[:3]):
                    if i < len(values):
                        result[year]["net_income"] = values[i]

    except Exception:
        pass

    return result


def _parse_balance_table(table) -> dict:
    """재무상태표 테이블 파싱"""
    result = {}

    try:
        rows = table.find_all("tr")

        for row in rows:
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue

            label = cells[0].get_text(strip=True)
            # 최신 연도 값 (두 번째 컬럼)
            value = _parse_number(cells[1].get_text(strip=True)) if len(cells) > 1 else None

            if label == "자산총계":
                result["total_assets"] = value
            elif label == "부채총계":
                result["total_liabilities"] = value
            elif label == "자본총계":
                result["total_equity"] = value

    except Exception:
        pass

    return result


def _parse_number(text: str) -> Optional[int]:
    """텍스트에서 숫자 추출 (억원 단위)"""
    try:
        # 콤마, 공백 제거
        clean = re.sub(r'[,\s]', '', text)
        # 숫자만 추출 (음수 포함)
        match = re.match(r'^-?\d+', clean)
        if match:
            return int(match.group())
        return None
    except:
        return None


def print_fi_report(ticker: str) -> None:
    """FI 리포트 출력 (FI 에이전트 호출용)

    Args:
        ticker: 종목코드
    """
    data = get_financial_data(ticker)

    if not data:
        print(f"재무제표 데이터 조회 실패: {ticker}")
        return

    print("=" * 60)
    print(f"FI Report: {data.get('name')} ({data.get('ticker')})")
    print(f"데이터 출처: {data.get('source')}")
    print(f"기준 시점: {data.get('period')}")
    print("=" * 60)

    # 연간 추이
    annual = data.get("annual", {})
    if annual:
        print("\n[1. 연간 재무 추이 (억원)]")
        print(f"{'연도':<10} {'매출액':>15} {'영업이익':>15} {'순이익':>15}")
        print("-" * 55)
        for year in sorted(annual.keys()):
            d = annual[year]
            rev = f"{d.get('revenue', 0):,}" if d.get('revenue') else "-"
            op = f"{d.get('operating_profit', 0):,}" if d.get('operating_profit') else "-"
            ni = f"{d.get('net_income', 0):,}" if d.get('net_income') else "-"
            print(f"{year:<10} {rev:>15} {op:>15} {ni:>15}")

    # 성장률
    growth = data.get("growth", {})
    if growth:
        print("\n[2. 성장률 (YoY)]")
        if "revenue_yoy" in growth:
            print(f"매출 성장률: {growth['revenue_yoy']:+.1f}%")
        if "operating_profit_yoy" in growth:
            print(f"영업이익 성장률: {growth['operating_profit_yoy']:+.1f}%")

    # 최신 재무상태
    latest = data.get("latest", {})
    if latest.get("total_assets"):
        print("\n[3. 재무상태 (최신)]")
        if latest.get("total_assets"):
            print(f"자산총계: {latest['total_assets']:,}억원")
        if latest.get("total_liabilities"):
            print(f"부채총계: {latest['total_liabilities']:,}억원")
        if latest.get("total_equity"):
            print(f"자본총계: {latest['total_equity']:,}억원")

    print("\n" + "=" * 60)
    print(f"출처: {data.get('source')}")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "005930"
    print_fi_report(ticker)
