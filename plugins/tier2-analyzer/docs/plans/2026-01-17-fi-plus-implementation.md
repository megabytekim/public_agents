# FI+ (Financial Intelligence Plus) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 분기 재무 데이터 수집 + 동종업계 밸류에이션 비교 기능을 제공하는 FI+ 에이전트 구현

**Architecture:** FnGuide 분기 테이블 파싱으로 8분기 데이터 수집, DART API로 현금흐름 보완, 섹터 평균 계산으로 피어 비교 테이블 생성. utils에 Python 함수 구현 후 에이전트 markdown 작성.

**Tech Stack:** Python 3.8+, requests, BeautifulSoup4, OpenDART API, pytest

---

## Phase 1: 분기 재무 데이터 수집

### Task 1: FnGuide 분기 테이블 구조 분석

**Files:**
- Create: `plugins/tier2-analyzer/docs/fnguide-quarterly-structure.md`

**Step 1: FnGuide 페이지 구조 분석**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
curl -s "https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A005930" \
  -H "User-Agent: Mozilla/5.0" | grep -o 'um_table' | head -5
```

Expected: `um_table` 클래스 확인

**Step 2: 분기 컬럼 패턴 확인**

FnGuide 페이지에서 분기 데이터 컬럼 형식 확인:
- 연간: `2024/12`, `2023/12`
- 분기: `2024/09`, `2024/06`, `2024/03`

**Step 3: 구조 문서화**

```markdown
# FnGuide 분기 테이블 구조

## URL 패턴
https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{ticker}

## 테이블 구조
- Table 0: 연간 손익계산서 (Annual)
- Table 1: 분기 손익계산서 (Quarterly) ← 타겟
- Table 2: 연간 재무상태표
- Table 3: 분기 재무상태표

## 분기 컬럼 형식
"2024/09" = 2024년 3분기
"2024/06" = 2024년 2분기
```

**Step 4: Commit**

```bash
git add plugins/tier2-analyzer/docs/fnguide-quarterly-structure.md
git commit -m "docs: add FnGuide quarterly table structure analysis"
```

---

### Task 2: 분기 재무 파싱 테스트 작성

**Files:**
- Create: `plugins/tier2-analyzer/tests/__init__.py`
- Create: `plugins/tier2-analyzer/tests/test_quarterly_scraper.py`
- Create: `plugins/tier2-analyzer/utils/__init__.py`

**Step 1: 테스트 디렉토리 초기화**

```bash
mkdir -p /Users/michael/public_agents/plugins/tier2-analyzer/tests
mkdir -p /Users/michael/public_agents/plugins/tier2-analyzer/utils
touch /Users/michael/public_agents/plugins/tier2-analyzer/tests/__init__.py
touch /Users/michael/public_agents/plugins/tier2-analyzer/utils/__init__.py
```

**Step 2: Write the failing test**

```python
# plugins/tier2-analyzer/tests/test_quarterly_scraper.py
"""FI+ 분기 재무 스크래퍼 테스트"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetFnguideQuarterly:
    """get_fnguide_quarterly() 함수 테스트"""

    def test_returns_quarterly_data_structure(self):
        """분기 데이터 구조 반환 확인"""
        from utils.quarterly_scraper import get_fnguide_quarterly

        # 삼성전자 테스트 (실제 API 호출)
        result = get_fnguide_quarterly("005930")

        assert result is not None
        assert "quarterly" in result
        assert "source" in result
        assert result["source"] == "FnGuide"

    def test_quarterly_has_recent_quarters(self):
        """최근 분기 데이터 포함 확인"""
        from utils.quarterly_scraper import get_fnguide_quarterly

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
        from utils.quarterly_scraper import get_fnguide_quarterly

        result = get_fnguide_quarterly("005930")

        assert result is not None
        quarterly = result.get("quarterly", {})

        # 첫 번째 분기 데이터 확인
        first_quarter = list(quarterly.values())[0] if quarterly else {}

        assert "revenue" in first_quarter or "매출액" in str(first_quarter)

    def test_invalid_ticker_returns_none(self):
        """잘못된 티커는 None 반환"""
        from utils.quarterly_scraper import get_fnguide_quarterly

        result = get_fnguide_quarterly("999999")

        assert result is None
```

**Step 3: Run test to verify it fails**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
python -m pytest tests/test_quarterly_scraper.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tier2.utils.quarterly_scraper'`

**Step 4: Commit failing test**

```bash
git add plugins/tier2-analyzer/tests/ plugins/tier2-analyzer/utils/__init__.py
git commit -m "test: add failing tests for quarterly scraper"
```

---

### Task 3: 분기 재무 파싱 함수 구현

**Files:**
- Create: `plugins/tier2-analyzer/utils/quarterly_scraper.py`

**Step 1: Write minimal implementation**

```python
# plugins/tier2-analyzer/utils/quarterly_scraper.py
"""FnGuide 분기 재무제표 스크래퍼

