"""UnifiedCollector 테스트

멀티소스 통합 수집기 테스트
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestUnifiedCollectorInit:
    """UnifiedCollector 초기화 테스트"""

    def test_init_with_telegram_channels(self):
        """텔레그램 채널로 초기화"""
        from utils.si_plus import UnifiedCollector

        collector = UnifiedCollector(
            telegram_channels=["channel1", "channel2"],
        )

        # TelegramCollector가 추가되어야 함
        assert len(collector.collectors) >= 1
        assert any(c.source_name == "telegram" for c in collector.collectors)

    def test_init_with_reddit(self):
        """Reddit 활성화 초기화"""
        from utils.si_plus import UnifiedCollector

        collector = UnifiedCollector(
            reddit_subreddits=[],  # 빈 리스트 = 전체 검색
        )

        assert any(c.source_name == "reddit" for c in collector.collectors)

    def test_init_with_naver(self):
        """네이버 활성화 초기화"""
        from utils.si_plus import UnifiedCollector

        collector = UnifiedCollector(
            enable_naver=True,
        )

        assert any(c.source_name == "naver" for c in collector.collectors)

    def test_init_all_sources(self):
        """모든 소스 활성화"""
        from utils.si_plus import UnifiedCollector

        collector = UnifiedCollector(
            telegram_channels=["channel1"],
            reddit_subreddits=[],
            enable_naver=True,
        )

        source_names = [c.source_name for c in collector.collectors]
        assert "telegram" in source_names
        assert "reddit" in source_names
        assert "naver" in source_names

    def test_init_empty(self):
        """빈 초기화"""
        from utils.si_plus import UnifiedCollector

        collector = UnifiedCollector(
            telegram_channels=None,
            reddit_subreddits=None,
            enable_naver=False,
        )

        assert len(collector.collectors) == 0


class TestUnifiedCollectorCollect:
    """UnifiedCollector collect 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_collect_returns_dict_structure(self):
        """collect는 올바른 구조의 dict 반환"""
        from utils.si_plus import UnifiedCollector

        collector = UnifiedCollector(enable_naver=False)  # 빈 컬렉터

        result = await collector.collect(
            ticker="005930",
            aliases=["삼성전자"],
            theme_keywords=["반도체"],
        )

        required_keys = ["ticker", "aliases", "theme_keywords", "sources", "combined", "stats"]
        for key in required_keys:
            assert key in result, f"'{key}' 키 없음"

    @pytest.mark.asyncio
    async def test_collect_combined_structure(self):
        """combined 결과 구조 확인"""
        from utils.si_plus import UnifiedCollector

        collector = UnifiedCollector(enable_naver=False)

        result = await collector.collect(ticker="005930")

        combined = result["combined"]
        assert "messages" in combined
        assert "sentiment" in combined
        assert "sentiment_label" in combined
        assert "rumors" in combined
        assert "facts" in combined

    @pytest.mark.asyncio
    async def test_collect_stats_structure(self):
        """stats 결과 구조 확인"""
        from utils.si_plus import UnifiedCollector

        collector = UnifiedCollector(enable_naver=False)

        result = await collector.collect(ticker="005930")

        stats = result["stats"]
        assert "total_messages" in stats
        assert "by_source" in stats
        assert "direct_count" in stats
        assert "theme_count" in stats
        assert "rumor_ratio" in stats

    @pytest.mark.asyncio
    async def test_collect_with_mock_collector(self):
        """Mock 수집기로 테스트"""
        from utils.si_plus import UnifiedCollector
        from utils.si_plus.base import BaseCollector

        # Mock 수집기 생성
        class MockCollector(BaseCollector):
            source_name = "mock"

            async def collect(self, ticker, **kwargs):
                return {
                    "source": "mock",
                    "ticker": ticker,
                    "messages": [
                        {"text": "급등 예상!", "date": "2024-01-15", "source": "mock"},
                        {"text": "폭락 주의!", "date": "2024-01-14", "source": "mock"},
                    ],
                    "stats": {
                        "total_messages": 2,
                        "direct_count": 2,
                        "theme_count": 0,
                    },
                }

        collector = UnifiedCollector(enable_naver=False)
        collector.collectors = [MockCollector()]

        result = await collector.collect(ticker="005930")

        assert result["stats"]["total_messages"] == 2
        assert result["stats"]["by_source"]["mock"] == 2
        assert len(result["combined"]["messages"]) == 2

    @pytest.mark.asyncio
    async def test_collect_sentiment_analysis(self):
        """센티먼트 분석 통합"""
        from utils.si_plus import UnifiedCollector
        from utils.si_plus.base import BaseCollector

        class BullishCollector(BaseCollector):
            source_name = "bullish_test"

            async def collect(self, ticker, **kwargs):
                return {
                    "source": "bullish_test",
                    "ticker": ticker,
                    "messages": [
                        {"text": "급등! 상한가! 대박!", "date": "2024-01-15"},
                    ],
                    "stats": {"total_messages": 1, "direct_count": 1, "theme_count": 0},
                }

        collector = UnifiedCollector(enable_naver=False)
        collector.collectors = [BullishCollector()]

        result = await collector.collect(ticker="005930")

        assert result["combined"]["sentiment"]["bullish_count"] >= 1
        assert result["combined"]["sentiment_label"] in ["Bullish", "Neutral"]

    @pytest.mark.asyncio
    async def test_collect_rumor_classification(self):
        """루머 분류 통합"""
        from utils.si_plus import UnifiedCollector
        from utils.si_plus.base import BaseCollector

        class RumorCollector(BaseCollector):
            source_name = "rumor_test"

            async def collect(self, ticker, **kwargs):
                return {
                    "source": "rumor_test",
                    "ticker": ticker,
                    "messages": [
                        {"text": "카더라 통신에 의하면 호재", "date": "2024-01-15"},
                        {"text": "공시에 따르면 배당 확정", "date": "2024-01-14"},
                    ],
                    "stats": {"total_messages": 2, "direct_count": 2, "theme_count": 0},
                }

        collector = UnifiedCollector(enable_naver=False)
        collector.collectors = [RumorCollector()]

        result = await collector.collect(ticker="005930")

        assert len(result["combined"]["rumors"]) >= 1
        assert len(result["combined"]["facts"]) >= 1


