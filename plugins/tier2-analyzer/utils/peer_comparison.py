"""피어 비교 유틸리티

동종업계 밸류에이션 비교 기능
"""
import importlib.util
from typing import Optional, List
from pathlib import Path

# Tier 1 utils 경로 (절대 경로 사용)
TIER1_UTILS = Path(__file__).parent.parent.parent / "stock-analyzer-advanced" / "utils"


def _load_tier1_module(module_name: str):
    """Tier 1 모듈을 절대 경로에서 동적 로드 (모듈 충돌 방지)"""
    module_path = TIER1_UTILS / f"{module_name}.py"
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        f"tier1_{module_name}", str(module_path)
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None


# Tier 1 모듈 로드
_web_scraper = _load_tier1_module("web_scraper")
_data_fetcher = _load_tier1_module("data_fetcher")

# 함수 바인딩 (없으면 None 반환 스텁)
if _web_scraper and hasattr(_web_scraper, "get_naver_stock_info"):
    get_naver_stock_info = _web_scraper.get_naver_stock_info
else:
    def get_naver_stock_info(ticker):
        return None

if _data_fetcher and hasattr(_data_fetcher, "get_ticker_name"):
    get_ticker_name = _data_fetcher.get_ticker_name
else:
    def get_ticker_name(ticker):
        return None


def get_peer_comparison(
    ticker: str,
    peers: List[str],
    include_sector_avg: bool = True
) -> Optional[dict]:
    """
    피어 그룹 밸류에이션 비교

    Args:
        ticker: 대상 종목코드
        peers: 비교 대상 종목코드 리스트
        include_sector_avg: 섹터 평균 포함 여부

    Returns:
        {
            "target": {
                "ticker": "377300",
                "name": "카카오페이",
                "per": 33.17,
                "pbr": 3.55,
                "market_cap": "6.72조"
            },
            "peers": [
                {"ticker": "035420", "name": "네이버", "per": 28.5, ...},
                ...
            ],
            "sector_avg": {
                "per": 30.2,
                "pbr": 3.1
            },
            "premium_discount": {
                "per": 10.0,  # 섹터 대비 10% 프리미엄
                "pbr": 14.5
            }
        }
    """
    # 타겟 종목 정보
    target_info = get_naver_stock_info(ticker)
    target_name = get_ticker_name(ticker)

    if not target_info:
        return None

    target = {
        "ticker": ticker,
        "name": target_name or target_info.get("name"),
        "per": target_info.get("per"),
        "pbr": target_info.get("pbr"),
        "market_cap": target_info.get("market_cap"),
    }

    # 피어 종목 정보 수집
    peer_data = []
    for peer_ticker in peers:
        peer_info = get_naver_stock_info(peer_ticker)
        peer_name = get_ticker_name(peer_ticker)

        if peer_info:
            peer_data.append({
                "ticker": peer_ticker,
                "name": peer_name or peer_info.get("name"),
                "per": peer_info.get("per"),
                "pbr": peer_info.get("pbr"),
                "market_cap": peer_info.get("market_cap"),
            })

    # 섹터 평균 계산
    all_tickers = [ticker] + peers
    sector_avg = get_sector_average(all_tickers) if include_sector_avg else {}

    # 프리미엄/디스카운트 계산
    premium_discount = {}
    if sector_avg and target.get("per") and sector_avg.get("per"):
        premium_discount["per"] = round(
            (target["per"] - sector_avg["per"]) / sector_avg["per"] * 100, 1
        )
    if sector_avg and target.get("pbr") and sector_avg.get("pbr"):
        premium_discount["pbr"] = round(
            (target["pbr"] - sector_avg["pbr"]) / sector_avg["pbr"] * 100, 1
        )

    return {
        "target": target,
        "peers": peer_data,
        "sector_avg": sector_avg,
        "premium_discount": premium_discount,
    }


def get_sector_average(tickers: List[str]) -> Optional[dict]:
    """
    종목 리스트의 평균 밸류에이션 계산

    Args:
        tickers: 종목코드 리스트

    Returns:
        {"per": 평균 PER, "pbr": 평균 PBR}
        or None (빈 리스트 시)
    """
    if not tickers:
        return None

    per_values = []
    pbr_values = []

    for ticker in tickers:
        info = get_naver_stock_info(ticker)
        if info:
            if info.get("per"):
                per_values.append(info["per"])
            if info.get("pbr"):
                pbr_values.append(info["pbr"])

    result = {}
    if per_values:
        result["per"] = round(sum(per_values) / len(per_values), 2)
    if pbr_values:
        result["pbr"] = round(sum(pbr_values) / len(pbr_values), 2)

    return result if result else None


def format_peer_table(comparison: dict) -> str:
    """
    피어 비교 결과를 마크다운 테이블로 포맷

    Args:
        comparison: get_peer_comparison() 결과

    Returns:
        마크다운 테이블 문자열
    """
    if not comparison:
        return "데이터 없음"

    lines = []
    lines.append("| 종목 | 시총 | PER | PBR |")
    lines.append("|------|------|-----|-----|")

    # 타겟
    t = comparison.get("target", {})
    lines.append(f"| **{t.get('name', '-')}** | {t.get('market_cap', '-')} | {t.get('per', '-')}x | {t.get('pbr', '-')}x |")

    # 피어
    for p in comparison.get("peers", []):
        lines.append(f"| {p.get('name', '-')} | {p.get('market_cap', '-')} | {p.get('per', '-')}x | {p.get('pbr', '-')}x |")

    # 섹터 평균
    avg = comparison.get("sector_avg", {})
    if avg:
        lines.append(f"| **섹터 평균** | - | **{avg.get('per', '-')}x** | **{avg.get('pbr', '-')}x** |")

    return "\n".join(lines)


if __name__ == "__main__":
    import json
    result = get_peer_comparison("377300", ["035420", "035720"])
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    print("\n" + format_peer_table(result))
