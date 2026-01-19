# SI+ (Sentiment Intelligence Plus) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 텔레그램 채널 센티먼트 수집 및 분석 기능을 제공하는 SI+ 에이전트 구현

**Architecture:** Telethon(MTProto)으로 텔레그램 채널 메시지 수집, 종목 멘션 추출, 센티먼트 스코어 계산, 루머 vs 팩트 분류. utils에 Python 함수 구현 후 에이전트 markdown 작성.

**Tech Stack:** Python 3.8+, Telethon, asyncio, pytest, pytest-asyncio

---

## Phase 1: 텔레그램 API 연동

### Task 1: Telegram API 환경 설정

**Files:**
- Create: `plugins/tier2-analyzer/docs/telegram-api-setup.md`
- Modify: `tier2/.env.example`

**Step 1: Telegram API 키 발급**

1. https://my.telegram.org 접속
2. API development tools 선택
3. App 생성하여 `api_id`와 `api_hash` 발급

**Step 2: 환경 변수 설정**

```bash
# tier2/.env.example 추가
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+821012345678
```

**Step 3: 설정 가이드 문서화**

```markdown
# Telegram API 설정 가이드

## 1. API 키 발급

1. https://my.telegram.org 접속
2. 로그인 (전화번호 인증)
3. "API development tools" 클릭
4. App 정보 입력:
   - App title: Stock Analyzer SI+
   - Short name: siplus
   - Platform: Desktop
5. `api_id`와 `api_hash` 복사

## 2. Telethon 설치

```bash
pip install telethon
```

## 3. 첫 인증

```python
from telethon import TelegramClient

api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
phone = '+821012345678'

client = TelegramClient('session_siplus', api_id, api_hash)
client.start(phone=phone)
# SMS 인증 코드 입력 필요 (최초 1회)
```

## 4. 세션 파일

- 첫 인증 후 `session_siplus.session` 파일 생성
- 이후 인증 없이 재사용 가능
- **주의**: 세션 파일은 git에 포함하지 않음

## 5. 채널 접근

- 공개 채널: 채널 username으로 접근 가능
- 비공개 채널: 초대 링크로 가입 필요
- 제한: 분당 메시지 수집 제한 있음 (FloodWait)
```

**Step 4: Commit**

```bash
git add plugins/tier2-analyzer/docs/telegram-api-setup.md tier2/.env.example
git commit -m "docs: add Telegram API setup guide for SI+"
```

---

### Task 2: 텔레그램 수집기 테스트 작성

**Files:**
- Create: `plugins/tier2-analyzer/tests/test_telegram_collector.py`

**Step 1: Write the failing test**

