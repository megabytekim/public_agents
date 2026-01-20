"""SI+ base 모듈 테스트

공통 센티먼트 분석, 루머 분류, 키워드 테스트
"""
import pytest
from utils.si_plus.base import (
    BULLISH_KEYWORDS,
    BEARISH_KEYWORDS,
    RUMOR_INDICATORS,
    FACT_INDICATORS,
    SPAM_PATTERNS,
    analyze_sentiment,
    classify_rumor,
    get_sentiment_label,
    format_unified_report,
    is_spam,
    filter_spam,
    SentimentResult,
)


# ============================================================
# 키워드 테스트
# ============================================================

class TestKeywords:
    """키워드 리스트 테스트"""

    def test_bullish_keywords_not_empty(self):
        """상승 키워드 리스트가 비어있지 않음"""
        assert len(BULLISH_KEYWORDS) > 0

    def test_bearish_keywords_not_empty(self):
        """하락 키워드 리스트가 비어있지 않음"""
        assert len(BEARISH_KEYWORDS) > 0

    def test_rumor_indicators_not_empty(self):
        """루머 지표 리스트가 비어있지 않음"""
        assert len(RUMOR_INDICATORS) > 0

    def test_fact_indicators_not_empty(self):
        """팩트 지표 리스트가 비어있지 않음"""
        assert len(FACT_INDICATORS) > 0

    def test_no_overlap_bullish_bearish(self):
        """상승/하락 키워드 중복 없음"""
        overlap = set(BULLISH_KEYWORDS) & set(BEARISH_KEYWORDS)
        assert len(overlap) == 0, f"중복 키워드: {overlap}"

    def test_essential_bullish_keywords_exist(self):
        """필수 상승 키워드 포함"""
        essential = ["급등", "상한가", "매수", "상승"]
        for kw in essential:
            assert kw in BULLISH_KEYWORDS, f"'{kw}' 없음"

    def test_essential_bearish_keywords_exist(self):
        """필수 하락 키워드 포함"""
        essential = ["급락", "하한가", "손절", "하락"]
        for kw in essential:
            assert kw in BEARISH_KEYWORDS, f"'{kw}' 없음"


# ============================================================
# analyze_sentiment 테스트
# ============================================================

