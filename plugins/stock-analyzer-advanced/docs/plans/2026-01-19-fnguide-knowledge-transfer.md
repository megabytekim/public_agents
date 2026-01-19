# FnGuide Knowledge Transfer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade stock-analyzer-advanced FI agent with robust FnGuide parsing knowledge from tier2-analyzer.

**Architecture:** Replace unreliable `um_table` class-based parsing with proper div ID-based parsing (`divSonikY`, `divDaechaY`, `divCashY`). Add period detection, proper growth calculation, and expanded financial ratios.

**Tech Stack:** Python, requests, BeautifulSoup4

---

## Background: FnGuide Knowledge Distilled

### Key Discoveries from tier2-analyzer

1. **Table ID Pattern** - FnGuide uses specific div IDs:
   - `divSonikY` - Annual income statement (손익계산서)
   - `divSonikQ` - Quarterly income statement
   - `divDaechaY` - Annual balance sheet (재무상태표)
   - `divCashY` - Annual cash flow (현금흐름표)

2. **Data Extraction** - Use `title` attribute for precision:
   ```html
   <td class="r" title="757,882.69">757,883</td>
   ```
   - `title` has decimal precision (억원)
   - Text content is rounded display value

3. **Row Identification** - `rowBold` class marks main metrics:
   - 매출액, 영업이익, 당기순이익 (income)
   - 자산, 부채, 자본 (balance)
   - 영업활동/투자활동/재무활동으로인한현금흐름 (cash flow)

4. **Period Detection** - Current year may be incomplete:
   - If latest quarter is Q3, the annual "2025" is actually "2025(3Q누적)"
   - YoY growth must compare complete years only (2024 vs 2023, not 2025 vs 2024)

5. **Metric Mappings** - Korean to English key standardization:
   ```python
   "매출액" → "revenue"
   "영업이익" → "operating_profit"
   "당기순이익" → "net_income"
   "자산" → "total_assets"
   "유동자산" → "current_assets"
   "부채" → "total_liabilities"
   "유동부채" → "current_liabilities"
   "자본" → "total_equity"
   ```

---

## Task 1: Add FnGuide Table Constants

**Files:**
- Modify: `/Users/michael/public_agents/plugins/stock-analyzer-advanced/utils/financial_scraper.py:1-15`

**Step 1: Add constants at top of file**

```python
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
```

**Step 2: Run existing tests to ensure no breakage**

Run: `cd /Users/michael/public_agents/plugins/stock-analyzer-advanced && python -m pytest tests/ -v -k financial 2>/dev/null || echo "No financial tests yet"`
Expected: No failures (or no tests)

**Step 3: Commit**

```bash
git add utils/financial_scraper.py
git commit -m "feat(fi): add FnGuide table ID constants and metric mappings"
```

---

## Task 2: Replace Table Parsing with Div ID Approach

**Files:**
- Modify: `/Users/michael/public_agents/plugins/stock-analyzer-advanced/utils/financial_scraper.py:46-136`

**Step 1: Add helper functions**

```python
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
```

**Step 2: Verify syntax**

Run: `python -c "import ast; ast.parse(open('/Users/michael/public_agents/plugins/stock-analyzer-advanced/utils/financial_scraper.py').read())"`
Expected: No output (syntax OK)

**Step 3: Commit**

```bash
git add utils/financial_scraper.py
git commit -m "feat(fi): add div ID-based FnGuide table parser"
```

---

## Task 3: Rewrite get_fnguide_financial with New Parser

**Files:**
- Modify: `/Users/michael/public_agents/plugins/stock-analyzer-advanced/utils/financial_scraper.py`
- Replace: `get_fnguide_financial` function (lines ~13-136)

**Step 1: Replace get_fnguide_financial function**