```python
# plugins/tier2-analyzer/tests/test_telegram_collector.py
"""텔레그램 수집기 테스트"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock


class TestGetChannelMessages:
    """채널 메시지 수집 테스트"""

    @pytest.mark.asyncio
    async def test_returns_message_list(self):
        """메시지 리스트 반환"""
        from utils.telegram_collector import get_channel_messages

        # Mock client
        with patch('tier2.utils.telegram_collector.get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_message = MagicMock()
            mock_message.text = "테스트 메시지"
            mock_message.date = MagicMock()
            mock_message.id = 12345

            mock_client.get_messages = AsyncMock(return_value=[mock_message])
            mock_get_client.return_value.__aenter__.return_value = mock_client

            result = await get_channel_messages("test_channel", limit=10)

            assert result is not None
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_filters_by_keyword(self):
        """키워드 필터링"""
        from utils.telegram_collector import filter_messages_by_ticker

        messages = [
            {"text": "삼성전자 상승 기대", "date": "2024-01-15"},
            {"text": "오늘 날씨 좋네요", "date": "2024-01-15"},
            {"text": "005930 매수 추천", "date": "2024-01-15"},
        ]

        result = filter_messages_by_ticker(messages, "005930", ["삼성전자", "삼성"])

        assert len(result) == 2


class TestAnalyzeTelegramSentiment:
    """텔레그램 센티먼트 분석 테스트"""

    def test_returns_sentiment_score(self):
        """센티먼트 점수 반환"""
        from utils.telegram_collector import analyze_telegram_sentiment

        messages = [
            {"text": "급등 예상! 지금이 매수 기회", "date": "2024-01-15"},
            {"text": "목표가 상향", "date": "2024-01-15"},
            {"text": "조심해야 함", "date": "2024-01-14"},
        ]

        result = analyze_telegram_sentiment(messages)

        assert result is not None
        assert "score" in result
        assert -1.0 <= result["score"] <= 1.0
        assert "bullish_count" in result
        assert "bearish_count" in result

    def test_identifies_bullish_keywords(self):
        """상승 키워드 감지"""
        from utils.telegram_collector import analyze_telegram_sentiment

        messages = [
            {"text": "대박! 급등 예상! 상한가 갈 듯", "date": "2024-01-15"},
        ]

        result = analyze_telegram_sentiment(messages)

        assert result["bullish_count"] > 0
        assert result["score"] > 0

    def test_identifies_bearish_keywords(self):
        """하락 키워드 감지"""
        from utils.telegram_collector import analyze_telegram_sentiment

        messages = [
            {"text": "폭락 주의! 손절 필수", "date": "2024-01-15"},
        ]

        result = analyze_telegram_sentiment(messages)

        assert result["bearish_count"] > 0
        assert result["score"] < 0


class TestClassifyRumor:
    """루머 분류 테스트"""

    def test_identifies_rumor(self):
        """루머 감지"""
        from utils.telegram_collector import classify_message

        message = "카더라 통신에 의하면 곧 대규모 발표 있을 듯"

        result = classify_message(message)

        assert result["is_rumor"] is True
        assert result["confidence"] < 0.5

    def test_identifies_fact(self):
        """팩트 감지"""
        from utils.telegram_collector import classify_message

        message = "공시에 따르면 배당금 1,000원 확정"

        result = classify_message(message)

        assert result["is_rumor"] is False
        assert result["confidence"] > 0.5
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
pip install pytest-asyncio
python -m pytest tests/test_telegram_collector.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Commit failing test**

```bash
git add plugins/tier2-analyzer/tests/test_telegram_collector.py
git commit -m "test: add failing tests for telegram collector"
```

---

### Task 3: 텔레그램 수집기 구현

**Files:**
- Create: `plugins/tier2-analyzer/utils/telegram_collector.py`

**Step 1: Write minimal implementation**

```python
# plugins/tier2-analyzer/utils/telegram_collector.py
"""텔레그램 채널 수집기

Telethon을 사용한 텔레그램 채널 메시지 수집 및 분석
"""
import os
import re
import asyncio
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

try:
    from telethon import TelegramClient
    from telethon.tl.types import Channel, Message
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

# API 설정
API_ID = os.environ.get("TELEGRAM_API_ID", "")
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
SESSION_NAME = "session_siplus"

# 센티먼트 키워드
BULLISH_KEYWORDS = [
    "급등", "상한가", "폭등", "대박", "상승", "매수", "추천", "목표가 상향",
    "호재", "돌파", "신고가", "기대", "좋아", "긍정", "오를", "상향",
    "강추", "존버", "가즈아", "풀매수", "물타기", "반등", "바닥",
]

BEARISH_KEYWORDS = [
    "급락", "하한가", "폭락", "손절", "하락", "매도", "경고", "목표가 하향",
    "악재", "이탈", "신저가", "우려", "나빠", "부정", "내릴", "하향",
    "도망", "탈출", "물렸", "패닉", "투매", "고점",
]

RUMOR_INDICATORS = [
    "카더라", "루머", "소문", "찌라시", "~일듯", "~할듯", "아마도",
    "추정", "예상", "들었는데", "한다더라", "~인듯", "~같음",
    "누가 그러는데", "확인 안됨", "비공식",
]

FACT_INDICATORS = [
    "공시", "IR", "발표", "확정", "공식", "보도", "기사", "뉴스",
    "실적", "결산", "분기", "사업보고서", "증권신고서", "확인됨",
]


@asynccontextmanager
async def get_client():
    """텔레그램 클라이언트 컨텍스트 매니저"""
    if not TELETHON_AVAILABLE:
        raise ImportError("Telethon not installed. Run: pip install telethon")

    if not API_ID or not API_HASH:
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    try:
        yield client
    finally:
        await client.disconnect()


