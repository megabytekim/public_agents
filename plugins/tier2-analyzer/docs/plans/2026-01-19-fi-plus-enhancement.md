# FI+ Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** FI+에 연간 재무제표(3년), 대차대조표, 현금흐름표 스크래핑 기능을 추가하여 완전한 펀더멘털 분석 지원

**Architecture:** 기존 `quarterly_scraper.py`를 확장하여 6개 FnGuide 테이블 모두 파싱. 공통 파싱 로직 추출 후 테이블별 특화 함수 구현. TDD 방식으로 테스트 먼저 작성.

**Tech Stack:** Python, BeautifulSoup, requests, pytest

---

## 현재 상태

| 테이블 ID | 재무제표 | 구현 상태 |
|----------|---------|----------|
| `divSonikQ` | 분기 손익계산서 | ✅ 구현됨 |
| `divSonikY` | 연간 손익계산서 | ❌ 미구현 |
| `divDaechaY` | 연간 재무상태표 | ❌ 미구현 |
| `divDaechaQ` | 분기 재무상태표 | ❌ 미구현 |
| `divCashY` | 연간 현금흐름표 | ❌ 미구현 |
| `divCashQ` | 분기 현금흐름표 | ❌ 미구현 |

## 목표 출력 구조

```python
{
    "ticker": "005930",
    "name": "삼성전자",
    "source": "FnGuide",

    # 손익계산서
    "income_statement": {
        "annual": {  # 3년
            "2024": {"revenue": ..., "operating_profit": ..., "net_income": ...},
            "2023": {...},
            "2022": {...}
        },
        "quarterly": {  # 8분기 (기존)
            "2024Q4": {...}, ...
        }
    },

    # 재무상태표 (NEW)
    "balance_sheet": {
        "annual": {  # 3년
            "2024": {"total_assets": ..., "total_liabilities": ..., "total_equity": ...,
                     "current_assets": ..., "current_liabilities": ...},
            ...
        },
        "quarterly": {  # 4분기
            "2024Q4": {...}, ...
        }
    },

    # 현금흐름표 (NEW)
    "cash_flow": {
        "annual": {  # 3년
            "2024": {"operating_cf": ..., "investing_cf": ..., "financing_cf": ..., "fcf": ...},
            ...
        },
        "quarterly": {  # 4분기
            "2024Q4": {...}, ...
        }
    },

    # 계산된 지표
    "ratios": {
        "debt_ratio": float,      # 부채비율 = 부채/자본
        "current_ratio": float,   # 유동비율 = 유동자산/유동부채
        "roe": float,             # ROE = 순이익/자본
        "roa": float              # ROA = 순이익/자산
    },

    # 성장률
    "growth": {
        "revenue_yoy": float,
        "operating_profit_yoy": float,
        "net_income_yoy": float
    }
}
```

---

## Task 1: 공통 테이블 파서 리팩토링

**Files:**
- Modify: `utils/quarterly_scraper.py`
- Test: `tests/test_quarterly_scraper.py`

### Step 1: 기존 테스트 확인

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/test_quarterly_scraper.py -v`
Expected: 4 tests PASS

### Step 2: 공통 파싱 함수 추출

기존 `_parse_quarterly_income_statement()` 로직을 일반화하여 재사용 가능한 함수로 분리

```python
# utils/quarterly_scraper.py 상단에 추가

def _parse_fnguide_table(soup: BeautifulSoup, div_id: str, target_metrics: list) -> Optional[dict]:
    """FnGuide 테이블 공통 파싱 함수

    Args:
        soup: BeautifulSoup 객체
        div_id: 테이블이 포함된 div ID (예: 'divSonikQ', 'divDaechaY')
        target_metrics: 추출할 항목명 리스트 (예: ['매출액', '영업이익'])

    Returns:
        {period: {metric: value}} 형태의 딕셔너리
    """
    div = soup.find("div", id=div_id)
    if not div:
        return None

    table = div.find("table")
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


