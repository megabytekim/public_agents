# MI+ (Management Intelligence Plus) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 경영진 평가(역량/주주친화성/지배구조) + DART 공시 분석 기능을 제공하는 MI+ 에이전트 구현

**Architecture:** OpenDART API로 사업보고서/공시 데이터 수집, 임원 현황/자사주/배당 이력 파싱, 워렌 버핏 스타일 경영진 스코어카드 생성. utils에 Python 함수 구현 후 에이전트 markdown 작성.

**Tech Stack:** Python 3.8+, requests, OpenDART API, BeautifulSoup4, pytest

---

## Phase 1: DART API 연동

### Task 1: OpenDART API 환경 설정

**Files:**
- Create: `plugins/tier2-analyzer/docs/dart-api-setup.md`
- Create: `tier2/.env.example`

**Step 1: DART API 키 확인**

OpenDART API 키 발급: https://opendart.fss.or.kr/

```bash
# .env.example
DART_API_KEY=your_api_key_here
```

**Step 2: API 구조 문서화**

```markdown
# DART API 구조

## Base URL
https://opendart.fss.or.kr/api/

## 주요 엔드포인트

| API | 설명 | 용도 |
|-----|------|------|
| /company.json | 기업 개황 | 기본 정보 |
| /fnlttSinglAcntAll.json | 재무제표 | 재무 데이터 |
| /exctvSttus.json | 임원 현황 | CEO 정보 |
| /tsstkAqTrsList.json | 자기주식 취득/처분 | 자사주 |
| /majorstock.json | 대주주 현황 | 지배구조 |
| /elestock.json | 임원 주식 변동 | 내부자 거래 |
| /alotMatter.json | 배당 관련 결정 | 배당 정책 |

## 공통 파라미터
- crtfc_key: API 키
- corp_code: 고유번호 (종목코드와 다름)
```

**Step 3: Commit**

```bash
git add plugins/tier2-analyzer/docs/dart-api-setup.md tier2/.env.example
git commit -m "docs: add DART API setup guide"
```

---

### Task 2: DART API 래퍼 테스트 작성

**Files:**
- Create: `plugins/tier2-analyzer/tests/test_dart_api.py`

**Step 1: Write the failing test**

```python
# plugins/tier2-analyzer/tests/test_dart_api.py
"""DART API 래퍼 테스트"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetCorpCode:
    """종목코드 → DART 고유번호 변환"""

    def test_returns_corp_code_for_valid_ticker(self):
        """유효한 티커에 대해 고유번호 반환"""
        from utils.dart_api import get_corp_code

        # 삼성전자 테스트
        result = get_corp_code("005930")

        assert result is not None
        assert len(result) == 8  # DART 고유번호는 8자리

    def test_returns_none_for_invalid_ticker(self):
        """잘못된 티커는 None 반환"""
        from utils.dart_api import get_corp_code

        result = get_corp_code("999999")

        assert result is None


class TestGetExecutiveStatus:
    """임원 현황 조회"""

    def test_returns_executive_list(self):
        """임원 리스트 반환"""
        from utils.dart_api import get_executive_status

        result = get_executive_status("005930")

        assert result is not None
        assert "executives" in result
        assert isinstance(result["executives"], list)

    def test_includes_ceo_info(self):
        """CEO 정보 포함 확인"""
        from utils.dart_api import get_executive_status

        result = get_executive_status("005930")

        assert result is not None
        # 대표이사 또는 사장 직위 확인
        executives = result.get("executives", [])
        ceo_found = any(
            "대표" in e.get("position", "") or "사장" in e.get("position", "")
            for e in executives
        )
        assert ceo_found


class TestGetTreasuryStock:
    """자사주 현황 조회"""

    def test_returns_treasury_stock_history(self):
        """자사주 취득/처분 이력 반환"""
        from utils.dart_api import get_treasury_stock

        result = get_treasury_stock("005930")

        assert result is not None
        assert "history" in result or "acquisitions" in result


class TestGetInsiderTrading:
    """내부자 거래 조회"""

    def test_returns_insider_trades(self):
        """임원 주식 변동 내역 반환"""
        from utils.dart_api import get_insider_trading

        result = get_insider_trading("005930")

        assert result is not None
        assert "trades" in result
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
python -m pytest tests/test_dart_api.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tier2.utils.dart_api'`

**Step 3: Commit failing test**

```bash
git add plugins/tier2-analyzer/tests/test_dart_api.py
git commit -m "test: add failing tests for DART API wrapper"
```

---

### Task 3: DART API 래퍼 구현

**Files:**
- Create: `plugins/tier2-analyzer/utils/dart_api.py`

**Step 1: Write minimal implementation**