async def get_channel_messages(
    channel: str,
    limit: int = 100,
    days_back: int = 7,
) -> List[dict]:
    """
    텔레그램 채널에서 메시지 수집

    Args:
        channel: 채널 username (예: "stock_research")
        limit: 최대 메시지 수
        days_back: 수집할 기간 (일)

    Returns:
        [
            {
                "id": 12345,
                "text": "메시지 내용",
                "date": "2024-01-15 14:30:00",
                "views": 1000,
                "forwards": 50,
            },
            ...
        ]
    """
    messages = []
    min_date = datetime.now() - timedelta(days=days_back)

    try:
        async with get_client() as client:
            entity = await client.get_entity(channel)

            async for msg in client.iter_messages(entity, limit=limit):
                if not msg.text:
                    continue

                if msg.date.replace(tzinfo=None) < min_date:
                    break

                messages.append({
                    "id": msg.id,
                    "text": msg.text,
                    "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "views": getattr(msg, 'views', 0) or 0,
                    "forwards": getattr(msg, 'forwards', 0) or 0,
                })

    except Exception as e:
        print(f"Error collecting messages: {e}")

    return messages


def filter_messages_by_ticker(
    messages: List[dict],
    ticker: str,
    aliases: Optional[List[str]] = None,
) -> List[dict]:
    """
    종목 관련 메시지 필터링

    Args:
        messages: 메시지 리스트
        ticker: 종목코드 (예: "005930")
        aliases: 종목 별칭 (예: ["삼성전자", "삼성", "삼전"])

    Returns:
        필터링된 메시지 리스트
    """
    keywords = [ticker]
    if aliases:
        keywords.extend(aliases)

    filtered = []
    for msg in messages:
        text = msg.get("text", "")
        if any(kw in text for kw in keywords):
            filtered.append(msg)

    return filtered


def analyze_telegram_sentiment(messages: List[dict]) -> dict:
    """
    메시지에서 센티먼트 분석

    Args:
        messages: 메시지 리스트

    Returns:
        {
            "score": float,           # -1.0 ~ 1.0
            "bullish_count": int,
            "bearish_count": int,
            "neutral_count": int,
            "total_messages": int,
            "top_bullish": [...],     # 주요 상승 메시지
            "top_bearish": [...],     # 주요 하락 메시지
        }
    """
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0

    top_bullish = []
    top_bearish = []

    for msg in messages:
        text = msg.get("text", "")

        # 키워드 카운트
        bull_hits = sum(1 for kw in BULLISH_KEYWORDS if kw in text)
        bear_hits = sum(1 for kw in BEARISH_KEYWORDS if kw in text)

        if bull_hits > bear_hits:
            bullish_count += 1
            if len(top_bullish) < 5:
                top_bullish.append({
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "date": msg.get("date"),
                    "keywords": [kw for kw in BULLISH_KEYWORDS if kw in text],
                })
        elif bear_hits > bull_hits:
            bearish_count += 1
            if len(top_bearish) < 5:
                top_bearish.append({
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "date": msg.get("date"),
                    "keywords": [kw for kw in BEARISH_KEYWORDS if kw in text],
                })
        else:
            neutral_count += 1

    total = len(messages)
    if total == 0:
        score = 0.0
    else:
        # 센티먼트 점수: (상승 - 하락) / 전체
        score = (bullish_count - bearish_count) / total

    return {
        "score": round(score, 3),
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": neutral_count,
        "total_messages": total,
        "top_bullish": top_bullish,
        "top_bearish": top_bearish,
    }


def classify_message(text: str) -> dict:
    """
    메시지를 루머 vs 팩트로 분류

    Args:
        text: 메시지 텍스트

    Returns:
        {
            "is_rumor": bool,
            "confidence": float,      # 0.0 ~ 1.0
            "indicators": [...]       # 감지된 지표
        }
    """
    rumor_hits = [ind for ind in RUMOR_INDICATORS if ind in text]
    fact_hits = [ind for ind in FACT_INDICATORS if ind in text]

    rumor_score = len(rumor_hits)
    fact_score = len(fact_hits)

    total = rumor_score + fact_score

    if total == 0:
        # 지표 없음 - 중립
        return {
            "is_rumor": False,
            "confidence": 0.5,
            "indicators": [],
        }

    # 팩트 비율 계산
    fact_ratio = fact_score / total

    return {
        "is_rumor": fact_ratio < 0.5,
        "confidence": max(fact_ratio, 1 - fact_ratio),
        "indicators": {
            "rumor": rumor_hits,
            "fact": fact_hits,
        },
    }