def _extract_data_rows_generic(table, target_metrics: list) -> dict:
    """데이터 행 추출 - 지정된 항목만"""
    data_rows = {}
    tbody = table.find("tbody")
    if not tbody:
        return data_rows

    for tr in tbody.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) < 2:
            continue

        row_name = cells[0].text.strip().replace("\xa0", "").strip()

        # rowBold 클래스 또는 target_metrics에 포함된 항목만
        row_classes = tr.get("class", [])
        is_bold = "rowBold" in row_classes

        if not is_bold and row_name not in target_metrics:
            continue

        values = []
        for cell in cells[1:]:
            value_str = cell.get("title") or cell.text.strip()
            value = _parse_numeric_value(value_str)
            values.append(value)

        if row_name and values:
            data_rows[row_name] = values

    return data_rows


def _convert_period_to_key(period: str, div_id: str) -> Optional[str]:
    """기간을 키로 변환

    연간 테이블 (divSonikY, divDaechaY, divCashY): "2024/12" -> "2024"
    분기 테이블 (divSonikQ, divDaechaQ, divCashQ): "2024/12" -> "2024Q4"
    """
    if "전년" in period or "%" in period:
        return None

    match = re.match(r"(\d{4})/(\d{2})", period)
    if not match:
        return None

    year = match.group(1)
    month = int(match.group(2))

    # 연간 테이블
    if div_id.endswith("Y"):
        return year

    # 분기 테이블
    quarter = MONTH_TO_QUARTER.get(month)
    if quarter:
        return f"{year}Q{quarter}"

    return None
```

### Step 3: 기존 테스트 재실행하여 리팩토링 확인

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/test_quarterly_scraper.py -v`
Expected: 4 tests PASS (기존 동작 유지)

### Step 4: 커밋

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
git add utils/quarterly_scraper.py
git commit -m "refactor: extract common table parsing logic"
```

---

## Task 2: 연간 손익계산서 스크래핑 (divSonikY)

**Files:**
- Modify: `utils/quarterly_scraper.py`
- Modify: `tests/test_quarterly_scraper.py`

### Step 1: 실패하는 테스트 작성

```python
# tests/test_quarterly_scraper.py에 추가

def test_get_fnguide_annual_income_returns_three_years():
    """연간 손익계산서가 최근 3년 데이터를 반환하는지 확인"""
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
```

### Step 2: 테스트 실행하여 실패 확인

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/test_quarterly_scraper.py::test_get_fnguide_annual_income_returns_three_years -v`
Expected: FAIL with "NameError: name 'get_fnguide_annual_income' is not defined"

### Step 3: 최소 구현 작성

```python
# utils/quarterly_scraper.py에 추가

# 연간 손익계산서 추출 대상 항목
ANNUAL_INCOME_METRICS = ["매출액", "영업이익", "영업이익(발표기준)", "당기순이익", "지배주주순이익"]

# 연간 손익계산서 항목명 -> 영문 키 매핑
ANNUAL_INCOME_KEY_MAP = {
    "매출액": "revenue",
    "영업이익": "operating_profit",
    "영업이익(발표기준)": "operating_profit",
    "당기순이익": "net_income",
    "지배주주순이익": "net_income_controlling",
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

    annual_data = _parse_fnguide_table(
        soup,
        "divSonikY",
        ANNUAL_INCOME_METRICS
    )

    if not annual_data:
        return None

    # 영문 키로 변환
    converted = {}
    for year, data in annual_data.items():
        converted[year] = {}
        for kr_key, value in data.items():
            eng_key = ANNUAL_INCOME_KEY_MAP.get(kr_key)
            if eng_key:
                converted[year][eng_key] = value

    return {
        "source": "FnGuide",
        "ticker": ticker,
        "name": name,
        "annual": converted,
    }
```

### Step 4: _get_english_key 함수 수정