```python
# plugins/tier2-analyzer/utils/dart_api.py
"""DART API 래퍼

OpenDART API를 통한 공시 데이터 수집
"""
import os
import time
import zipfile
import io
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict
from pathlib import Path
import requests

# API 키 로드
DART_API_KEY = os.environ.get("DART_API_KEY", "")
BASE_URL = "https://opendart.fss.or.kr/api"

# 종목코드 → 고유번호 매핑 캐시
_CORP_CODE_CACHE: Dict[str, str] = {}
_CORP_CODE_LOADED = False


def _load_corp_codes():
    """DART 고유번호 XML 다운로드 및 파싱"""
    global _CORP_CODE_CACHE, _CORP_CODE_LOADED

    if _CORP_CODE_LOADED:
        return

    # 캐시 파일 확인
    cache_dir = Path(__file__).parent / ".cache"
    cache_file = cache_dir / "corp_codes.xml"

    if cache_file.exists():
        # 캐시에서 로드
        tree = ET.parse(cache_file)
        root = tree.getroot()
        for corp in root.findall(".//list"):
            stock_code = corp.findtext("stock_code", "").strip()
            corp_code = corp.findtext("corp_code", "").strip()
            if stock_code and corp_code:
                _CORP_CODE_CACHE[stock_code] = corp_code
        _CORP_CODE_LOADED = True
        return

    # API에서 다운로드
    url = f"{BASE_URL}/corpCode.xml"
    params = {"crtfc_key": DART_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        # ZIP 파일 해제
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            xml_content = zf.read("CORPCODE.xml")

        # 캐시 저장
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "wb") as f:
            f.write(xml_content)

        # 파싱
        root = ET.fromstring(xml_content)
        for corp in root.findall(".//list"):
            stock_code = corp.findtext("stock_code", "").strip()
            corp_code = corp.findtext("corp_code", "").strip()
            if stock_code and corp_code:
                _CORP_CODE_CACHE[stock_code] = corp_code

        _CORP_CODE_LOADED = True

    except Exception as e:
        print(f"Warning: Failed to load corp codes: {e}")


def get_corp_code(ticker: str) -> Optional[str]:
    """
    종목코드를 DART 고유번호로 변환

    Args:
        ticker: 종목코드 (예: "005930")

    Returns:
        DART 고유번호 (8자리) 또는 None
    """
    _load_corp_codes()
    return _CORP_CODE_CACHE.get(ticker)


def get_executive_status(ticker: str, year: str = "2024") -> Optional[dict]:
    """
    임원 현황 조회

    Args:
        ticker: 종목코드
        year: 사업연도

    Returns:
        {
            "corp_name": "삼성전자",
            "executives": [
                {
                    "name": "홍길동",
                    "position": "대표이사",
                    "is_registered": True,
                    "tenure_start": "2020-03-01",
                    ...
                },
                ...
            ]
        }
    """
    corp_code = get_corp_code(ticker)
    if not corp_code:
        return None

    url = f"{BASE_URL}/exctvSttus.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bsns_year": year,
        "reprt_code": "11011",  # 사업보고서
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "000":
            # 이전 연도 시도
            params["bsns_year"] = str(int(year) - 1)
            response = requests.get(url, params=params, timeout=15)
            data = response.json()

        if data.get("status") != "000":
            return None

        executives = []
        for item in data.get("list", []):
            executives.append({
                "name": item.get("nm", ""),
                "gender": item.get("sexdstn", ""),
                "birth_year": item.get("birth_ym", "")[:4] if item.get("birth_ym") else "",
                "position": item.get("ofcps", ""),
                "is_registered": item.get("rgist_exctv_at", "N") == "Y",
                "is_fulltime": item.get("fte_at", "N") == "Y",
                "tenure_start": item.get("entconc_sttus", ""),
                "term_end": item.get("expire_date", ""),
            })

        return {
            "corp_name": data.get("list", [{}])[0].get("corp_name", "") if data.get("list") else "",
            "year": year,
            "executives": executives,
        }

    except Exception:
        return None


def get_treasury_stock(ticker: str) -> Optional[dict]:
    """
    자기주식 취득/처분 현황 조회

    Args:
        ticker: 종목코드

    Returns:
        {
            "acquisitions": [...],  # 취득 내역
            "disposals": [...],     # 처분 내역
            "summary": {...}        # 요약
        }
    """
    corp_code = get_corp_code(ticker)
    if not corp_code:
        return None

    url = f"{BASE_URL}/tsstkAqTrsList.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "000":
            return {"history": [], "summary": {}}

        history = []
        total_acquired = 0
        total_disposed = 0

        for item in data.get("list", []):
            entry = {
                "date": item.get("rcept_dt", ""),
                "type": item.get("ts_type", ""),
                "shares": int(item.get("aqd_trsr_stk_cnt", 0) or 0),
                "price": int(item.get("aqd_trsr_stk_prc", 0) or 0),
                "amount": int(item.get("aqd_trsr_stk_amt", 0) or 0),
                "method": item.get("aq_wtn_div", ""),
            }
            history.append(entry)

            if "취득" in item.get("ts_type", ""):
                total_acquired += entry["shares"]
            elif "처분" in item.get("ts_type", ""):
                total_disposed += entry["shares"]

        return {
            "history": history,
            "summary": {
                "total_acquired": total_acquired,
                "total_disposed": total_disposed,
                "net": total_acquired - total_disposed,
            },
        }

    except Exception:
        return None


def get_insider_trading(ticker: str, recent_months: int = 12) -> Optional[dict]:
    """
    임원 주식 변동 현황 조회

    Args:
        ticker: 종목코드
        recent_months: 조회 기간 (개월)

    Returns:
        {
            "trades": [
                {
                    "name": "홍길동",
                    "position": "대표이사",
                    "change_type": "매수",
                    "shares": 10000,
                    "date": "2024-01-15",
                    ...
                },
                ...
            ],
            "summary": {
                "net_buy": 50000,
                "net_sell": -20000,
            }
        }
    """
    corp_code = get_corp_code(ticker)
    if not corp_code:
        return None

    url = f"{BASE_URL}/elestock.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "000":
            return {"trades": [], "summary": {}}

        trades = []
        net_buy = 0
        net_sell = 0

        for item in data.get("list", []):
            change = int(item.get("sp_stock_chg_cnt", 0) or 0)
            trade = {
                "name": item.get("nm", ""),
                "position": item.get("ofcps", ""),
                "relation": item.get("rlt", ""),
                "date": item.get("rcept_dt", ""),
                "stock_type": item.get("sp_stock_knd", ""),
                "before_shares": int(item.get("bfr_sp_stock_cnt", 0) or 0),
                "after_shares": int(item.get("afr_sp_stock_cnt", 0) or 0),
                "change": change,
                "change_reason": item.get("sp_stock_chg_rsn", ""),
            }
            trades.append(trade)

            if change > 0:
                net_buy += change
            else:
                net_sell += abs(change)

        return {
            "trades": trades,
            "summary": {
                "net_buy": net_buy,
                "net_sell": net_sell,
                "net_change": net_buy - net_sell,
            },
        }

    except Exception:
        return None


def get_major_shareholders(ticker: str) -> Optional[dict]:
    """
    대주주 현황 조회

    Args:
        ticker: 종목코드

    Returns:
        {
            "shareholders": [...],
            "largest_shareholder_ratio": float,
        }
    """
    corp_code = get_corp_code(ticker)
    if not corp_code:
        return None

    url = f"{BASE_URL}/majorstock.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "000":
            return None

        shareholders = []
        max_ratio = 0.0

        for item in data.get("list", []):
            ratio = float(item.get("posesn_stock_co_rate", 0) or 0)
            shareholder = {
                "name": item.get("nm", ""),
                "relation": item.get("relate", ""),
                "shares": int(item.get("posesn_stock_co", 0) or 0),
                "ratio": ratio,
            }
            shareholders.append(shareholder)
            max_ratio = max(max_ratio, ratio)

        return {
            "shareholders": shareholders,
            "largest_shareholder_ratio": max_ratio,
        }

    except Exception:
        return None


if __name__ == "__main__":
    import json

    ticker = "005930"  # 삼성전자

    print("=== Corp Code ===")
    print(get_corp_code(ticker))

    print("\n=== Executives ===")
    print(json.dumps(get_executive_status(ticker), indent=2, ensure_ascii=False, default=str))

    print("\n=== Treasury Stock ===")
    print(json.dumps(get_treasury_stock(ticker), indent=2, ensure_ascii=False, default=str))

    print("\n=== Insider Trading ===")
    print(json.dumps(get_insider_trading(ticker), indent=2, ensure_ascii=False, default=str))
```