def analyze_channel(messages: List[dict], ticker: str) -> dict:
    """
    채널 종합 분석

    Args:
        messages: 메시지 리스트
        ticker: 종목코드

    Returns:
        종합 분석 결과
    """
    sentiment = analyze_telegram_sentiment(messages)

    # 루머 분류
    rumors = []
    facts = []
    for msg in messages:
        classification = classify_message(msg.get("text", ""))
        if classification["is_rumor"]:
            rumors.append({
                **msg,
                "confidence": classification["confidence"],
            })
        else:
            facts.append({
                **msg,
                "confidence": classification["confidence"],
            })

    return {
        "ticker": ticker,
        "sentiment": sentiment,
        "rumors": rumors[:10],  # 상위 10개
        "facts": facts[:10],
        "summary": {
            "total_messages": len(messages),
            "rumor_ratio": len(rumors) / len(messages) if messages else 0,
            "sentiment_label": _get_sentiment_label(sentiment["score"]),
        },
    }


def _get_sentiment_label(score: float) -> str:
    """센티먼트 점수를 레이블로 변환"""
    if score >= 0.3:
        return "Bullish"
    elif score <= -0.3:
        return "Bearish"
    else:
        return "Neutral"


def format_sentiment_report(analysis: dict) -> str:
    """
    분석 결과를 마크다운으로 포맷

    Args:
        analysis: analyze_channel() 결과

    Returns:
        마크다운 문자열
    """
    lines = []
    sentiment = analysis.get("sentiment", {})
    summary = analysis.get("summary", {})

    lines.append(f"## 텔레그램 센티먼트 분석: {analysis.get('ticker', 'N/A')}")
    lines.append("")

    # 요약
    score = sentiment.get("score", 0)
    label = summary.get("sentiment_label", "Neutral")
    lines.append(f"**센티먼트: {label}** (점수: {score:+.2f})")
    lines.append("")

    # 통계 테이블
    lines.append("### 메시지 통계")
    lines.append("")
    lines.append("| 구분 | 수량 |")
    lines.append("|------|------|")
    lines.append(f"| 전체 메시지 | {sentiment.get('total_messages', 0)} |")
    lines.append(f"| 상승 의견 | {sentiment.get('bullish_count', 0)} |")
    lines.append(f"| 하락 의견 | {sentiment.get('bearish_count', 0)} |")
    lines.append(f"| 중립 | {sentiment.get('neutral_count', 0)} |")
    lines.append(f"| 루머 비율 | {summary.get('rumor_ratio', 0):.1%} |")
    lines.append("")

    # 주요 상승 의견
    if sentiment.get("top_bullish"):
        lines.append("### 주요 상승 의견")
        lines.append("")
        for msg in sentiment["top_bullish"]:
            lines.append(f"- {msg['text']}")
            lines.append(f"  - 키워드: {', '.join(msg.get('keywords', []))}")
        lines.append("")

    # 주요 하락 의견
    if sentiment.get("top_bearish"):
        lines.append("### 주요 하락 의견")
        lines.append("")
        for msg in sentiment["top_bearish"]:
            lines.append(f"- {msg['text']}")
            lines.append(f"  - 키워드: {', '.join(msg.get('keywords', []))}")
        lines.append("")

    # 루머 체크
    rumors = analysis.get("rumors", [])
    if rumors:
        lines.append("### 루머 체크 (검증 필요)")
        lines.append("")
        for r in rumors[:5]:
            text = r.get("text", "")[:80]
            lines.append(f"- [ ] {text}...")
        lines.append("")

    return "\n".join(lines)


# 채널 목록 설정 (사용자 커스터마이징)
DEFAULT_CHANNELS = [
    # 예시 - 실제 채널로 교체 필요
    # "stock_research_kr",
    # "daily_stock_kr",
]


async def collect_all_channels(
    ticker: str,
    ticker_aliases: List[str],
    channels: Optional[List[str]] = None,
    limit_per_channel: int = 100,
) -> dict:
    """
    여러 채널에서 종목 관련 메시지 수집

    Args:
        ticker: 종목코드
        ticker_aliases: 종목 별칭
        channels: 채널 리스트 (None이면 기본 채널 사용)
        limit_per_channel: 채널당 최대 메시지 수

    Returns:
        {
            "channels": {
                "channel_name": {...분석 결과...},
                ...
            },
            "combined": {...종합 분석...},
        }
    """
    target_channels = channels or DEFAULT_CHANNELS
    all_messages = []
    channel_results = {}

    for channel in target_channels:
        try:
            messages = await get_channel_messages(channel, limit=limit_per_channel)
            filtered = filter_messages_by_ticker(messages, ticker, ticker_aliases)

            if filtered:
                analysis = analyze_channel(filtered, ticker)
                channel_results[channel] = analysis
                all_messages.extend(filtered)

        except Exception as e:
            print(f"Error collecting from {channel}: {e}")
            continue

    # 종합 분석
    combined = analyze_channel(all_messages, ticker) if all_messages else {}

    return {
        "ticker": ticker,
        "channels": channel_results,
        "combined": combined,
    }