```python
# utils/quarterly_scraper.py - 기존 함수 확장

def _get_english_key(korean_name: str, div_id: str) -> Optional[str]:
    """한글 항목명을 영문 키로 변환 (테이블 타입에 따라 다른 매핑)"""

    # 손익계산서 (divSonikY, divSonikQ)
    if "Sonik" in div_id:
        mapping = {
            "매출액": "revenue",
            "영업이익": "operating_profit",
            "영업이익(발표기준)": "operating_profit",
            "당기순이익": "net_income",
            "지배주주순이익": "net_income_controlling",
            "세전계속사업이익": "pretax_income",
        }
        return mapping.get(korean_name)

    # 재무상태표 (divDaechaY, divDaechaQ)
    if "Daecha" in div_id:
        mapping = {
            "자산": "total_assets",
            "유동자산": "current_assets",
            "비유동자산": "non_current_assets",
            "부채": "total_liabilities",
            "유동부채": "current_liabilities",
            "비유동부채": "non_current_liabilities",
            "자본": "total_equity",
            "지배기업주주지분": "equity_controlling",
        }
        return mapping.get(korean_name)

    # 현금흐름표 (divCashY, divCashQ)
    if "Cash" in div_id:
        mapping = {
            "영업활동으로인한현금흐름": "operating_cf",
            "투자활동으로인한현금흐름": "investing_cf",
            "재무활동으로인한현금흐름": "financing_cf",
            "현금및현금성자산의증가": "cash_change",
            "기말현금및현금성자산": "cash_end",
        }
        return mapping.get(korean_name)

    return None
```

### Step 5: 테스트 실행하여 통과 확인

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/test_quarterly_scraper.py::test_get_fnguide_annual_income_returns_three_years -v`
Expected: PASS

### Step 6: 커밋

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
git add utils/quarterly_scraper.py tests/test_quarterly_scraper.py
git commit -m "feat: add annual income statement scraping (divSonikY)"
```

---

## Task 3: 연간 재무상태표 스크래핑 (divDaechaY)

**Files:**
- Modify: `utils/quarterly_scraper.py`
- Modify: `tests/test_quarterly_scraper.py`

### Step 1: 실패하는 테스트 작성

```python
# tests/test_quarterly_scraper.py에 추가

def test_get_fnguide_annual_balance_sheet_returns_three_years():
    """연간 재무상태표가 최근 3년 데이터를 반환하는지 확인"""
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


def test_get_fnguide_annual_balance_sheet_calculates_ratios():
    """재무상태표에서 재무비율이 계산되는지 확인"""
    result = get_fnguide_annual_balance_sheet("005930")

    assert result is not None
    assert "ratios" in result

    ratios = result["ratios"]
    assert "debt_ratio" in ratios  # 부채비율
    assert "current_ratio" in ratios  # 유동비율
```

### Step 2: 테스트 실행하여 실패 확인

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/test_quarterly_scraper.py::test_get_fnguide_annual_balance_sheet_returns_three_years -v`
Expected: FAIL

### Step 3: 최소 구현 작성

```python
# utils/quarterly_scraper.py에 추가

BALANCE_SHEET_METRICS = [
    "자산", "유동자산", "비유동자산",
    "부채", "유동부채", "비유동부채",
    "자본", "지배기업주주지분"
]


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

    annual_data = _parse_fnguide_table(
        soup,
        "divDaechaY",
        BALANCE_SHEET_METRICS
    )

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
    """재무상태표 기반 재무비율 계산"""
    ratios = {
        "debt_ratio": None,
        "current_ratio": None,
    }

    if not annual_data:
        return ratios

    # 최신 연도 데이터
    latest_year = max(annual_data.keys())
    latest = annual_data[latest_year]

    total_liabilities = latest.get("total_liabilities")
    total_equity = latest.get("total_equity")
    current_assets = latest.get("current_assets")
    current_liabilities = latest.get("current_liabilities")

    # 부채비율 = 부채 / 자본 * 100
    if total_liabilities and total_equity and total_equity != 0:
        ratios["debt_ratio"] = round(total_liabilities / total_equity * 100, 2)

    # 유동비율 = 유동자산 / 유동부채 * 100
    if current_assets and current_liabilities and current_liabilities != 0:
        ratios["current_ratio"] = round(current_assets / current_liabilities * 100, 2)

    return ratios