**Step 2: Run test to verify it passes**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
DART_API_KEY=your_key python -m pytest tests/test_dart_api.py -v
```

Expected: PASS (API 키 필요)

**Step 3: Commit**

```bash
git add plugins/tier2-analyzer/utils/dart_api.py
git commit -m "feat: implement DART API wrapper for MI+"
```

---

## Phase 2: 경영진 스코어카드

### Task 4: 경영진 스코어 테스트 작성

**Files:**
- Create: `plugins/tier2-analyzer/tests/test_management_score.py`

**Step 1: Write the failing test**

```python
# plugins/tier2-analyzer/tests/test_management_score.py
"""경영진 스코어카드 테스트"""
import pytest


class TestCalculateCompetenceScore:
    """A. 경영진 역량 점수 (30%)"""

    def test_returns_score_out_of_10(self):
        """10점 만점 점수 반환"""
        from utils.management_score import calculate_competence_score

        # 예시 데이터
        data = {
            "ceo_tenure_years": 5,
            "industry_experience_years": 15,
            "previous_success": True,
        }
        result = calculate_competence_score(data)

        assert result is not None
        assert 0 <= result["score"] <= 10
        assert "breakdown" in result


class TestCalculateShareholderFriendlinessScore:
    """B. 주주 친화성 점수 (40%)"""

    def test_returns_score_with_dividend_factor(self):
        """배당 요소 포함 점수 반환"""
        from utils.management_score import calculate_shareholder_friendliness_score

        data = {
            "treasury_stock_buyback": True,
            "treasury_stock_cancelled": True,
            "dividend_consistency_years": 10,
            "dividend_growth": True,
            "ceo_ownership_percent": 5.0,
        }
        result = calculate_shareholder_friendliness_score(data)

        assert result is not None
        assert 0 <= result["score"] <= 10


class TestCalculateGovernanceScore:
    """C. 지배구조 점수 (30%)"""

    def test_returns_governance_metrics(self):
        """지배구조 점수 반환"""
        from utils.management_score import calculate_governance_score

        data = {
            "largest_shareholder_ratio": 35.0,
            "independent_director_ratio": 0.5,
            "has_audit_committee": True,
            "related_party_issues": False,
        }
        result = calculate_governance_score(data)

        assert result is not None
        assert 0 <= result["score"] <= 10


