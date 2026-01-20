"""Reddit 수집기

Reddit API를 사용한 서브레딧 게시물/댓글 수집
- 무료 API (rate limit 있음)
- 인증 없이 public 데이터 접근 가능
"""
import time
import requests
from typing import Optional, List, Dict

from .base import BaseCollector

# Reddit API 설정
BASE_URL = "https://www.reddit.com"
USER_AGENT = "SI-Plus-Collector/1.0"

# 한국 주식 관련 서브레딧
DEFAULT_SUBREDDITS = [
    "korea_stock",      # 한국 주식
    "korea",            # 한국 전반
    "hanguk",           # 한국어 커뮤니티
]


class RedditCollector(BaseCollector):
    """Reddit 수집기"""

    source_name = "reddit"

    def __init__(self, subreddits: Optional[List[str]] = None):
        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def search_subreddit(
        self,
        subreddit: str,
        query: str,
        limit: int = 50,
        sort: str = "relevance",  # relevance, hot, top, new
        time_filter: str = "month",  # hour, day, week, month, year, all
    ) -> List[dict]:
        """
        서브레딧에서 키워드 검색

        Args:
            subreddit: 서브레딧 이름
            query: 검색 쿼리
            limit: 최대 결과 수
            sort: 정렬 방식
            time_filter: 시간 필터

        Returns:
            검색 결과 리스트
        """
        url = f"{BASE_URL}/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "true",  # 해당 서브레딧만 검색
            "limit": min(limit, 100),  # Reddit API 최대 100
            "sort": sort,
            "t": time_filter,
        }

        messages = []

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})

                # 게시물 정보 추출
                messages.append({
                    "id": post_data.get("id"),
                    "text": f"{post_data.get('title', '')} {post_data.get('selftext', '')}",
                    "title": post_data.get("title"),
                    "date": self._timestamp_to_str(post_data.get("created_utc", 0)),
                    "score": post_data.get("score", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "source": "reddit",
                    "subreddit": subreddit,
                    "author": post_data.get("author"),
                })

            # Rate limiting (Reddit은 1초에 1요청 권장)
            time.sleep(1)

        except Exception as e:
            print(f"[Reddit] Error searching '{query}' in r/{subreddit}: {e}")

        return messages

    def search_all(
        self,
        query: str,
        limit: int = 50,
        time_filter: str = "month",
    ) -> List[dict]:
        """
        전체 Reddit에서 검색 (특정 서브레딧 제한 없이)

        Args:
            query: 검색 쿼리
            limit: 최대 결과 수
            time_filter: 시간 필터

        Returns:
            검색 결과 리스트
        """
        url = f"{BASE_URL}/search.json"
        params = {
            "q": query,
            "limit": min(limit, 100),
            "sort": "relevance",
            "t": time_filter,
        }

        messages = []

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})

                messages.append({
                    "id": post_data.get("id"),
                    "text": f"{post_data.get('title', '')} {post_data.get('selftext', '')}",
                    "title": post_data.get("title"),
                    "date": self._timestamp_to_str(post_data.get("created_utc", 0)),
                    "score": post_data.get("score", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "source": "reddit",
                    "subreddit": post_data.get("subreddit"),
                    "author": post_data.get("author"),
                })

            time.sleep(1)

        except Exception as e:
            print(f"[Reddit] Error in global search for '{query}': {e}")

        return messages

    async def collect(
        self,
        ticker: str,
        aliases: Optional[List[str]] = None,
        theme_keywords: Optional[List[str]] = None,
        limit_per_keyword: int = 30,
    ) -> Dict:
        """
        Reddit에서 종목 관련 게시물 수집

        Args:
            ticker: 종목코드
            aliases: 종목 별칭
            theme_keywords: 테마 키워드
            limit_per_keyword: 키워드당 최대 게시물 수

        Returns:
            수집 결과
        """
        # 검색 키워드 구성
        direct_keywords = [ticker]
        if aliases:
            direct_keywords.extend(aliases)

        all_keywords = direct_keywords.copy()
        if theme_keywords:
            all_keywords.extend(theme_keywords)

        all_messages = []
        seen_ids = set()
        keyword_stats = {}

        for keyword in all_keywords:
            # 전체 Reddit 검색 (한국 주식은 여러 서브레딧에 분산)
            messages = self.search_all(
                query=keyword,
                limit=limit_per_keyword,
                time_filter="month",
            )

            # 중복 제거
            new_messages = []
            for msg in messages:
                if msg["id"] not in seen_ids:
                    msg["match_type"] = "direct" if keyword in direct_keywords else "theme"
                    msg["matched_keyword"] = keyword
                    new_messages.append(msg)
                    seen_ids.add(msg["id"])

            keyword_stats[keyword] = len(messages)
            all_messages.extend(new_messages)

        # 점수순 정렬
        all_messages.sort(key=lambda x: x.get("score", 0), reverse=True)

        return {
            "source": "reddit",
            "ticker": ticker,
            "messages": all_messages,
            "stats": {
                "total_messages": len(all_messages),
                "by_keyword": keyword_stats,
                "direct_count": len([m for m in all_messages if m.get("match_type") == "direct"]),
                "theme_count": len([m for m in all_messages if m.get("match_type") == "theme"]),
            },
        }

    @staticmethod
    def _timestamp_to_str(timestamp: float) -> str:
        """Unix timestamp를 문자열로 변환"""
        from datetime import datetime
        try:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except:
            return ""


# 동기 래퍼 함수
def search_reddit(
    query: str,
    subreddits: Optional[List[str]] = None,
    limit: int = 50,
) -> List[dict]:
    """
    Reddit 검색 (동기)

    Args:
        query: 검색 쿼리
        subreddits: 검색할 서브레딧 리스트 (None이면 전체)
        limit: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    collector = RedditCollector(subreddits)

    if subreddits:
        all_results = []
        for subreddit in subreddits:
            results = collector.search_subreddit(subreddit, query, limit=limit)
            all_results.extend(results)
        return all_results
    else:
        return collector.search_all(query, limit=limit)