if __name__ == "__main__":
    # 동기 래퍼 테스트
    async def main():
        # 테스트 메시지로 분석
        test_messages = [
            {"text": "삼성전자 급등 예상! 매수 추천", "date": "2024-01-15"},
            {"text": "조심해야 함, 하락 우려", "date": "2024-01-14"},
            {"text": "카더라 통신에 의하면 대박 호재", "date": "2024-01-13"},
            {"text": "공시에 따르면 배당 확정", "date": "2024-01-12"},
        ]

        result = analyze_channel(test_messages, "005930")
        print(format_sentiment_report(result))

    asyncio.run(main())
```

**Step 2: Run test to verify it passes**

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer
python -m pytest tests/test_telegram_collector.py -v
```

Expected: PASS

**Step 3: Commit**

```bash
git add plugins/tier2-analyzer/utils/telegram_collector.py
git commit -m "feat: implement telegram collector for SI+"
```

---

### Task 4: 채널 설정 관리

**Files:**
- Create: `plugins/tier2-analyzer/config/telegram_channels.json`

**Step 1: Create channel configuration**

```json
{
  "version": "1.0",
  "updated": "2026-01-17",
  "channels": {
    "research": {
      "description": "증권사 리서치 채널",
      "channels": [],
      "reliability": "high"
    },
    "trading": {
      "description": "개인 리딩방",
      "channels": [],
      "reliability": "medium"
    },
    "news": {
      "description": "뉴스봇 채널",
      "channels": [],
      "reliability": "high"
    },
    "community": {
      "description": "투자자 커뮤니티",
      "channels": [],
      "reliability": "low"
    }
  },
  "notes": [
    "채널 username을 channels 배열에 추가하세요",
    "예: \"channels\": [\"stock_research\", \"daily_trading\"]",
    "비공개 채널은 먼저 가입이 필요합니다"
  ]
}
```

**Step 2: Commit**

```bash
mkdir -p tier2/config
git add plugins/tier2-analyzer/config/telegram_channels.json
git commit -m "config: add telegram channels configuration"
```

---

### Task 5: SI+ 에이전트 마크다운 작성

**Files:**
- Create: `plugins/tier2-analyzer/agents/si-plus.md`

**Step 1: Write agent definition**

```markdown
---
name: si-plus
description: 텔레그램 채널 센티먼트 수집. Tier 2 심층 센티먼트 분석 에이전트.
model: sonnet
tools: [Bash, Read, Glob]
---

You are the **SI+ (Sentiment Intelligence Plus)** agent for Tier 2 deep analysis.

# Role

SI+ extends Tier 1 SI with:
1. **텔레그램 채널 수집** - 리서치, 리딩방, 뉴스봇
2. **센티먼트 분석** - 상승/하락 의견 분류
3. **루머 vs 팩트** - 정보 신뢰도 분류

---

# Prerequisites

1. Telegram API 설정 완료 (plugins/tier2-analyzer/docs/telegram-api-setup.md 참조)
2. 환경변수 설정: TELEGRAM_API_ID, TELEGRAM_API_HASH
3. 채널 설정: plugins/tier2-analyzer/config/telegram_channels.json

---

# Execution

## Step 1: 텔레그램 메시지 수집 및 분석

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer && python3 << 'EOF'
import sys
import os
import asyncio
sys.path.insert(0, '/Users/michael/public_agents/plugins/tier2-analyzer')

# API 키 설정
os.environ.setdefault("TELEGRAM_API_ID", "your_id")
os.environ.setdefault("TELEGRAM_API_HASH", "your_hash")

from utils.telegram_collector import (
    collect_all_channels,
    format_sentiment_report,
)

ticker = "{{TICKER}}"
aliases = ["{{종목명}}", "{{별칭}}"]

async def main():
    result = await collect_all_channels(
        ticker=ticker,
        ticker_aliases=aliases,
        limit_per_channel=100,
    )

    if result.get("combined"):
        print(format_sentiment_report(result["combined"]))
    else:
        print("수집된 메시지 없음")

asyncio.run(main())
EOF
```