class TestCalculateTotalManagementScore:
    """종합 경영진 점수"""

    def test_returns_weighted_total(self):
        """가중 평균 종합 점수 반환"""
        from utils.management_score import calculate_total_score

        scores = {
            "competence": 8.0,
            "shareholder_friendliness": 9.0,
            "governance": 7.0,
        }
        result = calculate_total_score(scores)

        # 가중치: A(30%) + B(40%) + C(30%)
        expected = 8.0 * 0.3 + 9.0 * 0.4 + 7.0 * 0.3
        assert result is not None
        assert abs(result["total"] - expected) < 0.01
        assert "grade" in result


class TestGetManagementGrade:
    """등급 판정"""

    def test_returns_correct_grade(self):
        """점수에 따른 등급 반환"""
        from utils.management_score import get_grade

        assert get_grade(9.5) == "A+"
        assert get_grade(8.5) == "A"
        assert get_grade(7.5) == "B+"
        assert get_grade(6.5) == "B"
        assert get_grade(5.5) == "C"
        assert get_grade(4.0) == "D"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
python -m pytest tests/test_management_score.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Commit failing test**

```bash
git add plugins/tier2-analyzer/tests/test_management_score.py
git commit -m "test: add failing tests for management scorecard"
```

---

### Task 5: 경영진 스코어 함수 구현

**Files:**
- Create: `plugins/tier2-analyzer/utils/management_score.py`

**Step 1: Write minimal implementation**