class TestAnalyzeSentiment:
    """센티먼트 분석 함수 테스트"""

    def test_returns_dict_with_required_keys(self):
        """필수 키가 포함된 딕셔너리 반환"""
        messages = [{"text": "테스트 메시지", "date": "2024-01-15"}]
        result = analyze_sentiment(messages)

        required_keys = [
            "score", "bullish_count", "bearish_count",
            "neutral_count", "total_messages",
            "top_bullish", "top_bearish"
        ]
        for key in required_keys:
            assert key in result, f"'{key}' 키 없음"

    def test_score_range(self):
        """점수는 -1.0 ~ 1.0 범위"""
        messages = [
            {"text": "급등 급등 급등", "date": "2024-01-15"},
            {"text": "급락 급락", "date": "2024-01-14"},
        ]
        result = analyze_sentiment(messages)
        assert -1.0 <= result["score"] <= 1.0

    def test_bullish_message_positive_score(self):
        """상승 메시지는 양수 점수"""
        messages = [
            {"text": "급등 예상! 매수 추천! 상한가 간다!", "date": "2024-01-15"},
        ]
        result = analyze_sentiment(messages)
        assert result["score"] > 0
        assert result["bullish_count"] == 1
        assert result["bearish_count"] == 0

    def test_bearish_message_negative_score(self):
        """하락 메시지는 음수 점수"""
        messages = [
            {"text": "폭락 주의! 손절 필수! 하한가!", "date": "2024-01-15"},
        ]
        result = analyze_sentiment(messages)
        assert result["score"] < 0
        assert result["bearish_count"] == 1
        assert result["bullish_count"] == 0

    def test_neutral_message_zero_counts(self):
        """중립 메시지는 상승/하락 카운트 0"""
        messages = [
            {"text": "오늘 날씨가 좋네요", "date": "2024-01-15"},
        ]
        result = analyze_sentiment(messages)
        assert result["neutral_count"] == 1
        assert result["bullish_count"] == 0
        assert result["bearish_count"] == 0

    def test_empty_messages_zero_score(self):
        """빈 메시지 리스트는 0점"""
        result = analyze_sentiment([])
        assert result["score"] == 0
        assert result["total_messages"] == 0

    def test_mixed_sentiment_calculation(self):
        """혼합 센티먼트 계산"""
        messages = [
            {"text": "급등!", "date": "2024-01-15"},  # bullish
            {"text": "급락!", "date": "2024-01-14"},  # bearish
            {"text": "그냥 보합", "date": "2024-01-13"},  # neutral
        ]
        result = analyze_sentiment(messages)
        # (1 - 1) / 3 = 0
        assert result["score"] == 0
        assert result["bullish_count"] == 1
        assert result["bearish_count"] == 1
        assert result["neutral_count"] == 1

    def test_top_bullish_max_5(self):
        """top_bullish는 최대 5개"""
        messages = [
            {"text": f"급등 {i}", "date": "2024-01-15"}
            for i in range(10)
        ]
        result = analyze_sentiment(messages)
        assert len(result["top_bullish"]) <= 5

    def test_top_bearish_max_5(self):
        """top_bearish는 최대 5개"""
        messages = [
            {"text": f"폭락 {i}", "date": "2024-01-15"}
            for i in range(10)
        ]
        result = analyze_sentiment(messages)
        assert len(result["top_bearish"]) <= 5

    def test_top_messages_contain_keywords(self):
        """상위 메시지에 키워드 포함"""
        messages = [
            {"text": "급등 상한가 대박!", "date": "2024-01-15"},
        ]
        result = analyze_sentiment(messages)
        assert len(result["top_bullish"]) == 1
        assert "keywords" in result["top_bullish"][0]
        assert len(result["top_bullish"][0]["keywords"]) > 0

    def test_prioritize_direct_matches_bullish(self):
        """직접 매칭이 top_bullish에서 우선"""
        messages = [
            {"text": "급등 테마 매칭", "date": "2024-01-15", "match_type": "theme"},
            {"text": "급등 테마 매칭 2", "date": "2024-01-15", "match_type": "theme"},
            {"text": "급등 직접 매칭!", "date": "2024-01-15", "match_type": "direct"},
        ]
        result = analyze_sentiment(messages, prioritize_direct=True)
        # 직접 매칭이 먼저 와야 함
        assert result["top_bullish"][0]["match_type"] == "direct"

    def test_prioritize_direct_matches_bearish(self):
        """직접 매칭이 top_bearish에서 우선"""
        messages = [
            {"text": "폭락 테마 매칭", "date": "2024-01-15", "match_type": "theme"},
            {"text": "폭락 직접 매칭!", "date": "2024-01-15", "match_type": "direct"},
        ]
        result = analyze_sentiment(messages, prioritize_direct=True)
        assert result["top_bearish"][0]["match_type"] == "direct"

    def test_prioritize_direct_fills_with_theme(self):
        """직접 매칭 부족 시 테마로 채움"""
        messages = [
            {"text": "급등 직접 1", "date": "2024-01-15", "match_type": "direct"},
            {"text": "급등 직접 2", "date": "2024-01-15", "match_type": "direct"},
            {"text": "급등 테마 1", "date": "2024-01-15", "match_type": "theme"},
            {"text": "급등 테마 2", "date": "2024-01-15", "match_type": "theme"},
            {"text": "급등 테마 3", "date": "2024-01-15", "match_type": "theme"},
            {"text": "급등 테마 4", "date": "2024-01-15", "match_type": "theme"},
        ]
        result = analyze_sentiment(messages, prioritize_direct=True)
        # 직접 2개 + 테마 3개 = 5개
        assert len(result["top_bullish"]) == 5
        direct_count = sum(1 for m in result["top_bullish"] if m["match_type"] == "direct")
        assert direct_count == 2

    def test_prioritize_direct_false_mixes(self):
        """prioritize_direct=False면 순서대로"""
        messages = [
            {"text": "급등 테마", "date": "2024-01-15", "match_type": "theme"},
            {"text": "급등 직접", "date": "2024-01-15", "match_type": "direct"},
        ]
        result = analyze_sentiment(messages, prioritize_direct=False)
        # 순서대로 나옴 (직접+테마 통합)
        assert len(result["top_bullish"]) == 2