```

### Step 4: 테스트 실행하여 통과 확인

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/test_quarterly_scraper.py -k "balance_sheet" -v`
Expected: 2 tests PASS

### Step 5: 커밋

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
git add utils/quarterly_scraper.py tests/test_quarterly_scraper.py
git commit -m "feat: add annual balance sheet scraping with ratios (divDaechaY)"
```

---

## Task 4: 연간 현금흐름표 스크래핑 (divCashY)

**Files:**
- Modify: `utils/quarterly_scraper.py`
- Modify: `tests/test_quarterly_scraper.py`

### Step 1: 실패하는 테스트 작성

```python
# tests/test_quarterly_scraper.py에 추가

def test_get_fnguide_annual_cash_flow_returns_three_years():
    """연간 현금흐름표가 최근 3년 데이터를 반환하는지 확인"""
    result = get_fnguide_annual_cash_flow("005930")  # 삼성전자

    assert result is not None
    assert "annual" in result

    annual = result["annual"]
    assert len(annual) >= 3

    for year, data in list(annual.items())[:3]:
        assert "operating_cf" in data
        assert "investing_cf" in data
        assert "financing_cf" in data


def test_get_fnguide_annual_cash_flow_calculates_fcf():
    """현금흐름표에서 FCF가 계산되는지 확인"""
    result = get_fnguide_annual_cash_flow("005930")

    assert result is not None

    # FCF = 영업CF + 투자CF (투자CF는 보통 음수)
    annual = result["annual"]
    latest_year = max(annual.keys())
    latest = annual[latest_year]

    if latest.get("operating_cf") and latest.get("investing_cf"):
        expected_fcf = latest["operating_cf"] + latest["investing_cf"]
        assert "fcf" in latest
        assert abs(latest["fcf"] - expected_fcf) < 1  # 반올림 오차 허용
```

### Step 2: 테스트 실행하여 실패 확인

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/test_quarterly_scraper.py::test_get_fnguide_annual_cash_flow_returns_three_years -v`
Expected: FAIL

### Step 3: 최소 구현 작성

```python
# utils/quarterly_scraper.py에 추가

CASH_FLOW_METRICS = [
    "영업활동으로인한현금흐름",
    "투자활동으로인한현금흐름",
    "재무활동으로인한현금흐름",
    "현금및현금성자산의증가",
    "기말현금및현금성자산"
]


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
                    "operating_cf": ...,
                    "investing_cf": ...,
                    "financing_cf": ...,
                    "fcf": ...  # 계산됨
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

    annual_data = _parse_fnguide_table(
        soup,
        "divCashY",
        CASH_FLOW_METRICS
    )

    if not annual_data:
        return None

    # FCF 계산 추가
    for year, data in annual_data.items():
        operating_cf = data.get("operating_cf")
        investing_cf = data.get("investing_cf")
        if operating_cf is not None and investing_cf is not None:
            data["fcf"] = operating_cf + investing_cf

    return {
        "source": "FnGuide",
        "ticker": ticker,
        "name": name,
        "annual": annual_data,
    }
```

### Step 4: 테스트 실행하여 통과 확인

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/test_quarterly_scraper.py -k "cash_flow" -v`
Expected: 2 tests PASS

### Step 5: 커밋

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
git add utils/quarterly_scraper.py tests/test_quarterly_scraper.py
git commit -m "feat: add annual cash flow scraping with FCF calculation (divCashY)"
```

---

## Task 5: 통합 함수 구현 (get_fnguide_full_financials)

**Files:**
- Modify: `utils/quarterly_scraper.py`
- Modify: `tests/test_quarterly_scraper.py`

### Step 1: 실패하는 테스트 작성

```python
# tests/test_quarterly_scraper.py에 추가

def test_get_fnguide_full_financials_returns_all_statements():
    """통합 함수가 모든 재무제표를 반환하는지 확인"""
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
```

### Step 2: 테스트 실행하여 실패 확인

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/test_quarterly_scraper.py::test_get_fnguide_full_financials_returns_all_statements -v`
Expected: FAIL

### Step 3: 최소 구현 작성

```python
# utils/quarterly_scraper.py에 추가

