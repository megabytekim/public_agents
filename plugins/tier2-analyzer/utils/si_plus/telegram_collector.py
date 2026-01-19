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
DEFAULT_CHANNELS: List[str] = [
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
    all_messages: List[dict] = []
    channel_results: Dict[str, dict] = {}

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