```python
# plugins/tier2-analyzer/utils/management_score.py
"""경영진 스코어카드

워렌 버핏 스타일 경영진 평가 시스템
- A. 경영진 역량 (30%)
- B. 주주 친화성 (40%)
- C. 지배구조 (30%)
"""
from typing import Optional


def calculate_competence_score(data: dict) -> dict:
    """
    A. 경영진 역량 점수 계산 (30%)

    Args:
        data: {
            "ceo_tenure_years": int,       # CEO 재임 기간
            "industry_experience_years": int,  # 업계 경험
            "previous_success": bool,      # 과거 성공 이력
            "education_relevance": float,  # 학력 적합성 (0-1)
            "key_decisions_success_rate": float,  # 주요 의사결정 성공률
        }

    Returns:
        {"score": float, "breakdown": dict}
    """
    score = 0.0
    breakdown = {}

    # CEO 재임 기간 (2점)
    tenure = data.get("ceo_tenure_years", 0)
    if tenure >= 5:
        tenure_score = 2.0
    elif tenure >= 3:
        tenure_score = 1.5
    elif tenure >= 1:
        tenure_score = 1.0
    else:
        tenure_score = 0.5
    score += tenure_score
    breakdown["tenure"] = tenure_score

    # 업계 경험 (2점)
    experience = data.get("industry_experience_years", 0)
    if experience >= 15:
        exp_score = 2.0
    elif experience >= 10:
        exp_score = 1.5
    elif experience >= 5:
        exp_score = 1.0
    else:
        exp_score = 0.5
    score += exp_score
    breakdown["experience"] = exp_score

    # 과거 성공 이력 (2점)
    if data.get("previous_success"):
        success_score = 2.0
    else:
        success_score = 1.0
    score += success_score
    breakdown["previous_success"] = success_score

    # 전문성/학력 (2점)
    relevance = data.get("education_relevance", 0.5)
    edu_score = relevance * 2.0
    score += edu_score
    breakdown["education"] = edu_score

    # 주요 의사결정 (2점)
    decision_rate = data.get("key_decisions_success_rate", 0.5)
    decision_score = decision_rate * 2.0
    score += decision_score
    breakdown["decisions"] = decision_score

    return {
        "score": round(min(score, 10.0), 1),
        "max_score": 10.0,
        "weight": 0.3,
        "breakdown": breakdown,
    }


def calculate_shareholder_friendliness_score(data: dict) -> dict:
    """
    B. 주주 친화성 점수 계산 (40%)

    Args:
        data: {
            "treasury_stock_buyback": bool,     # 자사주 매입
            "treasury_stock_cancelled": bool,   # 자사주 소각
            "dividend_consistency_years": int,  # 연속 배당 연수
            "dividend_growth": bool,            # 배당 성장
            "ceo_ownership_percent": float,     # CEO 지분율
            "stock_option_dilution": float,     # 스톡옵션 희석률
            "ir_transparency": float,           # IR 투명성 (0-1)
        }

    Returns:
        {"score": float, "breakdown": dict}
    """
    score = 0.0
    breakdown = {}

    # 자사주 매입 (1.5점)
    if data.get("treasury_stock_buyback"):
        buyback_score = 1.5
    else:
        buyback_score = 0.0
    score += buyback_score
    breakdown["buyback"] = buyback_score

    # 자사주 소각 (1.5점) - 버핏이 가장 좋아하는
    if data.get("treasury_stock_cancelled"):
        cancel_score = 1.5
    else:
        cancel_score = 0.0
    score += cancel_score
    breakdown["cancellation"] = cancel_score

    # 배당 일관성 (2점)
    div_years = data.get("dividend_consistency_years", 0)
    if div_years >= 10:
        div_score = 2.0
    elif div_years >= 5:
        div_score = 1.5
    elif div_years >= 3:
        div_score = 1.0
    else:
        div_score = 0.5
    score += div_score
    breakdown["dividend_consistency"] = div_score

    # 배당 성장 (1점)
    if data.get("dividend_growth"):
        growth_score = 1.0
    else:
        growth_score = 0.5
    score += growth_score
    breakdown["dividend_growth"] = growth_score

    # CEO 지분율 (2점) - 이해관계 일치
    ownership = data.get("ceo_ownership_percent", 0)
    if ownership >= 5:
        own_score = 2.0
    elif ownership >= 1:
        own_score = 1.5
    elif ownership > 0:
        own_score = 1.0
    else:
        own_score = 0.5
    score += own_score
    breakdown["ceo_ownership"] = own_score

    # 스톡옵션 희석 (1점) - 낮을수록 좋음
    dilution = data.get("stock_option_dilution", 0.05)
    if dilution < 0.01:
        dilution_score = 1.0
    elif dilution < 0.03:
        dilution_score = 0.7
    elif dilution < 0.05:
        dilution_score = 0.5
    else:
        dilution_score = 0.2
    score += dilution_score
    breakdown["dilution"] = dilution_score

    # IR 투명성 (1점)
    ir = data.get("ir_transparency", 0.5)
    ir_score = ir * 1.0
    score += ir_score
    breakdown["ir_transparency"] = ir_score

    return {
        "score": round(min(score, 10.0), 1),
        "max_score": 10.0,
        "weight": 0.4,
        "breakdown": breakdown,
    }


def calculate_governance_score(data: dict) -> dict:
    """
    C. 지배구조 점수 계산 (30%)

    Args:
        data: {
            "largest_shareholder_ratio": float,  # 대주주 지분율
            "independent_director_ratio": float, # 사외이사 비율
            "has_audit_committee": bool,         # 감사위원회 존재
            "related_party_issues": bool,        # 관계사 거래 이슈
            "owner_risk_level": int,             # 오너 리스크 (1-5)
            "regulatory_penalties": bool,        # 규제 제재 이력
        }

    Returns:
        {"score": float, "breakdown": dict}
    """
    score = 0.0
    breakdown = {}

    # 대주주 지분율 (2점) - 30-50%가 적정
    ratio = data.get("largest_shareholder_ratio", 0)
    if 30 <= ratio <= 50:
        ratio_score = 2.0  # 적정 범위
    elif 20 <= ratio < 30 or 50 < ratio <= 60:
        ratio_score = 1.5
    elif ratio < 20:
        ratio_score = 1.0  # 너무 분산
    else:
        ratio_score = 0.5  # 너무 집중
    score += ratio_score
    breakdown["shareholder_ratio"] = ratio_score

    # 사외이사 비율 (2점)
    ind_ratio = data.get("independent_director_ratio", 0)
    if ind_ratio >= 0.5:
        ind_score = 2.0
    elif ind_ratio >= 0.33:
        ind_score = 1.5
    else:
        ind_score = 1.0
    score += ind_score
    breakdown["independent_directors"] = ind_score

    # 감사위원회 (1.5점)
    if data.get("has_audit_committee"):
        audit_score = 1.5
    else:
        audit_score = 0.5
    score += audit_score
    breakdown["audit_committee"] = audit_score

    # 관계사 거래 이슈 (1.5점) - 없으면 좋음
    if not data.get("related_party_issues"):
        related_score = 1.5
    else:
        related_score = 0.0
    score += related_score
    breakdown["related_party"] = related_score

    # 오너 리스크 (2점) - 낮을수록 좋음
    risk_level = data.get("owner_risk_level", 3)
    if risk_level <= 1:
        risk_score = 2.0
    elif risk_level <= 2:
        risk_score = 1.5
    elif risk_level <= 3:
        risk_score = 1.0
    else:
        risk_score = 0.5
    score += risk_score
    breakdown["owner_risk"] = risk_score

    # 규제 제재 (1점) - 없으면 좋음
    if not data.get("regulatory_penalties"):
        reg_score = 1.0
    else:
        reg_score = 0.0
    score += reg_score
    breakdown["regulatory"] = reg_score

    return {
        "score": round(min(score, 10.0), 1),
        "max_score": 10.0,
        "weight": 0.3,
        "breakdown": breakdown,
    }


def calculate_total_score(scores: dict) -> dict:
    """
    종합 경영진 점수 계산

    Args:
        scores: {
            "competence": float,              # A 점수
            "shareholder_friendliness": float, # B 점수
            "governance": float,              # C 점수
        }

    Returns:
        {
            "total": float,
            "weighted_scores": dict,
            "grade": str,
        }
    """
    weights = {
        "competence": 0.3,
        "shareholder_friendliness": 0.4,
        "governance": 0.3,
    }

    weighted_scores = {}
    total = 0.0

    for key, weight in weights.items():
        raw_score = scores.get(key, 0)
        weighted = raw_score * weight
        weighted_scores[key] = round(weighted, 2)
        total += weighted

    total = round(total, 1)
    grade = get_grade(total)

    return {
        "total": total,
        "max_total": 10.0,
        "weighted_scores": weighted_scores,
        "grade": grade,
        "interpretation": _get_interpretation(grade),
    }


def get_grade(score: float) -> str:
    """
    점수를 등급으로 변환

    Args:
        score: 0-10 사이의 점수

    Returns:
        등급 문자열 (A+, A, B+, B, C, D)
    """
    if score >= 9:
        return "A+"
    elif score >= 8:
        return "A"
    elif score >= 7:
        return "B+"
    elif score >= 6:
        return "B"
    elif score >= 5:
        return "C"
    else:
        return "D"


def _get_interpretation(grade: str) -> str:
    """등급 해석"""
    interpretations = {
        "A+": "버핏이 좋아할 경영진 - 장기 투자 매력적",
        "A": "우수한 경영진 - 안심하고 투자 가능",
        "B+": "양호한 경영진 - 모니터링 필요",
        "B": "보통 경영진 - 주의 필요",
        "C": "우려되는 경영진 - 투자 신중",
        "D": "문제 있는 경영진 - 투자 회피 권고",
    }
    return interpretations.get(grade, "")


def format_scorecard(
    competence: dict,
    shareholder: dict,
    governance: dict,
    total: dict,
) -> str:
    """
    스코어카드를 마크다운 테이블로 포맷

    Returns:
        마크다운 문자열
    """
    lines = []

    lines.append("## Management Intelligence Score")
    lines.append("")
    lines.append(f"**종합 등급: {total['grade']}** ({total['total']}/10)")
    lines.append(f"> {total['interpretation']}")
    lines.append("")

    # 요약 테이블
    lines.append("| 영역 | 가중치 | 점수 | 가중 점수 |")
    lines.append("|------|--------|------|----------|")
    lines.append(f"| A. 경영진 역량 | 30% | {competence['score']}/10 | {total['weighted_scores']['competence']} |")
    lines.append(f"| B. 주주 친화성 | 40% | {shareholder['score']}/10 | {total['weighted_scores']['shareholder_friendliness']} |")
    lines.append(f"| C. 지배구조 | 30% | {governance['score']}/10 | {total['weighted_scores']['governance']} |")
    lines.append(f"| **종합** | 100% | - | **{total['total']}/10** |")
    lines.append("")

    # 상세 분석
    lines.append("### A. 경영진 역량 상세")
    for key, value in competence.get("breakdown", {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("### B. 주주 친화성 상세")
    for key, value in shareholder.get("breakdown", {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("### C. 지배구조 상세")
    for key, value in governance.get("breakdown", {}).items():
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)


if __name__ == "__main__":
    # 예시 데이터로 테스트
    competence_data = {
        "ceo_tenure_years": 5,
        "industry_experience_years": 15,
        "previous_success": True,
        "education_relevance": 0.8,
        "key_decisions_success_rate": 0.7,
    }

    shareholder_data = {
        "treasury_stock_buyback": True,
        "treasury_stock_cancelled": True,
        "dividend_consistency_years": 10,
        "dividend_growth": True,
        "ceo_ownership_percent": 3.0,
        "stock_option_dilution": 0.02,
        "ir_transparency": 0.8,
    }

    governance_data = {
        "largest_shareholder_ratio": 35.0,
        "independent_director_ratio": 0.5,
        "has_audit_committee": True,
        "related_party_issues": False,
        "owner_risk_level": 2,
        "regulatory_penalties": False,
    }

    comp = calculate_competence_score(competence_data)
    shar = calculate_shareholder_friendliness_score(shareholder_data)
    gov = calculate_governance_score(governance_data)

    scores = {
        "competence": comp["score"],
        "shareholder_friendliness": shar["score"],
        "governance": gov["score"],
    }
    total = calculate_total_score(scores)

    print(format_scorecard(comp, shar, gov, total))
```

