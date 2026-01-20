"""텔레그램 채널 수집기

Telethon을 사용한 텔레그램 채널 메시지 수집 및 분석
- search API 활용으로 효율적 키워드 검색
"""
import os
import asyncio
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from pathlib import Path
from dotenv import load_dotenv

# .env 로드 (모듈 import 시점에)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(Path.cwd() / ".env")

try:
    from telethon import TelegramClient
    from telethon.tl.types import Channel, Message
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

from .base import (
    BaseCollector,
    SentimentResult,
    BULLISH_KEYWORDS,
    BEARISH_KEYWORDS,
    RUMOR_INDICATORS,
    FACT_INDICATORS,
    analyze_sentiment,
    classify_rumor,
)

SESSION_NAME = "session_siplus"


@asynccontextmanager
async def get_client():
    """텔레그램 클라이언트 컨텍스트 매니저"""
    if not TELETHON_AVAILABLE:
        raise ImportError("Telethon not installed. Run: pip install telethon")

    # 런타임에 환경변수 읽기 (import 시점 아닌)
    api_id = os.environ.get("TELEGRAM_API_ID", "")
    api_hash = os.environ.get("TELEGRAM_API_HASH", "")

    if not api_id or not api_hash:
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")

    client = TelegramClient(SESSION_NAME, api_id, api_hash)
    await client.start()

    try:
        yield client
    finally:
        await client.disconnect()


class TelegramCollector(BaseCollector):
    """텔레그램 채널 수집기"""

    source_name = "telegram"

    def __init__(self, channels: Optional[List[str]] = None):
        self.channels = channels or []

    async def search_messages(
        self,
        channel: str,
        keyword: str,
        limit: int = 100,
    ) -> List[dict]:
        """
        Telegram Search API를 사용하여 키워드 검색

        Args:
            channel: 채널 username
            keyword: 검색 키워드
            limit: 최대 메시지 수

        Returns:
            매칭된 메시지 리스트
        """
        messages = []

        try:
            async with get_client() as client:
                entity = await client.get_entity(channel)

                # Search API 사용 - 키워드로 직접 검색
                async for msg in client.iter_messages(
                    entity,
                    search=keyword,  # 핵심: search 파라미터로 서버사이드 검색
                    limit=limit,
                ):
                    if not msg.text:
                        continue

                    messages.append({
                        "id": msg.id,
                        "text": msg.text,
                        "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                        "views": getattr(msg, 'views', 0) or 0,
                        "forwards": getattr(msg, 'forwards', 0) or 0,
                        "source": "telegram",
                        "channel": channel,
                        "keyword": keyword,
                    })

        except Exception as e:
            print(f"[Telegram] Error searching '{keyword}' in @{channel}: {e}")

        return messages

    async def collect(
        self,
        ticker: str,
        aliases: Optional[List[str]] = None,
        theme_keywords: Optional[List[str]] = None,
        limit_per_keyword: int = 50,
    ) -> Dict:
        """
        여러 채널에서 키워드별로 검색하여 수집

        Args:
            ticker: 종목코드
            aliases: 종목 별칭
            theme_keywords: 테마 키워드
            limit_per_keyword: 키워드당 최대 메시지 수

        Returns:
            수집 결과
        """
        # 검색할 키워드 목록 구성
        direct_keywords = [ticker]
        if aliases:
            direct_keywords.extend(aliases)

        all_keywords = direct_keywords.copy()
        if theme_keywords:
            all_keywords.extend(theme_keywords)

        all_messages = []
        channel_stats = {}

        for channel in self.channels:
            channel_messages = []
            keyword_counts = {}

            for keyword in all_keywords:
                messages = await self.search_messages(
                    channel,
                    keyword,
                    limit=limit_per_keyword,
                )

                # 중복 제거 (message id 기준)
                seen_ids = {m["id"] for m in channel_messages}
                for msg in messages:
                    if msg["id"] not in seen_ids:
                        # 매칭 타입 분류
                        msg["match_type"] = "direct" if keyword in direct_keywords else "theme"
                        msg["matched_keyword"] = keyword
                        channel_messages.append(msg)
                        seen_ids.add(msg["id"])

                keyword_counts[keyword] = len(messages)

            channel_stats[channel] = {
                "total": len(channel_messages),
                "by_keyword": keyword_counts,
            }
            all_messages.extend(channel_messages)

        # 날짜순 정렬
        all_messages.sort(key=lambda x: x.get("date", ""), reverse=True)

        return {
            "source": "telegram",
            "ticker": ticker,
            "messages": all_messages,
            "stats": {
                "total_messages": len(all_messages),
                "channels": channel_stats,
                "direct_count": len([m for m in all_messages if m.get("match_type") == "direct"]),
                "theme_count": len([m for m in all_messages if m.get("match_type") == "theme"]),
            },
        }