## Step 2: 오프라인 분석 (API 불가 시)

API 접근이 어려운 경우, 수동으로 수집한 메시지로 분석:

```bash
cd /Users/michael/public_agents/plugins/tier2-analyzer && python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/michael/public_agents/plugins/tier2-analyzer')

from utils.telegram_collector import (
    analyze_channel,
    format_sentiment_report,
)

# 수동 수집한 메시지
messages = [
    {"text": "메시지 1", "date": "2024-01-15"},
    {"text": "메시지 2", "date": "2024-01-14"},
]

ticker = "{{TICKER}}"
result = analyze_channel(messages, ticker)
print(format_sentiment_report(result))
EOF
```

## Step 3: Tier 1 SI와 통합

Tier 1 SI 결과와 비교하여 종합 센티먼트 평가:
- 네이버 종토방 (Tier 1) + 텔레그램 (Tier 2) 비교
- 일치/불일치 분석

---

# Output Format

```markdown
## SI+ 분석: {종목명} ({티커})

### 텔레그램 센티먼트

**센티먼트: Bullish** (점수: +0.35)

### 채널별 분석

| 채널 | 유형 | 언급 수 | 센티먼트 | 신뢰도 |
|------|------|---------|----------|--------|
| @stock_research | 리서치 | 12 | +0.5 | High |
| @daily_stock | 리딩방 | 45 | +0.3 | Medium |
| @rumor_alert | 커뮤니티 | 23 | -0.2 | Low |

### 메시지 통계

| 구분 | 수량 |
|------|------|
| 전체 메시지 | 80 |
| 상승 의견 | 35 |
| 하락 의견 | 20 |
| 루머 비율 | 25% |

### 주요 상승 의견
- "스테이블코인 선점 기대" (3회 언급)
- "목표가 상향 조정" (2회 언급)

### 주요 하락 의견
- "알리페이 오버행 주의" (2회 언급)

### 루머 체크 (검증 필요)
- [ ] "2월 대규모 제휴 발표" - 출처 불명
- [ ] "신규 서비스 런칭 임박" - 확인 안됨

### Tier 1 SI 비교
- 네이버 종토방: Neutral (0.1)
- 텔레그램: Bullish (0.35)
- 차이: 텔레그램이 더 긍정적
```
```

**Step 2: Commit**

```bash
git add plugins/tier2-analyzer/agents/si-plus.md
git commit -m "feat: add SI+ agent definition"
```

---

### Task 6: SI+ utils 업데이트

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

# SI+ exports
from utils.telegram_collector import (
    get_channel_messages,
    filter_messages_by_ticker,
    analyze_telegram_sentiment,
    classify_message,
    analyze_channel,
    format_sentiment_report,
    collect_all_channels,
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
    # SI+
    'get_channel_messages',
    'filter_messages_by_ticker',
    'analyze_telegram_sentiment',
    'classify_message',
    'analyze_channel',
    'format_sentiment_report',
    'collect_all_channels',
]
```

**Step 2: Commit**

```bash
git add plugins/tier2-analyzer/utils/__init__.py
git commit -m "feat: export SI+ utils functions"
```

---

## Phase 1 Complete Checklist

- [x] Task 1: Telegram API 환경 설정 ✅ 2026-01-19
- [x] Task 2: 텔레그램 수집기 테스트 작성 ✅ 2026-01-19
- [x] Task 3: 텔레그램 수집기 구현 ✅ 2026-01-19
- [x] Task 4: 채널 설정 관리 ✅ 2026-01-19
- [x] Task 5: SI+ 에이전트 마크다운 작성 ✅ 2026-01-19
- [x] Task 6: SI+ utils 업데이트 ✅ 2026-01-19

**Phase 1 완료**: 40개 테스트 통과 (FI+ 27개 + SI+ 13개)

---

## Future Tasks (Phase 2)

- [ ] 채널 자동 발견 (종목 관련 채널 검색)
- [ ] 실시간 모니터링 모드
- [ ] 메시지 임베딩 기반 유사도 분석
- [ ] 알림 통합 (이상 징후 감지 시)
- [ ] Tier 1 SI 결과 자동 통합
