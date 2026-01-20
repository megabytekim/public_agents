"""SI+ 통합 수집기

여러 소스에서 센티먼트 데이터를 수집하고 통합 분석
"""
import asyncio
from typing import Optional, List, Dict

from .base import (
    BaseCollector,
    analyze_sentiment,
    classify_rumor,
    get_sentiment_label,
    format_unified_report,
    filter_spam,
)
from .telegram_collector import TelegramCollector
from .reddit_collector import RedditCollector
from .naver_collector import NaverCollector


class UnifiedCollector:
    """
    SI+ 통합 수집기

    여러 소스(Telegram, Reddit, Naver)에서
    센티먼트 데이터를 수집하고 통합 분석
    """

    def __init__(
        self,
        telegram_channels: Optional[List[str]] = None,
        reddit_subreddits: Optional[List[str]] = None,
        enable_naver: bool = True,
    ):
        """
        Args:
            telegram_channels: 텔레그램 채널 리스트
            reddit_subreddits: Reddit 서브레딧 리스트
            enable_naver: 네이버 종토방 수집 여부
        """
        self.collectors: List[BaseCollector] = []

        if telegram_channels:
            self.collectors.append(TelegramCollector(telegram_channels))

        if reddit_subreddits is not None:  # 빈 리스트도 허용 (전체 검색)
            self.collectors.append(RedditCollector(reddit_subreddits))

        if enable_naver:
            self.collectors.append(NaverCollector())

    async def collect(
        self,
        ticker: str,
        aliases: Optional[List[str]] = None,
        theme_keywords: Optional[List[str]] = None,
        limit_per_source: int = 50,
    ) -> Dict:
        """
        모든 소스에서 수집

        Args:
            ticker: 종목코드
            aliases: 종목 별칭
            theme_keywords: 테마 키워드
            limit_per_source: 소스당 최대 메시지 수

        Returns:
            통합 수집 결과
        """
        results = []

        for collector in self.collectors:
            try:
                result = await collector.collect(
                    ticker=ticker,
                    aliases=aliases,
                    theme_keywords=theme_keywords,
                    limit_per_keyword=limit_per_source,
                )
                results.append(result)
                print(f"[{collector.source_name}] 수집 완료: {result['stats']['total_messages']}개")

            except Exception as e:
                print(f"[{collector.source_name}] 수집 실패: {e}")
                continue

        # 모든 메시지 통합
        all_messages = []
        for result in results:
            all_messages.extend(result.get("messages", []))

        # 스팸 필터링
        spam_count = len(all_messages)
        all_messages = filter_spam(all_messages)
        spam_count = spam_count - len(all_messages)
        if spam_count > 0:
            print(f"[Spam Filter] {spam_count}개 스팸 제거됨")

        # 통합 분석
        sentiment = analyze_sentiment(all_messages) if all_messages else {}

        # 루머 분류
        rumors = []
        facts = []
        for msg in all_messages:
            classification = classify_rumor(msg.get("text", ""))
            if classification["is_rumor"]:
                rumors.append({**msg, "rumor_confidence": classification["confidence"]})
            else:
                facts.append({**msg, "fact_confidence": classification["confidence"]})

        return {
            "ticker": ticker,
            "aliases": aliases,
            "theme_keywords": theme_keywords,
            "sources": results,
            "combined": {
                "messages": all_messages,
                "sentiment": sentiment,
                "sentiment_label": get_sentiment_label(sentiment.get("score", 0)) if sentiment else "N/A",
                "rumors": rumors[:10],
                "facts": facts[:10],
            },
            "stats": {
                "total_messages": len(all_messages),
                "by_source": {
                    r.get("source", "unknown"): r.get("stats", {}).get("total_messages", 0)
                    for r in results
                },
                "direct_count": sum(
                    r.get("stats", {}).get("direct_count", 0) for r in results
                ),
                "theme_count": sum(
                    r.get("stats", {}).get("theme_count", 0) for r in results
                ),
                "rumor_ratio": len(rumors) / len(all_messages) if all_messages else 0,
            },
        }

    def generate_report(
        self,
        result: Dict,
    ) -> str:
        """
        수집 결과를 마크다운 리포트로 변환

        Args:
            result: collect() 결과

        Returns:
            마크다운 리포트
        """
        return format_unified_report(
            ticker=result.get("ticker", ""),
            results=result.get("sources", []),
            aliases=result.get("aliases"),
            theme_keywords=result.get("theme_keywords"),
        )


# ============================================================
# 편의 함수
# ============================================================

async def collect_all_sources(
    ticker: str,
    aliases: Optional[List[str]] = None,
    theme_keywords: Optional[List[str]] = None,
    telegram_channels: Optional[List[str]] = None,
    enable_reddit: bool = True,
    enable_naver: bool = True,
    limit_per_source: int = 50,
) -> Dict:
    """
    모든 소스에서 센티먼트 수집 (편의 함수)

    Args:
        ticker: 종목코드
        aliases: 종목 별칭
        theme_keywords: 테마 키워드
        telegram_channels: 텔레그램 채널 (없으면 텔레그램 스킵)
        enable_reddit: Reddit 수집 여부
        enable_naver: 네이버 수집 여부
        limit_per_source: 소스당 최대 메시지 수

    Returns:
        통합 수집 결과

    Usage:
        ```python
        result = await collect_all_sources(
            ticker="005930",
            aliases=["삼성전자", "삼전"],
            theme_keywords=["반도체", "HBM"],
            telegram_channels=["siglab", "FastStockNews"],
        )
        print(result["combined"]["sentiment_label"])
        ```
    """
    collector = UnifiedCollector(
        telegram_channels=telegram_channels,
        reddit_subreddits=[] if enable_reddit else None,
        enable_naver=enable_naver,
    )

    return await collector.collect(
        ticker=ticker,
        aliases=aliases,
        theme_keywords=theme_keywords,
        limit_per_source=limit_per_source,
    )


def collect_all_sources_sync(
    ticker: str,
    aliases: Optional[List[str]] = None,
    theme_keywords: Optional[List[str]] = None,
    telegram_channels: Optional[List[str]] = None,
    enable_reddit: bool = True,
    enable_naver: bool = True,
    limit_per_source: int = 50,
) -> Dict:
    """
    모든 소스에서 센티먼트 수집 (동기 래퍼)
    """
    return asyncio.run(collect_all_sources(
        ticker=ticker,
        aliases=aliases,
        theme_keywords=theme_keywords,
        telegram_channels=telegram_channels,
        enable_reddit=enable_reddit,
        enable_naver=enable_naver,
        limit_per_source=limit_per_source,
    ))