```python
def get_fnguide_financial(ticker: str, retry: int = 2) -> Optional[dict]:
    """FnGuide에서 재무제표 스크래핑 (div ID 기반)

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
            "latest": {...},
            "growth": {"revenue_yoy": ..., "operating_profit_yoy": ...},
            "ratios": {"debt_ratio": ..., "current_ratio": ..., "roe": ..., "roa": ...},
            "period_labels": {"2025": "3Q누적"}  # 누적 기간 표시
        }
    """
    url = f"{FNGUIDE_URL}?pGB=1&gicode=A{ticker}"

    for attempt in range(retry + 1):
        try:
            response = requests.get(url, headers=FNGUIDE_HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # 종목명 추출
            name = _extract_company_name(soup)

            # 테이블 파싱
            income_annual = _parse_fnguide_table(soup, "divSonikY", INCOME_METRICS)
            balance_annual = _parse_fnguide_table(soup, "divDaechaY", BALANCE_METRICS)
            cash_annual = _parse_fnguide_table(soup, "divCashY", CASH_FLOW_METRICS)

            if not income_annual:
                raise ValueError("Failed to parse income data")

            # FCF 계산
            if cash_annual:
                for year, data in cash_annual.items():
                    ocf = data.get("operating_cash_flow")
                    icf = data.get("investing_cash_flow")
                    if ocf is not None and icf is not None:
                        data["fcf"] = ocf + icf

            # 누적 기간 감지
            period_labels = _detect_accumulated_periods(income_annual, soup)

            # 성장률 계산 (완결 연도 기준)
            growth = _calculate_growth(income_annual, period_labels)

            # 재무비율 계산
            ratios = _calculate_ratios(income_annual, balance_annual)

            # 최신 연도
            years = sorted(income_annual.keys(), reverse=True)
            latest_year = years[0] if years else None

            # latest 구성
            latest = {}
            if latest_year and latest_year in income_annual:
                latest.update(income_annual[latest_year])
            if balance_annual and latest_year in balance_annual:
                latest.update(balance_annual[latest_year])

            return {
                "source": "FnGuide",
                "ticker": ticker,
                "name": name,
                "period": f"{latest_year}/12" if latest_year else None,
                "annual": income_annual,
                "balance": balance_annual or {},
                "cash_flow": cash_annual or {},
                "latest": latest,
                "growth": growth,
                "ratios": ratios,
                "period_labels": period_labels,
            }

        except Exception as e:
            if attempt < retry:
                time.sleep(1)
                continue
            return None

    return None


def _extract_company_name(soup: BeautifulSoup) -> Optional[str]:
    """회사명 추출"""
    # h1.giName 시도
    name_elem = soup.find("h1", class_="giName")
    if name_elem:
        return name_elem.text.strip()

    # title에서 추출
    title = soup.find("title")
    if title:
        title_text = title.text.strip()
        match = re.match(r"([^(]+)\(", title_text)
        if match:
            return match.group(1).strip()
    return None


def _detect_accumulated_periods(annual_data: dict, soup: BeautifulSoup) -> dict:
    """누적 기간 감지 (4분기 미완료 연도)

    Returns:
        {"2025": "3Q누적"} - 해당 연도가 누적인 경우
    """
    labels = {}
    if not annual_data:
        return labels

    latest_year = max(annual_data.keys())

    # 분기 테이블에서 해당 연도 최신 분기 확인
    quarterly = _parse_fnguide_table(soup, "divSonikQ", INCOME_METRICS)
    if quarterly:
        year_quarters = [q for q in quarterly.keys() if q.startswith(latest_year)]
        if year_quarters:
            latest_quarter = max(year_quarters)
            quarter_num = latest_quarter[-1]
            if quarter_num != "4":
                labels[latest_year] = f"{quarter_num}Q누적"

    return labels


def _calculate_growth(income_data: dict, period_labels: Optional[dict] = None) -> dict:
    """연간 성장률 (완결 연도 기준)

    누적 연도는 제외하고 완결된 연도끼리 비교
    예: 2025(3Q누적)이 있으면 2024 vs 2023 비교
    """
    growth = {"revenue_yoy": None, "operating_profit_yoy": None, "comparison": None}
    if not income_data or len(income_data) < 2:
        return growth

    years = sorted(income_data.keys(), reverse=True)

    # 누적 연도 제외
    if period_labels:
        complete_years = [y for y in years if y not in period_labels]
    else:
        complete_years = years

    if len(complete_years) < 2:
        return growth

    latest_year, prev_year = complete_years[0], complete_years[1]
    latest, prev = income_data[latest_year], income_data[prev_year]

    growth["comparison"] = f"{latest_year} vs {prev_year}"

    lr, pr = latest.get("revenue"), prev.get("revenue")
    if lr is not None and pr is not None and pr != 0:
        growth["revenue_yoy"] = round((lr - pr) / abs(pr) * 100, 2)

    lo, po = latest.get("operating_profit"), prev.get("operating_profit")
    if lo is not None and po is not None and po != 0:
        growth["operating_profit_yoy"] = round((lo - po) / abs(po) * 100, 2)

    return growth


def _calculate_ratios(income_data: Optional[dict], balance_data: Optional[dict]) -> dict:
    """재무비율 계산"""
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
```