FI+ 에이전트용 분기 데이터 수집 함수
"""
import re
import time
from typing import Optional
import requests
from bs4 import BeautifulSoup


def get_fnguide_quarterly(ticker: str, retry: int = 2) -> Optional[dict]:
    """
    FnGuide에서 분기 재무제표 스크래핑

    Args:
        ticker: 종목코드 (예: "005930")
        retry: 실패 시 재시도 횟수

    Returns:
        {
            "source": "FnGuide",
            "ticker": "005930",
            "name": "삼성전자",
            "quarterly": {
                "2024Q4": {"revenue": ..., "operating_profit": ..., "net_income": ...},
                "2024Q3": {...},
                ...
            },
            "growth": {
                "revenue_qoq": float,  # 전분기 대비
                "revenue_yoy": float,  # 전년 동기 대비
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

            # 종목명 추출
            title = soup.find("title")
            name = None
            if title:
                title_text = title.get_text(strip=True)
                match = re.match(r'^([^(]+)\(', title_text)
                if match:
                    name = match.group(1).strip()

            # um_table div들 찾기
            tables = soup.find_all("div", class_="um_table")
            if len(tables) < 2:
                raise ValueError("Required tables not found")

            # Table 1: 분기 손익계산서 (두 번째 테이블)
            quarterly_table = tables[1] if len(tables) > 1 else None
            quarterly_data = _parse_quarterly_table(quarterly_table) if quarterly_table else {}

            if not quarterly_data:
                raise ValueError("Failed to parse quarterly data")

            # 성장률 계산
            growth = _calculate_growth(quarterly_data)

            result = {
                "source": "FnGuide",
                "ticker": ticker,
                "name": name,
                "quarterly": quarterly_data,
                "growth": growth,
            }

            return result

        except Exception as e:
            if attempt < retry:
                time.sleep(1)
                continue
            return None

    return None


def _parse_quarterly_table(table) -> dict:
    """분기 손익계산서 테이블 파싱"""
    result = {}

    try:
        rows = table.find_all("tr")
        if not rows:
            return result

        # 헤더에서 분기 추출
        header_row = rows[0]
        quarters = []
        ths = header_row.find_all("th")

        for th in ths:
            text = th.get_text(strip=True)
            # "2024/09" 형식에서 분기 추출
            match = re.search(r'(\d{4})/(\d{2})', text)
            if match:
                year = match.group(1)
                month = match.group(2)
                quarter = _month_to_quarter(month)
                quarter_key = f"{year}Q{quarter}"
                quarters.append(quarter_key)

        # 분기별 데이터 초기화
        for q in quarters[:8]:  # 최근 8분기
            result[q] = {}

        # 데이터 행 파싱
        for row in rows[1:]:
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue

            label = cells[0].get_text(strip=True)
            values = [_parse_number(c.get_text(strip=True)) for c in cells[1:]]

            # 매출액
            if label == "매출액":
                for i, q in enumerate(quarters[:8]):
                    if i < len(values) and values[i] is not None:
                        result[q]["revenue"] = values[i]

            # 영업이익
            elif label == "영업이익":
                for i, q in enumerate(quarters[:8]):
                    if i < len(values) and values[i] is not None:
                        result[q]["operating_profit"] = values[i]

            # 당기순이익
            elif "당기순이익" in label and "지배" not in label:
                for i, q in enumerate(quarters[:8]):
                    if i < len(values) and values[i] is not None:
                        result[q]["net_income"] = values[i]

    except Exception:
        pass

    # 빈 분기 제거
    result = {k: v for k, v in result.items() if v}

    return result


def _month_to_quarter(month: str) -> int:
    """월을 분기로 변환"""
    month_int = int(month)
    if month_int <= 3:
        return 1
    elif month_int <= 6:
        return 2
    elif month_int <= 9:
        return 3
    else:
        return 4


def _calculate_growth(quarterly: dict) -> dict:
    """분기 성장률 계산"""
    growth = {}

    quarters = sorted(quarterly.keys(), reverse=True)
    if len(quarters) < 2:
        return growth

    latest = quarterly.get(quarters[0], {})
    prev = quarterly.get(quarters[1], {})

    # QoQ (전분기 대비)
    if latest.get("revenue") and prev.get("revenue") and prev["revenue"] != 0:
        growth["revenue_qoq"] = round(
            (latest["revenue"] - prev["revenue"]) / prev["revenue"] * 100, 2
        )

    # YoY (전년 동기 대비) - 4분기 전과 비교
    if len(quarters) >= 5:
        yoy_prev = quarterly.get(quarters[4], {})
        if latest.get("revenue") and yoy_prev.get("revenue") and yoy_prev["revenue"] != 0:
            growth["revenue_yoy"] = round(
                (latest["revenue"] - yoy_prev["revenue"]) / yoy_prev["revenue"] * 100, 2
            )

    return growth


def _parse_number(text: str) -> Optional[int]:
    """텍스트에서 숫자 추출 (억원 단위)"""
    try:
        clean = re.sub(r'[,\s]', '', text)
        match = re.match(r'^-?\d+', clean)
        if match:
            return int(match.group())
        return None
    except:
        return None


if __name__ == "__main__":
    import json
    result = get_fnguide_quarterly("005930")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
```

**Step 2: Run test to verify it passes**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
python -m pytest tests/test_quarterly_scraper.py -v
```

Expected: PASS (일부 테스트는 실제 API 상태에 따라 다를 수 있음)

**Step 3: Commit**

```bash
git add plugins/tier2-analyzer/utils/quarterly_scraper.py
git commit -m "feat: implement quarterly financial scraper for FI+"
```

---

### Task 4: 피어 비교 테스트 작성

**Files:**
- Create: `plugins/tier2-analyzer/tests/test_peer_comparison.py`

**Step 1: Write the failing test**

```python
# plugins/tier2-analyzer/tests/test_peer_comparison.py
"""피어 비교 기능 테스트"""
import pytest


class TestGetPeerComparison:
    """get_peer_comparison() 함수 테스트"""

    def test_returns_comparison_table(self):
        """비교 테이블 반환 확인"""
        from utils.peer_comparison import get_peer_comparison

        # 카카오페이와 피어 비교
        result = get_peer_comparison(
            ticker="377300",
            peers=["035420", "035720"]  # 네이버, 카카오
        )

        assert result is not None
        assert "target" in result
        assert "peers" in result
        assert "sector_avg" in result

    def test_calculates_premium_discount(self):
        """프리미엄/디스카운트 계산 확인"""
        from utils.peer_comparison import get_peer_comparison

        result = get_peer_comparison(
            ticker="377300",
            peers=["035420"]
        )

        assert result is not None
        assert "premium_discount" in result
        # PER 기준 프리미엄/디스카운트 (%)
        assert isinstance(result["premium_discount"].get("per"), (int, float, type(None)))


class TestGetSectorAverage:
    """get_sector_average() 함수 테스트"""

    def test_returns_sector_metrics(self):
        """섹터 평균 지표 반환"""
        from utils.peer_comparison import get_sector_average

        result = get_sector_average(tickers=["377300", "035420", "035720"])

        assert result is not None
        assert "avg_per" in result or "per" in result
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
python -m pytest tests/test_peer_comparison.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Commit failing test**

```bash
git add plugins/tier2-analyzer/tests/test_peer_comparison.py
git commit -m "test: add failing tests for peer comparison"
```

---

### Task 5: 피어 비교 함수 구현

**Files:**
- Create: `plugins/tier2-analyzer/utils/peer_comparison.py`

**Step 1: Write minimal implementation**

```python
# plugins/tier2-analyzer/utils/peer_comparison.py
"""피어 비교 유틸리티

동종업계 밸류에이션 비교 기능
"""
import sys
from typing import Optional, List
from pathlib import Path

# Tier 1 utils 경로 추가
TIER1_PATH = Path(__file__).parent.parent.parent / "plugins" / "stock-analyzer-advanced"
sys.path.insert(0, str(TIER1_PATH))

try:
    from utils.web_scraper import get_naver_stock_info
    from utils.data_fetcher import get_ticker_name
except ImportError:
    # Fallback: 함수가 없으면 None 반환하는 스텁
    def get_naver_stock_info(ticker):
        return None
    def get_ticker_name(ticker):
        return None


def get_peer_comparison(
    ticker: str,
    peers: List[str],
    include_sector_avg: bool = True
) -> Optional[dict]:
    """
    피어 그룹 밸류에이션 비교

    Args:
        ticker: 대상 종목코드
        peers: 비교 대상 종목코드 리스트
        include_sector_avg: 섹터 평균 포함 여부

    Returns:
        {
            "target": {
                "ticker": "377300",
                "name": "카카오페이",
                "per": 33.17,
                "pbr": 3.55,
                "market_cap": "6.72조"
            },
            "peers": [
                {"ticker": "035420", "name": "네이버", "per": 28.5, ...},
                ...
            ],
            "sector_avg": {
                "per": 30.2,
                "pbr": 3.1
            },
            "premium_discount": {
                "per": 10.0,  # 섹터 대비 10% 프리미엄
                "pbr": 14.5
            }
        }
    """
    # 타겟 종목 정보
    target_info = get_naver_stock_info(ticker)
    target_name = get_ticker_name(ticker)

    if not target_info:
        return None

    target = {
        "ticker": ticker,
        "name": target_name or target_info.get("name"),
        "per": target_info.get("per"),
        "pbr": target_info.get("pbr"),
        "market_cap": target_info.get("market_cap"),
    }

    # 피어 종목 정보 수집
    peer_data = []
    for peer_ticker in peers:
        peer_info = get_naver_stock_info(peer_ticker)
        peer_name = get_ticker_name(peer_ticker)

        if peer_info:
            peer_data.append({
                "ticker": peer_ticker,
                "name": peer_name or peer_info.get("name"),
                "per": peer_info.get("per"),
                "pbr": peer_info.get("pbr"),
                "market_cap": peer_info.get("market_cap"),
            })

    # 섹터 평균 계산
    all_tickers = [ticker] + peers
    sector_avg = get_sector_average(all_tickers) if include_sector_avg else {}

    # 프리미엄/디스카운트 계산
    premium_discount = {}
    if sector_avg and target.get("per") and sector_avg.get("per"):
        premium_discount["per"] = round(
            (target["per"] - sector_avg["per"]) / sector_avg["per"] * 100, 1
        )
    if sector_avg and target.get("pbr") and sector_avg.get("pbr"):
        premium_discount["pbr"] = round(
            (target["pbr"] - sector_avg["pbr"]) / sector_avg["pbr"] * 100, 1
        )

    return {
        "target": target,
        "peers": peer_data,
        "sector_avg": sector_avg,
        "premium_discount": premium_discount,
    }


def get_sector_average(tickers: List[str]) -> dict:
    """
    종목 리스트의 평균 밸류에이션 계산

    Args:
        tickers: 종목코드 리스트

    Returns:
        {"per": 평균 PER, "pbr": 평균 PBR}
    """
    per_values = []
    pbr_values = []

    for ticker in tickers:
        info = get_naver_stock_info(ticker)
        if info:
            if info.get("per"):
                per_values.append(info["per"])
            if info.get("pbr"):
                pbr_values.append(info["pbr"])

    result = {}
    if per_values:
        result["per"] = round(sum(per_values) / len(per_values), 2)
    if pbr_values:
        result["pbr"] = round(sum(pbr_values) / len(pbr_values), 2)

    return result


def format_peer_table(comparison: dict) -> str:
    """
    피어 비교 결과를 마크다운 테이블로 포맷

    Args:
        comparison: get_peer_comparison() 결과

    Returns:
        마크다운 테이블 문자열
    """
    if not comparison:
        return "데이터 없음"

    lines = []
    lines.append("| 종목 | 시총 | PER | PBR |")
    lines.append("|------|------|-----|-----|")

    # 타겟
    t = comparison.get("target", {})
    lines.append(f"| **{t.get('name', '-')}** | {t.get('market_cap', '-')} | {t.get('per', '-')}x | {t.get('pbr', '-')}x |")

    # 피어
    for p in comparison.get("peers", []):
        lines.append(f"| {p.get('name', '-')} | {p.get('market_cap', '-')} | {p.get('per', '-')}x | {p.get('pbr', '-')}x |")

    # 섹터 평균
    avg = comparison.get("sector_avg", {})
    if avg:
        lines.append(f"| **섹터 평균** | - | **{avg.get('per', '-')}x** | **{avg.get('pbr', '-')}x** |")

    return "\n".join(lines)


if __name__ == "__main__":
    import json
    result = get_peer_comparison("377300", ["035420", "035720"])
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    print("\n" + format_peer_table(result))
```

**Step 2: Run test to verify it passes**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
python -m pytest tests/test_peer_comparison.py -v
```

Expected: PASS

**Step 3: Commit**

```bash
git add plugins/tier2-analyzer/utils/peer_comparison.py
git commit -m "feat: implement peer comparison for FI+"
```

---

### Task 6: FI+ 에이전트 마크다운 작성

**Files:**
- Create: `plugins/tier2-analyzer/agents/fi-plus.md`

**Step 1: Write agent definition**

```markdown
---
name: fi-plus
description: 분기 재무 + 동종업계 밸류에이션 비교. Tier 2 심층 재무 분석 에이전트.
model: sonnet
tools: [Bash, Read, Glob]
---

You are the **FI+ (Financial Intelligence Plus)** agent for Tier 2 deep analysis.

# Role

FI+ extends Tier 1 FI with:
1. **분기 재무 데이터** - 최근 8분기 손익
2. **피어 비교** - 동종업계 밸류에이션

---

# Execution

## Step 1: 분기 재무 수집

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer && python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/michael/public_agents/plugins/tier2-analyzer')

from utils.quarterly_scraper import get_fnguide_quarterly
import json

ticker = "{{TICKER}}"  # 종목코드
result = get_fnguide_quarterly(ticker)
print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
EOF
```

## Step 2: 피어 비교

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer && python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/michael/public_agents/plugins/tier2-analyzer')

from utils.peer_comparison import get_peer_comparison, format_peer_table

ticker = "{{TICKER}}"
peers = ["{{PEER1}}", "{{PEER2}}"]  # 비교 대상

result = get_peer_comparison(ticker, peers)
print(format_peer_table(result))
EOF
```

---

# Output Format

```markdown
## FI+ 분석: {종목명} ({티커})

### 1. 분기 재무 추이

| 분기 | 매출액 | 영업이익 | 순이익 | QoQ | YoY |
|------|--------|----------|--------|-----|-----|
| 2024Q4 | X,XXX | X,XXX | X,XXX | +X% | +X% |
| 2024Q3 | X,XXX | X,XXX | X,XXX | | |
| ... | | | | | |

### 2. 동종업계 비교

| 종목 | 시총 | PER | PBR |
|------|------|-----|-----|
| **카카오페이** | 6.7조 | 33.2x | 3.6x |
| 네이버 | 40조 | 28.5x | 2.8x |
| **섹터 평균** | - | **30.2x** | **3.1x** |

### 3. 밸류에이션 판단
- PER 프리미엄/디스카운트: +X% (섹터 대비)
- 판단: 고평가/적정/저평가
```
```

**Step 2: Commit**

```bash
git add plugins/tier2-analyzer/agents/fi-plus.md
git commit -m "feat: add FI+ agent definition"
```

---

### Task 7: FI+ utils __init__.py 업데이트

**Files:**
- Modify: `plugins/tier2-analyzer/utils/__init__.py`

**Step 1: Update exports**

```python
# plugins/tier2-analyzer/utils/__init__.py
"""Tier 2 Utils Package"""

from utils.quarterly_scraper import get_fnguide_quarterly
from utils.peer_comparison import (
    get_peer_comparison,
    get_sector_average,
    format_peer_table,
)

__all__ = [
    'get_fnguide_quarterly',
    'get_peer_comparison',
    'get_sector_average',
    'format_peer_table',
]
```

**Step 2: Commit**

```bash
git add plugins/tier2-analyzer/utils/__init__.py
git commit -m "feat: export FI+ utils functions"
```

---

## Phase 1 Complete Checklist

- [ ] Task 1: FnGuide 분기 테이블 구조 분석
- [ ] Task 2: 분기 재무 파싱 테스트 작성
- [ ] Task 3: 분기 재무 파싱 함수 구현
- [ ] Task 4: 피어 비교 테스트 작성
- [ ] Task 5: 피어 비교 함수 구현
- [ ] Task 6: FI+ 에이전트 마크다운 작성
- [ ] Task 7: utils __init__.py 업데이트

---

## Future Tasks (Phase 2)

- [ ] DART API 연동 (현금흐름)
- [ ] 컨센서스 데이터 파싱
- [ ] 섹터 자동 감지