def get_fnguide_full_financials(ticker: str) -> Optional[dict]:
    """FnGuide에서 전체 재무제표 데이터를 가져옵니다.

    단일 HTTP 요청으로 모든 재무제표를 파싱합니다.

    Args:
        ticker: 종목코드 (예: "005930")

    Returns:
        {
            "ticker": "005930",
            "name": "삼성전자",
            "source": "FnGuide",
            "income_statement": {
                "annual": {...},
                "quarterly": {...}
            },
            "balance_sheet": {
                "annual": {...}
            },
            "cash_flow": {
                "annual": {...}
            },
            "ratios": {
                "debt_ratio": float,
                "current_ratio": float,
                "roe": float,
                "roa": float
            },
            "growth": {
                "revenue_yoy": float,
                "operating_profit_yoy": float
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

    # 손익계산서
    income_annual = _parse_fnguide_table(soup, "divSonikY", ANNUAL_INCOME_METRICS)
    income_quarterly = _parse_fnguide_table(soup, "divSonikQ", TARGET_METRICS)

    # 재무상태표
    balance_annual = _parse_fnguide_table(soup, "divDaechaY", BALANCE_SHEET_METRICS)

    # 현금흐름표
    cash_annual = _parse_fnguide_table(soup, "divCashY", CASH_FLOW_METRICS)

    # FCF 계산
    if cash_annual:
        for year, data in cash_annual.items():
            operating_cf = data.get("operating_cf")
            investing_cf = data.get("investing_cf")
            if operating_cf is not None and investing_cf is not None:
                data["fcf"] = operating_cf + investing_cf

    # 재무비율 계산
    ratios = _calculate_full_ratios(income_annual, balance_annual)

    # 성장률 계산
    growth = _calculate_growth_rates(income_annual)

    return {
        "ticker": ticker,
        "name": name,
        "source": "FnGuide",
        "income_statement": {
            "annual": income_annual or {},
            "quarterly": income_quarterly or {},
        },
        "balance_sheet": {
            "annual": balance_annual or {},
        },
        "cash_flow": {
            "annual": cash_annual or {},
        },
        "ratios": ratios,
        "growth": growth,
    }


def _calculate_full_ratios(income_data: dict, balance_data: dict) -> dict:
    """전체 재무비율 계산"""
    ratios = {
        "debt_ratio": None,
        "current_ratio": None,
        "roe": None,
        "roa": None,
    }

    if not balance_data:
        return ratios

    latest_year = max(balance_data.keys())
    balance = balance_data[latest_year]

    total_liabilities = balance.get("total_liabilities")
    total_equity = balance.get("total_equity")
    current_assets = balance.get("current_assets")
    current_liabilities = balance.get("current_liabilities")
    total_assets = balance.get("total_assets")

    # 부채비율
    if total_liabilities and total_equity and total_equity != 0:
        ratios["debt_ratio"] = round(total_liabilities / total_equity * 100, 2)

    # 유동비율
    if current_assets and current_liabilities and current_liabilities != 0:
        ratios["current_ratio"] = round(current_assets / current_liabilities * 100, 2)

    # ROE, ROA (손익계산서 필요)
    if income_data and latest_year in income_data:
        net_income = income_data[latest_year].get("net_income")

        if net_income and total_equity and total_equity != 0:
            ratios["roe"] = round(net_income / total_equity * 100, 2)

        if net_income and total_assets and total_assets != 0:
            ratios["roa"] = round(net_income / total_assets * 100, 2)

    return ratios


def _calculate_growth_rates(income_data: dict) -> dict:
    """성장률 계산 (YoY)"""
    growth = {
        "revenue_yoy": None,
        "operating_profit_yoy": None,
    }

    if not income_data or len(income_data) < 2:
        return growth

    sorted_years = sorted(income_data.keys(), reverse=True)
    latest_year = sorted_years[0]
    prev_year = sorted_years[1]

    latest = income_data[latest_year]
    prev = income_data[prev_year]

    # 매출 성장률
    if latest.get("revenue") and prev.get("revenue") and prev["revenue"] != 0:
        growth["revenue_yoy"] = round(
            (latest["revenue"] - prev["revenue"]) / abs(prev["revenue"]) * 100, 2
        )

    # 영업이익 성장률
    if latest.get("operating_profit") and prev.get("operating_profit") and prev["operating_profit"] != 0:
        growth["operating_profit_yoy"] = round(
            (latest["operating_profit"] - prev["operating_profit"]) / abs(prev["operating_profit"]) * 100, 2
        )

    return growth
```

### Step 4: 테스트 실행하여 통과 확인

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/test_quarterly_scraper.py::test_get_fnguide_full_financials_returns_all_statements -v`
Expected: PASS

### Step 5: 커밋

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
git add utils/quarterly_scraper.py tests/test_quarterly_scraper.py
git commit -m "feat: add get_fnguide_full_financials unified function"
```

---

## Task 6: utils/__init__.py 업데이트 및 FI+ 에이전트 수정

**Files:**
- Modify: `utils/__init__.py`
- Modify: `agents/fi-plus.md`

### Step 1: utils/__init__.py export 확인

```python
# utils/__init__.py

from .quarterly_scraper import (
    get_fnguide_quarterly,
    get_fnguide_annual_income,
    get_fnguide_annual_balance_sheet,
    get_fnguide_annual_cash_flow,
    get_fnguide_full_financials,
)
from .peer_comparison import get_peer_comparison, get_sector_average

__all__ = [
    "get_fnguide_quarterly",
    "get_fnguide_annual_income",
    "get_fnguide_annual_balance_sheet",
    "get_fnguide_annual_cash_flow",
    "get_fnguide_full_financials",
    "get_peer_comparison",
    "get_sector_average",
]
```

### Step 2: FI+ 에이전트 문서 업데이트

`agents/fi-plus.md` 수정하여 새로운 함수 사용 예시 추가:

- Step 1: 통합 재무 데이터 수집 (`get_fnguide_full_financials`)
- Step 2: 피어 비교 (기존)
- Output Format에 대차대조표, 현금흐름표 섹션 추가

### Step 3: 커밋

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
git add utils/__init__.py agents/fi-plus.md
git commit -m "feat: update exports and FI+ agent with full financials support"
```

---

## Task 7: 전체 테스트 및 검증

**Files:**
- All modified files

### Step 1: 전체 테스트 실행

Run: `cd /Users/michael/public_agents/plugins/tier2-analyzer && pytest tests/ -v`
Expected: All tests PASS (기존 8개 + 신규 6개 = 14개)

### Step 2: 실제 데이터 검증

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer && python3 << 'EOF'
from utils import get_fnguide_full_financials
import json

result = get_fnguide_full_financials("005930")  # 삼성전자
if result:
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
else:
    print("Failed to fetch data")
EOF
```

Expected: 삼성전자의 전체 재무제표 데이터 출력 (손익계산서, 재무상태표, 현금흐름표, 재무비율, 성장률)

### Step 3: 최종 커밋

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
git add .
git commit -m "feat: complete FI+ enhancement with full financial statements"
```

---

## Summary

| Task | 내용 | 예상 테스트 |
|------|------|------------|
| 1 | 공통 테이블 파서 리팩토링 | 기존 4개 유지 |
| 2 | 연간 손익계산서 (divSonikY) | +1 |
| 3 | 연간 재무상태표 (divDaechaY) | +2 |
| 4 | 연간 현금흐름표 (divCashY) | +2 |
| 5 | 통합 함수 (get_fnguide_full_financials) | +1 |
| 6 | Export 및 에이전트 업데이트 | - |
| 7 | 전체 테스트 및 검증 | 14개 총 |

**총 신규 기능:**
- 연간 손익계산서 3년
- 연간 재무상태표 3년 + 부채비율/유동비율
- 연간 현금흐름표 3년 + FCF
- 통합 조회 함수 (단일 HTTP 요청)
- ROE, ROA 자동 계산
