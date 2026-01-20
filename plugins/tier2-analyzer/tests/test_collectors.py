"""SI+ 수집기 테스트

TelegramCollector, RedditCollector, NaverCollector 테스트
(네트워크 호출은 Mock 처리)
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio


# ============================================================
# TelegramCollector 테스트
# ============================================================

class TestTelegramCollector:
    """텔레그램 수집기 테스트"""

    def test_init_with_channels(self):
        """채널 리스트로 초기화"""
        from utils.si_plus import TelegramCollector

        channels = ["channel1", "channel2"]
        collector = TelegramCollector(channels)

        assert collector.channels == channels
        assert collector.source_name == "telegram"

    def test_init_empty_channels(self):
        """빈 채널로 초기화"""
        from utils.si_plus import TelegramCollector

        collector = TelegramCollector()
        assert collector.channels == []

    @pytest.mark.asyncio
    async def test_search_messages_returns_list(self):
        """search_messages는 리스트 반환"""
        from utils.si_plus import TelegramCollector

        collector = TelegramCollector(["test_channel"])

        # Mock the get_client context manager
        mock_client = AsyncMock()
        mock_client.get_entity = AsyncMock(return_value=MagicMock())
        mock_client.iter_messages = AsyncMock(return_value=[])

        with patch('utils.si_plus.telegram_collector.get_client') as mock_get_client:
            mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await collector.search_messages("test_channel", "키워드", limit=10)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_collect_returns_dict_structure(self):
        """collect는 올바른 구조의 dict 반환"""
        from utils.si_plus import TelegramCollector

        collector = TelegramCollector([])  # 빈 채널

        result = await collector.collect(
            ticker="005930",
            aliases=["삼성전자"],
            theme_keywords=["반도체"],
        )

        assert "source" in result
        assert result["source"] == "telegram"
        assert "ticker" in result
        assert "messages" in result
        assert "stats" in result

    @pytest.mark.asyncio
    async def test_collect_stats_structure(self):
        """collect stats 구조 확인"""
        from utils.si_plus import TelegramCollector

        collector = TelegramCollector([])

        result = await collector.collect(ticker="005930")

        stats = result["stats"]
        assert "total_messages" in stats
        assert "channels" in stats
        assert "direct_count" in stats
        assert "theme_count" in stats


# ============================================================
# RedditCollector 테스트
# ============================================================

class TestRedditCollector:
    """Reddit 수집기 테스트"""

    def test_init_with_subreddits(self):
        """서브레딧 리스트로 초기화"""
        from utils.si_plus import RedditCollector

        subreddits = ["korea_stock", "hanguk"]
        collector = RedditCollector(subreddits)

        assert collector.subreddits == subreddits
        assert collector.source_name == "reddit"

    def test_init_default_subreddits(self):
        """기본 서브레딧으로 초기화"""
        from utils.si_plus import RedditCollector

        collector = RedditCollector()
        assert len(collector.subreddits) > 0

    def test_search_subreddit_returns_list(self):
        """search_subreddit은 리스트 반환"""
        from utils.si_plus import RedditCollector

        collector = RedditCollector()

        # Mock requests
        with patch.object(collector.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": {
                    "children": [
                        {
                            "data": {
                                "id": "abc123",
                                "title": "테스트 제목",
                                "selftext": "테스트 본문",
                                "created_utc": 1704067200,
                                "score": 10,
                                "num_comments": 5,
                                "permalink": "/r/test/comments/abc123",
                                "subreddit": "test",
                                "author": "user1",
                            }
                        }
                    ]
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = collector.search_subreddit("test", "키워드", limit=10)

        assert isinstance(result, list)
        if result:
            assert "id" in result[0]
            assert "text" in result[0]
            assert "source" in result[0]

    def test_search_all_returns_list(self):
        """search_all은 리스트 반환"""
        from utils.si_plus import RedditCollector

        collector = RedditCollector()

        with patch.object(collector.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": {"children": []}}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = collector.search_all("키워드", limit=10)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_collect_returns_dict_structure(self):
        """collect는 올바른 구조의 dict 반환"""
        from utils.si_plus import RedditCollector

        collector = RedditCollector()

        with patch.object(collector, 'search_all', return_value=[]):
            result = await collector.collect(
                ticker="005930",
                aliases=["삼성전자"],
            )

        assert "source" in result
        assert result["source"] == "reddit"
        assert "ticker" in result
        assert "messages" in result
        assert "stats" in result

    def test_timestamp_to_str(self):
        """Unix timestamp 변환 테스트"""
        from utils.si_plus import RedditCollector

        result = RedditCollector._timestamp_to_str(1704067200)  # 2024-01-01 00:00:00 UTC
        assert isinstance(result, str)
        assert "2024" in result


# ============================================================
# NaverCollector 테스트
# ============================================================

class TestNaverCollector:
    """네이버 수집기 테스트"""

    def test_init(self):
        """초기화 테스트"""
        from utils.si_plus import NaverCollector

        collector = NaverCollector()
        assert collector.source_name == "naver"

    def test_get_discussion_board_returns_list(self):
        """get_discussion_board은 리스트 반환"""
        from utils.si_plus import NaverCollector

        collector = NaverCollector()

        # Mock HTML response
        mock_html = """
        <table class="type2">
            <tbody>
                <tr>
                    <td>01.15 12:30</td>
                    <td class="title"><a href="/item/board_read.naver?code=005930&nid=123">테스트 제목</a></td>
                    <td>user1</td>
                    <td>100</td>
                    <td>5</td>
                </tr>
            </tbody>
        </table>
        """

        with patch.object(collector.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = mock_html
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = collector.get_discussion_board("005930", limit=10)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_collect_returns_dict_structure(self):
        """collect는 올바른 구조의 dict 반환"""
        from utils.si_plus import NaverCollector

        collector = NaverCollector()

        with patch.object(collector, 'get_discussion_board', return_value=[
            {"text": "테스트", "title": "테스트 제목", "date": "2024-01-15"}
        ]):
            result = await collector.collect(
                ticker="005930",
                aliases=["삼성전자"],
            )

        assert "source" in result
        assert result["source"] == "naver"
        assert "ticker" in result
        assert "messages" in result
        assert "stats" in result

    def test_extract_post_id(self):
        """게시물 ID 추출"""
        from utils.si_plus import NaverCollector

        url = "/item/board_read.naver?code=005930&nid=123456"
        result = NaverCollector._extract_post_id(url)
        assert result == "123456"

    def test_parse_number(self):
        """숫자 파싱"""
        from utils.si_plus import NaverCollector

        assert NaverCollector._parse_number("1,234") == 1234
        assert NaverCollector._parse_number("100") == 100
        assert NaverCollector._parse_number("invalid") == 0

    def test_normalize_date_mm_dd(self):
        """MM.DD HH:MM 형식 날짜 정규화"""
        from utils.si_plus import NaverCollector
        from datetime import date

        result = NaverCollector._normalize_date("01.15 12:30")
        year = date.today().year
        assert f"{year}-01-15" in result


# ============================================================
# 편의 함수 테스트
# ============================================================

class TestConvenienceFunctions:
    """편의 함수 테스트"""

    def test_search_reddit(self):
        """search_reddit 함수"""
        from utils.si_plus import search_reddit

        with patch('utils.si_plus.reddit_collector.RedditCollector.search_all', return_value=[]):
            result = search_reddit("테스트")

        assert isinstance(result, list)

    def test_get_naver_discussions(self):
        """get_naver_discussions 함수"""
        from utils.si_plus import get_naver_discussions

        with patch('utils.si_plus.naver_collector.NaverCollector.get_discussion_board', return_value=[]):
            result = get_naver_discussions("005930")

        assert isinstance(result, list)


# ============================================================
# Legacy 함수 호환성 테스트
# ============================================================

class TestLegacyCompatibility:
    """기존 함수 하위 호환성 테스트"""

    def test_filter_messages_by_ticker(self):
        """filter_messages_by_ticker 함수 동작"""
        from utils.si_plus import filter_messages_by_ticker

        messages = [
            {"text": "삼성전자 급등", "date": "2024-01-15"},
            {"text": "관계없는 글", "date": "2024-01-15"},
        ]

        result = filter_messages_by_ticker(messages, "005930", ["삼성전자"])

        assert len(result) == 1
        assert result[0]["match_type"] == "direct"

    def test_filter_messages_with_theme_keywords(self):
        """테마 키워드 필터링"""
        from utils.si_plus import filter_messages_by_ticker

        messages = [
            {"text": "반도체 급등", "date": "2024-01-15"},
            {"text": "관계없는 글", "date": "2024-01-15"},
        ]

        result = filter_messages_by_ticker(
            messages, "005930", ["삼성전자"],
            theme_keywords=["반도체"]
        )

        assert len(result) == 1
        assert result[0]["match_type"] == "theme"

    def test_analyze_channel(self):
        """analyze_channel 함수 동작"""
        from utils.si_plus import analyze_channel

        messages = [
            {"text": "급등 예상!", "date": "2024-01-15"},
        ]

        result = analyze_channel(messages, "005930")

        assert "ticker" in result
        assert "sentiment" in result
        assert "summary" in result

    def test_format_sentiment_report(self):
        """format_sentiment_report 함수 동작"""
        from utils.si_plus import analyze_channel, format_sentiment_report

        messages = [{"text": "테스트", "date": "2024-01-15"}]
        analysis = analyze_channel(messages, "005930")
        result = format_sentiment_report(analysis)

        assert isinstance(result, str)
        assert "005930" in result