**Step 2: Run test to verify it passes**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
python -m pytest tests/test_management_score.py -v
```

Expected: PASS

**Step 3: Commit**

```bash
git add plugins/tier2-analyzer/utils/management_score.py
git commit -m "feat: implement management scorecard for MI+"
```

---

### Task 6: MI+ 데이터 수집기 구현

**Files:**
- Create: `plugins/tier2-analyzer/utils/mi_collector.py`

**Step 1: Write data collector that integrates DART API and scoring**

```python
# plugins/tier2-analyzer/utils/mi_collector.py
"""MI+ 데이터 수집기

DART API와 경영진 스코어카드를 통합하여
종목에 대한 경영진 분석 데이터 수집
"""
from typing import Optional
from utils.dart_api import (
    get_executive_status,
    get_treasury_stock,
    get_insider_trading,
    get_major_shareholders,
)
from utils.management_score import (
    calculate_competence_score,
    calculate_shareholder_friendliness_score,
    calculate_governance_score,
    calculate_total_score,
    format_scorecard,
)


def collect_management_data(ticker: str) -> Optional[dict]:
    """
    종목에 대한 경영진 관련 데이터 수집

    Args:
        ticker: 종목코드

    Returns:
        {
            "executives": {...},
            "treasury_stock": {...},
            "insider_trading": {...},
            "major_shareholders": {...},
        }
    """
    return {
        "executives": get_executive_status(ticker),
        "treasury_stock": get_treasury_stock(ticker),
        "insider_trading": get_insider_trading(ticker),
        "major_shareholders": get_major_shareholders(ticker),
    }


