"""SI+ (Sentiment Intelligence Plus) 패키지

멀티소스 센티먼트 분석을 위한 Tier 2 모듈

지원 소스:
- Telegram: 채널 메시지 수집 (Search API 활용)
- Reddit: 서브레딧 게시물 검색
- Naver: 종토방(토론방) 수집
"""

# 공통 모듈
from .base import (
    # 키워드
    BULLISH_KEYWORDS,
    BEARISH_KEYWORDS,
    RUMOR_INDICATORS,
    FACT_INDICATORS,
    SPAM_PATTERNS,
    # 분석 함수
    analyze_sentiment,
    classify_rumor,
    get_sentiment_label,
    format_unified_report,
    # 스팸 필터링
    is_spam,
    filter_spam,
    # 기본 클래스
    BaseCollector,
    SentimentResult,
)

# 텔레그램 수집기
from .telegram_collector import (
    TelegramCollector,
    # Legacy functions (하위 호환성)
    get_channel_messages,
    filter_messages_by_ticker,
    analyze_telegram_sentiment,
    classify_message,
    analyze_channel,
    format_sentiment_report,
    collect_all_channels,
)

# Reddit 수집기
from .reddit_collector import (
    RedditCollector,
    search_reddit,
)

# 네이버 수집기
from .naver_collector import (
    NaverCollector,
    get_naver_discussions,
)

# 통합 수집기
from .unified_collector import (
    UnifiedCollector,
    collect_all_sources,
    collect_all_sources_sync,
)

# 리포트 생성기
from .report_generator import generate_report

# 컨텍스트 추출기
from .context_extractor import (
    StockContext,
    extract_context_from_analysis,
    context_to_search_config,
)

# Context-Aware 리포트
from .context_aware_report import generate_context_aware_report


__all__ = [
    # 키워드
    "BULLISH_KEYWORDS",
    "BEARISH_KEYWORDS",
    "RUMOR_INDICATORS",
    "FACT_INDICATORS",
    "SPAM_PATTERNS",
    # 분석 함수
    "analyze_sentiment",
    "classify_rumor",
    "get_sentiment_label",
    "format_unified_report",
    # 스팸 필터링
    "is_spam",
    "filter_spam",
    # 기본 클래스
    "BaseCollector",
    "SentimentResult",
    # 수집기 클래스
    "TelegramCollector",
    "RedditCollector",
    "NaverCollector",
    "UnifiedCollector",
    # 편의 함수
    "collect_all_sources",
    "collect_all_sources_sync",
    "search_reddit",
    "get_naver_discussions",
    "generate_report",
    # 컨텍스트 추출기
    "StockContext",
    "extract_context_from_analysis",
    "context_to_search_config",
    "generate_context_aware_report",
    # Legacy (하위 호환성)
    "get_channel_messages",
    "filter_messages_by_ticker",
    "analyze_telegram_sentiment",
    "classify_message",
    "analyze_channel",
    "format_sentiment_report",
    "collect_all_channels",
]