# ============================================================
# classify_rumor 테스트
# ============================================================

class TestClassifyRumor:
    """루머 분류 함수 테스트"""

    def test_returns_dict_with_required_keys(self):
        """필수 키가 포함된 딕셔너리 반환"""
        result = classify_rumor("테스트 메시지")
        required_keys = ["is_rumor", "confidence", "indicators"]
        for key in required_keys:
            assert key in result, f"'{key}' 키 없음"

    def test_rumor_indicator_detected(self):
        """루머 지표 감지"""
        result = classify_rumor("카더라 통신에 의하면 곧 호재 있을 듯")
        assert result["is_rumor"] is True
        assert result["confidence"] > 0.5

    def test_fact_indicator_detected(self):
        """팩트 지표 감지"""
        result = classify_rumor("공시에 따르면 배당금 1000원 확정")
        assert result["is_rumor"] is False
        assert result["confidence"] > 0.5

    def test_neutral_message_low_confidence(self):
        """중립 메시지는 낮은 신뢰도"""
        result = classify_rumor("오늘 날씨가 좋네요")
        assert result["confidence"] == 0.5
        assert result["indicators"] == []

    def test_mixed_indicators_majority_wins(self):
        """혼합 지표는 다수결"""
        # 루머 지표 2개, 팩트 지표 1개
        result = classify_rumor("카더라 통신, 아마도 공시 예정")
        # "카더라", "아마도" vs "공시"
        # 루머가 더 많으므로 is_rumor = True
        assert result["is_rumor"] is True

    def test_indicators_dict_structure(self):
        """지표 딕셔너리 구조"""
        result = classify_rumor("카더라, 공시")
        if result["indicators"]:
            assert "rumor" in result["indicators"]
            assert "fact" in result["indicators"]


# ============================================================
# get_sentiment_label 테스트
# ============================================================

class TestGetSentimentLabel:
    """센티먼트 레이블 함수 테스트"""

    def test_bullish_threshold(self):
        """Bullish 임계값 (+0.3 이상)"""
        assert get_sentiment_label(0.3) == "Bullish"
        assert get_sentiment_label(0.5) == "Bullish"
        assert get_sentiment_label(1.0) == "Bullish"

    def test_bearish_threshold(self):
        """Bearish 임계값 (-0.3 이하)"""
        assert get_sentiment_label(-0.3) == "Bearish"
        assert get_sentiment_label(-0.5) == "Bearish"
        assert get_sentiment_label(-1.0) == "Bearish"

    def test_neutral_range(self):
        """Neutral 범위 (-0.3 ~ +0.3)"""
        assert get_sentiment_label(0.0) == "Neutral"
        assert get_sentiment_label(0.1) == "Neutral"
        assert get_sentiment_label(-0.1) == "Neutral"
        assert get_sentiment_label(0.29) == "Neutral"
        assert get_sentiment_label(-0.29) == "Neutral"


# ============================================================
# format_unified_report 테스트
# ============================================================

class TestFormatUnifiedReport:
    """통합 리포트 포맷 함수 테스트"""

    def test_returns_string(self):
        """문자열 반환"""
        result = format_unified_report("005930", [])
        assert isinstance(result, str)

    def test_contains_ticker(self):
        """티커 포함"""
        result = format_unified_report("005930", [])
        assert "005930" in result

    def test_contains_markdown_headers(self):
        """마크다운 헤더 포함"""
        result = format_unified_report("005930", [])
        assert "#" in result

    def test_with_results_contains_source_table(self):
        """결과가 있으면 소스 테이블 포함"""
        results = [
            {
                "source": "telegram",
                "messages": [{"text": "테스트", "date": "2024-01-15"}],
                "stats": {
                    "total_messages": 1,
                    "direct_count": 1,
                    "theme_count": 0,
                },
            }
        ]
        result = format_unified_report("005930", results)
        assert "telegram" in result
        assert "| 소스 |" in result  # 테이블 헤더


# ============================================================
# SentimentResult 데이터클래스 테스트
# ============================================================