**Step 2: Remove old parsing functions**

Delete `_parse_income_table` and `_parse_balance_table` functions (now replaced by `_parse_fnguide_table`).

**Step 3: Verify syntax**

Run: `python -c "import ast; ast.parse(open('/Users/michael/public_agents/plugins/stock-analyzer-advanced/utils/financial_scraper.py').read())"`
Expected: No output (syntax OK)

**Step 4: Test with real ticker**

Run: `cd /Users/michael/public_agents/plugins/stock-analyzer-advanced && python -c "from utils import get_fnguide_financial; import json; print(json.dumps(get_fnguide_financial('005930'), indent=2, ensure_ascii=False, default=str))"`
Expected: Valid JSON with Samsung Electronics financial data

**Step 5: Commit**

```bash
git add utils/financial_scraper.py
git commit -m "refactor(fi): rewrite FnGuide parser with div ID approach"
```

---

## Task 4: Update print_fi_report for New Data Structure

**Files:**
- Modify: `/Users/michael/public_agents/plugins/stock-analyzer-advanced/utils/financial_scraper.py`
- Function: `print_fi_report` (lines ~338-391)

**Step 1: Update print_fi_report**

```python
def print_fi_report(ticker: str) -> None:
    """FI 리포트 출력 (FI 에이전트 호출용)

    Args:
        ticker: 종목코드
    """
    data = get_financial_data(ticker)

    if not data:
        print(f"재무제표 데이터 조회 실패: {ticker}")
        return

    period_labels = data.get("period_labels", {})

    print("=" * 60)
    print(f"FI Report: {data.get('name')} ({data.get('ticker')})")
    print(f"데이터 출처: {data.get('source')}")
    print(f"기준 시점: {data.get('period')}")
    print("=" * 60)

    # 연간 손익 추이
    annual = data.get("annual", {})
    if annual:
        print("\n[1. 연간 재무 추이 (억원)]")
        print(f"{'연도':<15} {'매출액':>15} {'영업이익':>15} {'순이익':>15}")
        print("-" * 60)
        for year in sorted(annual.keys()):
            d = annual[year]
            # 누적 라벨 처리
            year_label = f"{year}({period_labels[year]})" if year in period_labels else year

            rev = f"{d.get('revenue', 0):,.0f}" if d.get('revenue') else "-"
            op = f"{d.get('operating_profit', 0):,.0f}" if d.get('operating_profit') else "-"
            ni = f"{d.get('net_income', 0):,.0f}" if d.get('net_income') else "-"
            print(f"{year_label:<15} {rev:>15} {op:>15} {ni:>15}")

    # 성장률
    growth = data.get("growth", {})
    if growth:
        print("\n[2. 성장률 (YoY)]")
        comparison = growth.get("comparison")
        if comparison:
            print(f"비교 기준: {comparison}")
        if growth.get("revenue_yoy") is not None:
            print(f"매출 성장률: {growth['revenue_yoy']:+.1f}%")
        if growth.get("operating_profit_yoy") is not None:
            print(f"영업이익 성장률: {growth['operating_profit_yoy']:+.1f}%")

    # 재무비율
    ratios = data.get("ratios", {})
    if ratios:
        print("\n[3. 재무비율]")
        if ratios.get("debt_ratio") is not None:
            status = "안정" if ratios["debt_ratio"] < 100 else "주의" if ratios["debt_ratio"] < 200 else "위험"
            print(f"부채비율: {ratios['debt_ratio']:.1f}% ({status})")
        if ratios.get("current_ratio") is not None:
            status = "안정" if ratios["current_ratio"] > 150 else "보통" if ratios["current_ratio"] > 100 else "주의"
            print(f"유동비율: {ratios['current_ratio']:.1f}% ({status})")
        if ratios.get("roe") is not None:
            status = "우수" if ratios["roe"] > 15 else "보통" if ratios["roe"] > 5 else "부진"
            print(f"ROE: {ratios['roe']:.1f}% ({status})")
        if ratios.get("roa") is not None:
            status = "우수" if ratios["roa"] > 5 else "보통" if ratios["roa"] > 2 else "부진"
            print(f"ROA: {ratios['roa']:.1f}% ({status})")

    # 현금흐름
    cash_flow = data.get("cash_flow", {})
    if cash_flow:
        print("\n[4. 현금흐름 (억원)]")
        for year in sorted(cash_flow.keys(), reverse=True)[:2]:
            cf = cash_flow[year]
            year_label = f"{year}({period_labels[year]})" if year in period_labels else year
            ocf = cf.get("operating_cash_flow")
            fcf = cf.get("fcf")
            ocf_str = f"{ocf:,.0f}" if ocf else "-"
            fcf_str = f"{fcf:,.0f}" if fcf else "-"
            print(f"{year_label}: 영업CF {ocf_str} / FCF {fcf_str}")

    print("\n" + "=" * 60)
    print(f"출처: {data.get('source')}")
    print("=" * 60)
```

