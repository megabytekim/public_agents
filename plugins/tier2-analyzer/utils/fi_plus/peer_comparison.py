"""피어 비교 모듈

동종업계 밸류에이션 비교 기능
"""

import importlib.util
import logging
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Tier 1 utils 경로
TIER1_UTILS = Path(__file__).parent.parent.parent.parent / "stock-analyzer-advanced" / "utils"


def _load_tier1_module(module_name: str):
    """Tier 1 모듈 동적 로드"""
    module_path = TIER1_UTILS / f"{module_name}.py"
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"tier1_{module_name}", str(module_path))
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None


_web_scraper = _load_tier1_module("web_scraper")
_data_fetcher = _load_tier1_module("data_fetcher")

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


def get_peer_comparison(ticker: str, peers: List[str], include_sector_avg: bool = True) -> Optional[dict]:
    """피어 그룹 밸류에이션 비교"""
    try:
        target_info = get_naver_stock_info(ticker)
        target_name = get_ticker_name(ticker)
    except Exception as e:
        logger.error(f"Exception fetching ticker {ticker}: {e}")
        return None

    if not target_info:
        logger.warning(f"Failed to fetch stock info for ticker: {ticker}")
        return None

    target = {
        "ticker": ticker,
        "name": target_name or target_info.get("name"),
        "per": target_info.get("per"),
        "pbr": target_info.get("pbr"),
        "market_cap": target_info.get("market_cap"),
    }

    peer_data = []
    for peer_ticker in peers:
        try:
            peer_info = get_naver_stock_info(peer_ticker)
            peer_name = get_ticker_name(peer_ticker)
        except Exception as e:
            logger.error(f"Exception fetching peer ticker {peer_ticker}: {e}")
            continue

        if peer_info:
            peer_data.append({
                "ticker": peer_ticker,
                "name": peer_name or peer_info.get("name"),
                "per": peer_info.get("per"),
                "pbr": peer_info.get("pbr"),
                "market_cap": peer_info.get("market_cap"),
            })

    all_tickers = [ticker] + peers
    sector_avg = get_sector_average(all_tickers) if include_sector_avg else {}

    premium_discount = {}
    if sector_avg and target.get("per") and sector_avg.get("per") and sector_avg["per"] != 0:
        premium_discount["per"] = round((target["per"] - sector_avg["per"]) / sector_avg["per"] * 100, 1)
    if sector_avg and target.get("pbr") and sector_avg.get("pbr") and sector_avg["pbr"] != 0:
        premium_discount["pbr"] = round((target["pbr"] - sector_avg["pbr"]) / sector_avg["pbr"] * 100, 1)

    return {"target": target, "peers": peer_data, "sector_avg": sector_avg, "premium_discount": premium_discount}


def get_sector_average(tickers: List[str]) -> Optional[dict]:
    """종목 리스트의 평균 밸류에이션"""
    if not tickers:
        return None

    per_values, pbr_values = [], []

    for ticker in tickers:
        try:
            info = get_naver_stock_info(ticker)
        except Exception:
            continue

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