class TestSentimentResult:
    """SentimentResult 데이터클래스 테스트"""

    def test_label_property_bullish(self):
        """label 프로퍼티 - Bullish"""
        sr = SentimentResult(
            score=0.5,
            bullish_count=5,
            bearish_count=1,
            neutral_count=2,
            total_messages=8,
            top_bullish=[],
            top_bearish=[],
        )
        assert sr.label == "Bullish"

    def test_label_property_bearish(self):
        """label 프로퍼티 - Bearish"""
        sr = SentimentResult(
            score=-0.5,
            bullish_count=1,
            bearish_count=5,
            neutral_count=2,
            total_messages=8,
            top_bullish=[],
            top_bearish=[],
        )
        assert sr.label == "Bearish"

    def test_label_property_neutral(self):
        """label 프로퍼티 - Neutral"""
        sr = SentimentResult(
            score=0.1,
            bullish_count=2,
            bearish_count=2,
            neutral_count=4,
            total_messages=8,
            top_bullish=[],
            top_bearish=[],
        )
        assert sr.label == "Neutral"


# ============================================================
# 스팸 필터링 테스트
# ============================================================

class TestSpamFiltering:
    """스팸 필터링 테스트"""

    def test_spam_patterns_not_empty(self):
        """스팸 패턴 리스트가 비어있지 않음"""
        assert len(SPAM_PATTERNS) > 0

    def test_is_spam_loan_keywords(self):
        """대출 관련 키워드 스팸 감지"""
        assert is_spam("전세자금대출비교 - 과연 어떤 조건이 가장 유리할까?")
        assert is_spam("동그라미대부 대출 전 꼭 알아야 할 꿀팁")
        assert is_spam("무직자대출 OK 당일 급전 가능")

    def test_is_spam_gambling_keywords(self):
        """도박 관련 키워드 스팸 감지"""
        assert is_spam("카지노 무료 체험 이벤트")
        assert is_spam("바카라 필승 전략 공개")
        assert is_spam("스포츠토토 분석 전문")

    def test_is_spam_ad_keywords(self):
        """광고성 키워드 스팸 감지"""
        assert is_spam("텔레그램 문의 주세요")
        assert is_spam("클릭하면 무료 상담")

    def test_is_spam_normal_stock_message(self):
        """일반 주식 메시지는 스팸 아님"""
        assert not is_spam("케이옥션 급등 예상! 매수 추천!")
        assert not is_spam("삼성전자 분기 실적 발표")
        assert not is_spam("오늘 시장 전망이 좋네요")

    def test_is_spam_case_insensitive(self):
        """대소문자 구분 없이 감지 (URL 패턴)"""
        assert is_spam("bit.ly/abc123 접속")
        assert is_spam("BIT.LY/ABC123 접속")

    def test_filter_spam_removes_spam(self):
        """filter_spam이 스팸 메시지 제거"""
        messages = [
            {"text": "급등 예상!", "date": "2024-01-15"},
            {"text": "전세자금대출 추천", "date": "2024-01-15"},
            {"text": "매수 타이밍", "date": "2024-01-15"},
            {"text": "카지노 무료 게임", "date": "2024-01-15"},
        ]
        filtered = filter_spam(messages)
        assert len(filtered) == 2
        assert all("대출" not in m["text"] for m in filtered)
        assert all("카지노" not in m["text"] for m in filtered)

    def test_filter_spam_preserves_order(self):
        """filter_spam이 순서 유지"""
        messages = [
            {"text": "첫번째", "date": "2024-01-15"},
            {"text": "대출 스팸", "date": "2024-01-15"},
            {"text": "세번째", "date": "2024-01-15"},
        ]
        filtered = filter_spam(messages)
        assert filtered[0]["text"] == "첫번째"
        assert filtered[1]["text"] == "세번째"

    def test_filter_spam_empty_list(self):
        """빈 리스트 처리"""
        assert filter_spam([]) == []

    def test_filter_spam_all_spam(self):
        """모든 메시지가 스팸인 경우"""
        messages = [
            {"text": "대출 광고", "date": "2024-01-15"},
            {"text": "카지노 홍보", "date": "2024-01-15"},
        ]
        filtered = filter_spam(messages)
        assert len(filtered) == 0
