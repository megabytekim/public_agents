"""텔레그램 수집기 테스트"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestFilterMessagesByTicker:
    """종목별 메시지 필터링 테스트"""

    def test_filters_by_ticker_code(self):
        """종목코드로 필터링"""
        from utils.si_plus.telegram_collector import filter_messages_by_ticker

        messages = [
            {"text": "삼성전자 상승 기대", "date": "2024-01-15"},
            {"text": "오늘 날씨 좋네요", "date": "2024-01-15"},
            {"text": "005930 매수 추천", "date": "2024-01-15"},
        ]

        result = filter_messages_by_ticker(messages, "005930", ["삼성전자", "삼성"])

        assert len(result) == 2

    def test_filters_by_alias(self):
        """종목 별칭으로 필터링"""
        from utils.si_plus.telegram_collector import filter_messages_by_ticker

        messages = [
            {"text": "삼전 급등!", "date": "2024-01-15"},
            {"text": "관계없는 메시지", "date": "2024-01-15"},
        ]

        result = filter_messages_by_ticker(messages, "005930", ["삼성전자", "삼전"])

        assert len(result) == 1

    def test_empty_messages_returns_empty(self):
        """빈 메시지 리스트는 빈 결과 반환"""
        from utils.si_plus.telegram_collector import filter_messages_by_ticker

        result = filter_messages_by_ticker([], "005930", ["삼성전자"])

        assert result == []


class TestAnalyzeTelegramSentiment:
    """텔레그램 센티먼트 분석 테스트"""

    def test_returns_sentiment_score(self):
        """센티먼트 점수 반환"""
        from utils.si_plus.telegram_collector import analyze_telegram_sentiment

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
        from utils.si_plus.telegram_collector import analyze_telegram_sentiment

        messages = [
            {"text": "대박! 급등 예상! 상한가 갈 듯", "date": "2024-01-15"},
        ]

        result = analyze_telegram_sentiment(messages)

        assert result["bullish_count"] > 0
        assert result["score"] > 0

    def test_identifies_bearish_keywords(self):
        """하락 키워드 감지"""
        from utils.si_plus.telegram_collector import analyze_telegram_sentiment

        messages = [
            {"text": "폭락 주의! 손절 필수", "date": "2024-01-15"},
        ]

        result = analyze_telegram_sentiment(messages)

        assert result["bearish_count"] > 0
        assert result["score"] < 0

    def test_empty_messages_returns_zero_score(self):
        """빈 메시지는 0점 반환"""
        from utils.si_plus.telegram_collector import analyze_telegram_sentiment

        result = analyze_telegram_sentiment([])

        assert result["score"] == 0
        assert result["total_messages"] == 0


class TestClassifyMessage:
    """루머 분류 테스트"""

    def test_identifies_rumor(self):
        """루머 감지"""
        from utils.si_plus.telegram_collector import classify_message

        message = "카더라 통신에 의하면 곧 대규모 이벤트 있을 듯"

        result = classify_message(message)

        assert result["is_rumor"] is True
        assert result["confidence"] > 0.5  # rumor confidence

    def test_identifies_fact(self):
        """팩트 감지"""
        from utils.si_plus.telegram_collector import classify_message

        message = "공시에 따르면 배당금 1,000원 확정"

        result = classify_message(message)

        assert result["is_rumor"] is False
        assert result["confidence"] > 0.5

    def test_neutral_message(self):
        """중립 메시지는 루머 아님"""
        from utils.si_plus.telegram_collector import classify_message

        message = "오늘 날씨가 좋네요"

        result = classify_message(message)

        assert result["confidence"] == 0.5


class TestAnalyzeChannel:
    """채널 분석 테스트"""

    def test_returns_analysis_structure(self):
        """분석 결과 구조 확인"""
        from utils.si_plus.telegram_collector import analyze_channel

        messages = [
            {"text": "삼성전자 급등 기대! 매수 추천", "date": "2024-01-15"},
            {"text": "카더라로는 호재 있다더라", "date": "2024-01-14"},
        ]

        result = analyze_channel(messages, "005930")

        assert "ticker" in result
        assert "sentiment" in result
        assert "rumors" in result
        assert "facts" in result
        assert "summary" in result

    def test_summary_has_sentiment_label(self):
        """요약에 센티먼트 레이블 포함"""
        from utils.si_plus.telegram_collector import analyze_channel

        messages = [
            {"text": "급등! 상한가! 대박!", "date": "2024-01-15"},
        ]

        result = analyze_channel(messages, "005930")

        assert result["summary"]["sentiment_label"] in ["Bullish", "Bearish", "Neutral"]


class TestFormatSentimentReport:
    """리포트 포맷 테스트"""

    def test_returns_markdown_string(self):
        """마크다운 문자열 반환"""
        from utils.si_plus.telegram_collector import analyze_channel, format_sentiment_report

        messages = [
            {"text": "삼성전자 급등 기대", "date": "2024-01-15"},
        ]

        analysis = analyze_channel(messages, "005930")
        result = format_sentiment_report(analysis)

        assert isinstance(result, str)
        assert "##" in result  # 마크다운 헤더
        assert "005930" in result