**Step 2: Test report output**

Run: `cd /Users/michael/public_agents/plugins/stock-analyzer-advanced && python -c "from utils import print_fi_report; print_fi_report('005930')"`
Expected: Formatted report with Samsung Electronics data

**Step 3: Commit**

```bash
git add utils/financial_scraper.py
git commit -m "feat(fi): update print_fi_report with ratios and cash flow"
```

---

## Task 5: Update FI Agent Documentation

**Files:**
- Modify: `/Users/michael/public_agents/plugins/stock-analyzer-advanced/agents/financial-intelligence.md`

**Step 1: Update data source section**

Replace the "데이터 소스 우선순위" section (lines ~39-58) with:

```markdown
### 데이터 소스 우선순위 (CRITICAL)

```
┌─────────────────────────────────────────┐
│ 1순위: FnGuide (div ID 기반 파싱)       │
│        utils.get_financial_data()       │
│        - divSonikY: 연간 손익계산서     │
│        - divDaechaY: 연간 재무상태표    │
│        - divCashY: 연간 현금흐름표      │
│        ⚠️ retry 최소 1회 필수           │
│        ↓ None 반환 시                   │
├─────────────────────────────────────────┤
│ 2순위: yfinance MCP (US stocks only)    │
│        MCP: yfinance_get_ticker_info    │
│        ↓ 실패 시                        │
├─────────────────────────────────────────┤
│ ❌ FAIL: 모든 방법 실패                 │
│    "재무제표 수집 실패" 명시적 보고     │
└─────────────────────────────────────────┘
```

**⚠️ 중요: FnGuide 파싱 개선사항**

1. **div ID 기반 파싱**: `divSonikY`, `divDaechaY`, `divCashY` 사용 (기존 `um_table` 클래스 대체)
2. **누적 기간 자동 감지**: 2025년 3분기까지만 있으면 "2025(3Q누적)"으로 표시
3. **완결 연도 기준 YoY**: 누적 데이터 제외하고 완결 연도끼리 비교
4. **확장된 재무비율**: 부채비율, 유동비율, ROE, ROA, FCF
```

**Step 2: Update return data structure section**

Replace the "반환 데이터 구조" section (lines ~159-185) with:

