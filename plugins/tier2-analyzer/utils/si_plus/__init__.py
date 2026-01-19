"""SI+ (Sentiment Intelligence Plus) 패키지

텔레그램 채널 센티먼트 분석을 위한 Tier 2 모듈
"""

from .telegram_collector import (
    # 메시지 수집
    get_channel_messages,
    filter_messages_by_ticker,
    # 센티먼트 분석
    analyze_telegram_sentiment,
    classify_message,
    analyze_channel,
    # 리포트
    format_sentiment_report,
    # 통합 수집
    collect_all_channels,
    # 키워드
    BULLISH_KEYWORDS,
    BEARISH_KEYWORDS,
    RUMOR_INDICATORS,
    FACT_INDICATORS,
)

__all__ = [
    "get_channel_messages",
    "filter_messages_by_ticker",
    "analyze_telegram_sentiment",
    "classify_message",
    "analyze_channel",
    "format_sentiment_report",
    "collect_all_channels",
    "BULLISH_KEYWORDS",
    "BEARISH_KEYWORDS",
    "RUMOR_INDICATORS",
    "FACT_INDICATORS",
]