def analyze_management(ticker: str, supplementary_data: Optional[dict] = None) -> Optional[dict]:
    """
    경영진 종합 분석 수행

    Args:
        ticker: 종목코드
        supplementary_data: 추가 데이터 (뉴스, IR 등에서 수집한 정성적 데이터)

    Returns:
        {
            "data": {...},           # 수집된 원시 데이터
            "scores": {...},         # 각 영역별 점수
            "total": {...},          # 종합 점수
            "scorecard_md": str,     # 마크다운 스코어카드
        }
    """
    # 데이터 수집
    data = collect_management_data(ticker)
    if not data:
        return None

    supp = supplementary_data or {}

    # A. 경영진 역량 데이터 준비
    executives = data.get("executives") or {}
    exec_list = executives.get("executives", [])

    # CEO 찾기
    ceo = next(
        (e for e in exec_list if "대표" in e.get("position", "") or "사장" in e.get("position", "")),
        {}
    )

    # CEO 재임 기간 추정 (데이터가 있으면)
    tenure_years = supp.get("ceo_tenure_years", 3)  # 기본값

    competence_data = {
        "ceo_tenure_years": tenure_years,
        "industry_experience_years": supp.get("industry_experience_years", 10),
        "previous_success": supp.get("previous_success", True),
        "education_relevance": supp.get("education_relevance", 0.7),
        "key_decisions_success_rate": supp.get("key_decisions_success_rate", 0.6),
    }

    # B. 주주 친화성 데이터 준비
    treasury = data.get("treasury_stock") or {}
    treasury_summary = treasury.get("summary", {})

    has_buyback = treasury_summary.get("total_acquired", 0) > 0
    # 소각 여부는 추가 데이터 필요 (DART에서 직접 확인 어려움)
    has_cancellation = supp.get("treasury_stock_cancelled", False)

    shareholder_data = {
        "treasury_stock_buyback": has_buyback,
        "treasury_stock_cancelled": has_cancellation,
        "dividend_consistency_years": supp.get("dividend_consistency_years", 5),
        "dividend_growth": supp.get("dividend_growth", True),
        "ceo_ownership_percent": supp.get("ceo_ownership_percent", 1.0),
        "stock_option_dilution": supp.get("stock_option_dilution", 0.03),
        "ir_transparency": supp.get("ir_transparency", 0.7),
    }

    # C. 지배구조 데이터 준비
    major = data.get("major_shareholders") or {}
    largest_ratio = major.get("largest_shareholder_ratio", 30)

    # 사외이사 비율 계산
    total_directors = len(exec_list)
    independent_count = len([
        e for e in exec_list
        if "사외" in e.get("position", "") or "독립" in e.get("position", "")
    ])
    independent_ratio = independent_count / total_directors if total_directors > 0 else 0.33

    governance_data = {
        "largest_shareholder_ratio": largest_ratio,
        "independent_director_ratio": independent_ratio,
        "has_audit_committee": supp.get("has_audit_committee", True),
        "related_party_issues": supp.get("related_party_issues", False),
        "owner_risk_level": supp.get("owner_risk_level", 3),
        "regulatory_penalties": supp.get("regulatory_penalties", False),
    }

    # 점수 계산
    comp = calculate_competence_score(competence_data)
    shar = calculate_shareholder_friendliness_score(shareholder_data)
    gov = calculate_governance_score(governance_data)

    scores = {
        "competence": comp["score"],
        "shareholder_friendliness": shar["score"],
        "governance": gov["score"],
    }
    total = calculate_total_score(scores)

    # 스코어카드 생성
    scorecard_md = format_scorecard(comp, shar, gov, total)

    return {
        "ticker": ticker,
        "data": data,
        "scores": {
            "competence": comp,
            "shareholder_friendliness": shar,
            "governance": gov,
        },
        "total": total,
        "scorecard_md": scorecard_md,
    }


if __name__ == "__main__":
    result = analyze_management("005930")
    if result:
        print(result["scorecard_md"])
```

**Step 2: Commit**

```bash
git add plugins/tier2-analyzer/utils/mi_collector.py
git commit -m "feat: implement MI+ data collector integrating DART and scoring"
```

---

### Task 7: MI+ 에이전트 마크다운 작성

**Files:**
- Create: `plugins/tier2-analyzer/agents/mi-plus.md`

**Step 1: Write agent definition**

```markdown
---
name: mi-plus
description: 경영진 평가 + DART 공시 분석. Tier 2 심층 경영진 분석 에이전트.
model: sonnet
tools: [Bash, Read, Glob, WebSearch]
---

You are the **MI+ (Management Intelligence Plus)** agent for Tier 2 deep analysis.

# Role

MI+ extends Tier 1 MI with:
1. **경영진 평가** - 워렌 버핏 스타일 스코어카드
2. **DART 공시 분석** - 사업보고서, 내부자 거래

---

# Execution

## Step 1: DART 데이터 수집 및 경영진 분석

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer && python3 << 'EOF'
import sys
import os
sys.path.insert(0, '/Users/michael/public_agents/plugins/tier2-analyzer')

# DART API 키 설정 (환경변수에서)
os.environ.setdefault("DART_API_KEY", "your_key")