```markdown
### 반환 데이터 구조

```python
{
    "source": "FnGuide",
    "ticker": "005930",
    "name": "삼성전자",
    "period": "2024/12",
    "annual": {
        "2022": {"revenue": 3022314, "operating_profit": 433766, "net_income": 556541},
        "2023": {"revenue": 2589355, "operating_profit": 65670, "net_income": 154871},
        "2024": {"revenue": 3008709, "operating_profit": 327260, "net_income": 344514},
        "2025": {"revenue": 1234567, ...}  # 누적 데이터
    },
    "balance": {
        "2024": {
            "total_assets": ...,
            "current_assets": ...,
            "total_liabilities": ...,
            "current_liabilities": ...,
            "total_equity": ...
        }
    },
    "cash_flow": {
        "2024": {
            "operating_cash_flow": ...,
            "investing_cash_flow": ...,
            "financing_cash_flow": ...,
            "fcf": ...  # 계산됨: operating + investing
        }
    },
    "latest": {
        "revenue": ...,
        "operating_profit": ...,
        "net_income": ...,
        "total_assets": ...,
        "total_liabilities": ...,
        "total_equity": ...
    },
    "growth": {
        "revenue_yoy": 16.2,
        "operating_profit_yoy": 398.3,
        "comparison": "2024 vs 2023"  # 비교 대상 명시
    },
    "ratios": {
        "debt_ratio": 45.2,      # 부채비율 (%)
        "current_ratio": 178.5,  # 유동비율 (%)
        "roe": 12.3,             # ROE (%)
        "roa": 8.1               # ROA (%)
    },
    "period_labels": {
        "2025": "3Q누적"  # 누적 기간 라벨
    }
}
```
```

**Step 3: Add FnGuide knowledge reference**

Add at the end of the file (before the closing quote):

```markdown
---

# 📚 FnGuide 참고 사항

## 테이블 ID 구조

| 테이블 ID | 재무제표 유형 | 기간 구분 |
|----------|-------------|----------|
| `divSonikY` | 포괄손익계산서 | 연간 |
| `divSonikQ` | 포괄손익계산서 | 분기 |
| `divDaechaY` | 재무상태표 | 연간 |
| `divCashY` | 현금흐름표 | 연간 |

## 데이터 형식

- **단위**: 억원
- **날짜 형식**: `YYYY/MM` (예: `2024/12`)
- **정밀값**: `<td title="757,882.69">` - title 속성에 소수점 포함

## 주요 메트릭 (rowBold 클래스)

- **손익**: 매출액, 영업이익, 당기순이익
- **재무상태**: 자산, 부채, 자본
- **현금흐름**: 영업활동/투자활동/재무활동으로인한현금흐름
```

**Step 4: Commit**

```bash
git add agents/financial-intelligence.md
git commit -m "docs(fi): update agent with FnGuide knowledge transfer"
```

---

## Task 6: Final Integration Test

**Files:**
- None (testing only)

**Step 1: Test full FI workflow**

Run: `cd /Users/michael/public_agents/plugins/stock-analyzer-advanced && python -c "from utils import print_fi_report; print_fi_report('102370')"`
Expected: 케이옥션 report with:
- 2025(3Q누적) label
- Growth comparison: "2024 vs 2023"
- Ratios: debt_ratio, current_ratio, ROE, ROA

**Step 2: Test another stock**

Run: `cd /Users/michael/public_agents/plugins/stock-analyzer-advanced && python -c "from utils import print_fi_report; print_fi_report('005930')"`
Expected: 삼성전자 report with complete data

**Step 3: Final commit (if all tests pass)**

```bash
git add -A
git commit -m "feat(fi): complete FnGuide knowledge transfer from tier2-analyzer"
```

---

## Summary

This plan transfers the following FnGuide knowledge from tier2-analyzer to stock-analyzer-advanced:

| Feature | Before | After |
|---------|--------|-------|
| Table Parsing | `um_table` class (unreliable) | `divSonikY`, `divDaechaY`, `divCashY` (reliable) |
| Period Detection | None | Auto-detect "3Q누적" |
| Growth Calculation | Compares any two years | Complete years only |
| Financial Ratios | debt_ratio only | + current_ratio, ROE, ROA |
| Cash Flow | Not parsed | Operating/Investing/Financing CF + FCF |
| Data Precision | Text content | `title` attribute (decimal) |

**Estimated Steps:** 6 tasks × ~5 steps each = ~30 bite-sized steps