class TestUnifiedCollectorReport:
    """UnifiedCollector 리포트 생성 테스트"""

    def test_generate_report_returns_string(self):
        """generate_report는 문자열 반환"""
        from utils.si_plus import UnifiedCollector

        collector = UnifiedCollector(enable_naver=False)

        mock_result = {
            "ticker": "005930",
            "aliases": ["삼성전자"],
            "theme_keywords": ["반도체"],
            "sources": [],
            "combined": {"messages": [], "sentiment": {}},
            "stats": {},
        }

        report = collector.generate_report(mock_result)

        assert isinstance(report, str)
        assert "005930" in report

    def test_generate_report_contains_sections(self):
        """리포트에 필수 섹션 포함"""
        from utils.si_plus import UnifiedCollector

        collector = UnifiedCollector(enable_naver=False)

        mock_result = {
            "ticker": "005930",
            "aliases": ["삼성전자"],
            "theme_keywords": ["반도체"],
            "sources": [
                {
                    "source": "test",
                    "messages": [{"text": "테스트", "date": "2024-01-15"}],
                    "stats": {"total_messages": 1, "direct_count": 1, "theme_count": 0},
                }
            ],
            "combined": {"messages": [], "sentiment": {}},
            "stats": {},
        }

        report = collector.generate_report(mock_result)

        assert "#" in report  # 마크다운 헤더
        assert "소스" in report or "test" in report


class TestConvenienceFunctions:
    """collect_all_sources 편의 함수 테스트"""

    @pytest.mark.asyncio
    async def test_collect_all_sources_returns_dict(self):
        """collect_all_sources는 dict 반환"""
        from utils.si_plus import collect_all_sources

        # 모든 소스 비활성화하여 빠른 테스트
        with patch('utils.si_plus.unified_collector.NaverCollector') as mock_naver:
            mock_naver_instance = MagicMock()
            mock_naver_instance.source_name = "naver"
            mock_naver_instance.collect = AsyncMock(return_value={
                "source": "naver",
                "ticker": "005930",
                "messages": [],
                "stats": {"total_messages": 0, "direct_count": 0, "theme_count": 0},
            })
            mock_naver.return_value = mock_naver_instance

            result = await collect_all_sources(
                ticker="005930",
                aliases=["삼성전자"],
                enable_reddit=False,
                enable_naver=True,
            )

        assert isinstance(result, dict)
        assert "ticker" in result

    def test_collect_all_sources_sync(self):
        """collect_all_sources_sync 동기 래퍼"""
        from utils.si_plus import collect_all_sources_sync

        with patch('utils.si_plus.unified_collector.collect_all_sources', new_callable=AsyncMock) as mock:
            mock.return_value = {"ticker": "005930", "stats": {}}

            result = collect_all_sources_sync(
                ticker="005930",
                enable_reddit=False,
                enable_naver=False,
            )

        assert isinstance(result, dict)