# ============================================================
# Legacy functions (하위 호환성 유지)
# ============================================================

async def get_channel_messages(
    channel: str,
    limit: int = 100,
    days_back: int = 7,
) -> List[dict]:
    """
    [Legacy] 텔레그램 채널에서 메시지 수집 (전체 fetch 방식)

    ⚠️ Deprecated: search_messages() 사용 권장
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
    theme_keywords: Optional[List[str]] = None,
) -> List[dict]:
    """
    [Legacy] 종목 관련 메시지 필터링

    ⚠️ Deprecated: TelegramCollector.collect() 사용 권장
    """
    direct_keywords = [ticker]
    if aliases:
        direct_keywords.extend(aliases)

    filtered = []
    for msg in messages:
        text = msg.get("text", "")

        direct_match = [kw for kw in direct_keywords if kw in text]
        if direct_match:
            filtered.append({
                **msg,
                "match_type": "direct",
                "matched_keywords": direct_match,
            })
            continue

        if theme_keywords:
            theme_match = [kw for kw in theme_keywords if kw in text]
            if theme_match:
                filtered.append({
                    **msg,
                    "match_type": "theme",
                    "matched_keywords": theme_match,
                })

    return filtered


def analyze_telegram_sentiment(messages: List[dict]) -> dict:
    """[Legacy] 메시지에서 센티먼트 분석"""
    return analyze_sentiment(messages)


def classify_message(text: str) -> dict:
    """[Legacy] 메시지를 루머 vs 팩트로 분류"""
    return classify_rumor(text)


def analyze_channel(messages: List[dict], ticker: str) -> dict:
    """[Legacy] 채널 종합 분석"""
    sentiment = analyze_sentiment(messages)

    rumors = []
    facts = []
    for msg in messages:
        classification = classify_rumor(msg.get("text", ""))
        if classification["is_rumor"]:
            rumors.append({**msg, "confidence": classification["confidence"]})
        else:
            facts.append({**msg, "confidence": classification["confidence"]})

    def _get_sentiment_label(score: float) -> str:
        if score >= 0.3:
            return "Bullish"
        elif score <= -0.3:
            return "Bearish"
        return "Neutral"

    return {
        "ticker": ticker,
        "sentiment": sentiment,
        "rumors": rumors[:10],
        "facts": facts[:10],
        "summary": {
            "total_messages": len(messages),
            "rumor_ratio": len(rumors) / len(messages) if messages else 0,
            "sentiment_label": _get_sentiment_label(sentiment["score"]),
        },
    }


def format_sentiment_report(analysis: dict) -> str:
    """[Legacy] 분석 결과를 마크다운으로 포맷"""
    lines = []
    sentiment = analysis.get("sentiment", {})
    summary = analysis.get("summary", {})

    lines.append(f"## 텔레그램 센티먼트 분석: {analysis.get('ticker', 'N/A')}")
    lines.append("")

    score = sentiment.get("score", 0)
    label = summary.get("sentiment_label", "Neutral")
    lines.append(f"**센티먼트: {label}** (점수: {score:+.2f})")
    lines.append("")

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

    if sentiment.get("top_bullish"):
        lines.append("### 주요 상승 의견")
        lines.append("")
        for msg in sentiment["top_bullish"]:
            lines.append(f"- {msg['text']}")
            lines.append(f"  - 키워드: {', '.join(msg.get('keywords', []))}")
        lines.append("")

    if sentiment.get("top_bearish"):
        lines.append("### 주요 하락 의견")
        lines.append("")
        for msg in sentiment["top_bearish"]:
            lines.append(f"- {msg['text']}")
            lines.append(f"  - 키워드: {', '.join(msg.get('keywords', []))}")
        lines.append("")

    rumors = analysis.get("rumors", [])
    if rumors:
        lines.append("### 루머 체크 (검증 필요)")
        lines.append("")
        for r in rumors[:5]:
            text = r.get("text", "")[:80]
            lines.append(f"- [ ] {text}...")
        lines.append("")

    return "\n".join(lines)


async def collect_all_channels(
    ticker: str,
    ticker_aliases: List[str],
    channels: Optional[List[str]] = None,
    limit_per_channel: int = 100,
) -> dict:
    """[Legacy] 여러 채널에서 종목 관련 메시지 수집"""
    target_channels = channels or []
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

    combined = analyze_channel(all_messages, ticker) if all_messages else {}

    return {
        "ticker": ticker,
        "channels": channel_results,
        "combined": combined,
    }