from utils.mi_collector import analyze_management
import json

ticker = "{{TICKER}}"
result = analyze_management(ticker)

if result:
    print(result["scorecard_md"])
    print("\n\n### 원시 데이터")
    print(json.dumps(result["data"], indent=2, ensure_ascii=False, default=str))
else:
    print("데이터 수집 실패")
EOF
```

## Step 2: 보완 데이터 수집 (WebSearch)

수집해야 할 추가 정보:
- CEO 이력 및 경력 (뉴스, 인터뷰)
- 과거 주요 의사결정 결과 (M&A, 사업 확장)
- 규제 이슈, 소송 이력
- IR 자료 품질

WebSearch 쿼리 예시:
- "{회사명} CEO 인터뷰 2024"
- "{회사명} 대주주 오너리스크"
- "{회사명} 규제 과징금"

## Step 3: 보완 데이터로 스코어 재계산

정성적 데이터를 반영하여 supplementary_data 업데이트:

```python
supplementary_data = {
    "ceo_tenure_years": X,          # 조사 결과
    "industry_experience_years": X, # 조사 결과
    "previous_success": True/False,
    "treasury_stock_cancelled": True/False,
    "dividend_consistency_years": X,
    "has_audit_committee": True,
    "related_party_issues": True/False,
    "owner_risk_level": 1-5,        # 조사 결과
    "regulatory_penalties": True/False,
}
```

---

# Output Format

```markdown
## MI+ 분석: {종목명} ({티커})

### Management Intelligence Score

**종합 등급: A** (8.2/10)
> 우수한 경영진 - 안심하고 투자 가능

| 영역 | 가중치 | 점수 | 가중 점수 |
|------|--------|------|----------|
| A. 경영진 역량 | 30% | 8.0/10 | 2.4 |
| B. 주주 친화성 | 40% | 9.0/10 | 3.6 |
| C. 지배구조 | 30% | 7.0/10 | 2.1 |
| **종합** | 100% | - | **8.1/10** |

### A. 경영진 역량 (8.0/10)
- CEO: 홍길동 (재임 5년, 업계 경력 15년)
- 주요 성과: ...
- 리스크: ...

### B. 주주 친화성 (9.0/10)
- 자사주: 최근 3년 1,000억원 매입
- 배당: 연속 10년 배당, DPS 성장 중
- CEO 지분: 3.5%

### C. 지배구조 (7.0/10)
- 대주주 지분: 35% (적정)
- 사외이사: 50%
- 관계사 거래: 이슈 없음

### DART 공시 요약
- 최근 내부자 거래: CEO +10,000주 매수 (긍정)
- 주요 공시: ...
```
```

**Step 2: Commit**

```bash
git add plugins/tier2-analyzer/agents/mi-plus.md
git commit -m "feat: add MI+ agent definition"
```

---

### Task 8: MI+ utils 업데이트

**Files:**
- Modify: `plugins/tier2-analyzer/utils/__init__.py`

**Step 1: Update exports**

```python
# plugins/tier2-analyzer/utils/__init__.py
"""Tier 2 Utils Package"""

# FI+ exports
from utils.quarterly_scraper import get_fnguide_quarterly
from utils.peer_comparison import (
    get_peer_comparison,
    get_sector_average,
    format_peer_table,
)

# MI+ exports
from utils.dart_api import (
    get_corp_code,
    get_executive_status,
    get_treasury_stock,
    get_insider_trading,
    get_major_shareholders,
)
from utils.management_score import (
    calculate_competence_score,
    calculate_shareholder_friendliness_score,
    calculate_governance_score,
    calculate_total_score,
    get_grade,
    format_scorecard,
)
from utils.mi_collector import (
    collect_management_data,
    analyze_management,
)

__all__ = [
    # FI+
    'get_fnguide_quarterly',
    'get_peer_comparison',
    'get_sector_average',
    'format_peer_table',
    # MI+ DART
    'get_corp_code',
    'get_executive_status',
    'get_treasury_stock',
    'get_insider_trading',
    'get_major_shareholders',
    # MI+ Score
    'calculate_competence_score',
    'calculate_shareholder_friendliness_score',
    'calculate_governance_score',
    'calculate_total_score',
    'get_grade',
    'format_scorecard',
    # MI+ Collector
    'collect_management_data',
    'analyze_management',
]
```

**Step 2: Commit**

```bash
git add plugins/tier2-analyzer/utils/__init__.py
git commit -m "feat: export MI+ utils functions"
```

---

## Phase 2 Complete Checklist

- [ ] Task 1: OpenDART API 환경 설정
- [ ] Task 2: DART API 래퍼 테스트 작성
- [ ] Task 3: DART API 래퍼 구현
- [ ] Task 4: 경영진 스코어 테스트 작성
- [ ] Task 5: 경영진 스코어 함수 구현
- [ ] Task 6: MI+ 데이터 수집기 구현
- [ ] Task 7: MI+ 에이전트 마크다운 작성
- [ ] Task 8: MI+ utils 업데이트

---

## Future Tasks (Phase 3)

- [ ] DART 사업보고서 본문 파싱 (PDF/XML)
- [ ] 법원 소송 검색 연동
- [ ] ESG 평가 연동
- [ ] 관계사 거래 상세 분석
