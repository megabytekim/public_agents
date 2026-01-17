# plugins/tier2-analyzer/tests/test_peer_comparison.py
"""피어 비교 기능 테스트"""
import pytest


class TestGetPeerComparison:
    """get_peer_comparison() 함수 테스트"""

    def test_returns_comparison_table(self):
        """비교 테이블 반환 확인"""
        from utils.peer_comparison import get_peer_comparison

        # 카카오페이와 피어 비교
        result = get_peer_comparison(
            ticker="377300",
            peers=["035420", "035720"]  # 네이버, 카카오
        )

        assert result is not None
        assert "target" in result
        assert "peers" in result
        assert "sector_avg" in result

    def test_calculates_premium_discount(self):
        """프리미엄/디스카운트 계산 확인"""
        from utils.peer_comparison import get_peer_comparison

        result = get_peer_comparison(
            ticker="377300",
            peers=["035420"]
        )

        assert result is not None
        assert "premium_discount" in result
        # PER 기준 프리미엄/디스카운트 (%)
        assert isinstance(result["premium_discount"].get("per"), (int, float, type(None)))


class TestGetSectorAverage:
    """get_sector_average() 함수 테스트"""

    def test_returns_sector_metrics(self):
        """섹터 평균 지표 반환"""
        from utils.peer_comparison import get_sector_average

        result = get_sector_average(tickers=["377300", "035420", "035720"])

        assert result is not None
        assert "avg_per" in result or "per" in result
