"""네이버 수집기

네이버 금융 종토방(토론방) 수집 (웹 스크래핑)
- 종목별 토론방
- 뉴스 댓글
"""
import re
import time
import requests
from typing import Optional, List, Dict
from bs4 import BeautifulSoup

from .base import BaseCollector

# 네이버 금융 설정
FINANCE_URL = "https://finance.naver.com"
MOBILE_URL = "https://m.stock.naver.com"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


class NaverCollector(BaseCollector):
    """네이버 금융 수집기"""

    source_name = "naver"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "ko-KR,ko;q=0.9",
        })

    def get_discussion_board(
        self,
        ticker: str,
        limit: int = 50,
    ) -> List[dict]:
        """
        종목 토론방 게시물 수집

        Args:
            ticker: 종목코드 (6자리)
            limit: 최대 게시물 수

        Returns:
            게시물 리스트
        """
        messages = []
        page = 1
        max_pages = (limit // 20) + 1

        while len(messages) < limit and page <= max_pages:
            try:
                url = f"{FINANCE_URL}/item/board.naver"
                params = {
                    "code": ticker,
                    "page": page,
                }

                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # 토론방 게시물 파싱
                table = soup.select_one("table.type2")
                if not table:
                    break

                rows = table.select("tbody tr")

                for row in rows:
                    try:
                        # 제목/날짜/조회수 등이 없는 구분선 행 건너뛰기
                        cols = row.select("td")
                        if len(cols) < 5:
                            continue

                        # 제목
                        title_elem = row.select_one("td.title a")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        href = title_elem.get("href", "")

                        # 날짜
                        date_elem = cols[0]
                        date = date_elem.get_text(strip=True)

                        # 조회수
                        view_elem = cols[3]
                        views = self._parse_number(view_elem.get_text(strip=True))

                        # 공감/비공감
                        good_elem = cols[4]
                        good = self._parse_number(good_elem.get_text(strip=True))

                        messages.append({
                            "id": self._extract_post_id(href),
                            "text": title,
                            "title": title,
                            "date": self._normalize_date(date),
                            "views": views,
                            "score": good,  # 공감 수를 score로 사용
                            "url": f"{FINANCE_URL}{href}" if href.startswith("/") else href,
                            "source": "naver",
                            "ticker": ticker,
                        })

                    except Exception as e:
                        continue

                page += 1
                time.sleep(0.3)

            except Exception as e:
                print(f"[Naver] Error fetching discussion board for {ticker}: {e}")
                break

        return messages[:limit]

    def search_discussions(
        self,
        query: str,
        ticker: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """
        종토방 검색 (키워드 기반)

        Note: 네이버 종토방은 종목별로 분리되어 있어서
              특정 키워드 검색이 제한적입니다.
              ticker가 주어지면 해당 종목 토론방에서 필터링합니다.

        Args:
            query: 검색 쿼리
            ticker: 종목코드 (선택)
            limit: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        if ticker:
            # 종목 토론방에서 키워드 필터링
            all_posts = self.get_discussion_board(ticker, limit=limit * 2)
            return [
                post for post in all_posts
                if query.lower() in post.get("title", "").lower()
            ][:limit]
        else:
            # 종목코드 없이는 검색 불가
            return []

    async def collect(
        self,
        ticker: str,
        aliases: Optional[List[str]] = None,
        theme_keywords: Optional[List[str]] = None,
        limit_per_keyword: int = 50,
    ) -> Dict:
        """
        네이버 금융에서 종목 관련 게시물 수집

        Args:
            ticker: 종목코드
            aliases: 종목 별칭 (사용 안 함 - 네이버는 종목코드 기반)
            theme_keywords: 테마 키워드 (종토방 내 필터링용)
            limit_per_keyword: 키워드당 최대 게시물 수

        Returns:
            수집 결과
        """
        all_messages = []

        # 1. 종목 토론방 전체 게시물
        board_posts = self.get_discussion_board(ticker, limit=limit_per_keyword)

        for post in board_posts:
            post["match_type"] = "direct"
            post["matched_keyword"] = ticker

        all_messages.extend(board_posts)

        # 2. 테마 키워드로 필터링 (선택)
        theme_matches = []
        if theme_keywords:
            for keyword in theme_keywords:
                for post in board_posts:
                    if keyword in post.get("title", ""):
                        theme_post = post.copy()
                        theme_post["match_type"] = "theme"
                        theme_post["matched_keyword"] = keyword
                        theme_matches.append(theme_post)

        return {
            "source": "naver",
            "ticker": ticker,
            "messages": all_messages,
            "stats": {
                "total_messages": len(all_messages),
                "direct_count": len(board_posts),
                "theme_count": len(theme_matches),
                "theme_matches": theme_matches,  # 테마 매칭된 것들 별도 제공
            },
        }

    @staticmethod
    def _extract_post_id(url: str) -> str:
        """URL에서 게시물 ID 추출"""
        match = re.search(r"nid=(\d+)", url)
        return match.group(1) if match else url

    @staticmethod
    def _parse_number(text: str) -> int:
        """숫자 문자열 파싱"""
        try:
            return int(text.replace(",", ""))
        except:
            return 0

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """날짜 문자열 정규화"""
        # 네이버 날짜 형식: "2024.01.15 12:30", "01.15 12:30" 등
        from datetime import date

        date_str = date_str.strip()

        # MM.DD HH:MM 형식
        if re.match(r"^\d{2}\.\d{2}\s+\d{2}:\d{2}$", date_str):
            year = date.today().year
            parts = date_str.split()
            return f"{year}-{parts[0].replace('.', '-')} {parts[1]}:00"

        # YYYY.MM.DD HH:MM 형식
        if re.match(r"^\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}$", date_str):
            parts = date_str.split()
            return f"{parts[0].replace('.', '-')} {parts[1]}:00"

        return date_str


# 동기 래퍼 함수
def get_naver_discussions(
    ticker: str,
    limit: int = 50,
) -> List[dict]:
    """
    네이버 종토방 게시물 가져오기 (동기)

    Args:
        ticker: 종목코드
        limit: 최대 게시물 수

    Returns:
        게시물 리스트
    """
    collector = NaverCollector()
    return collector.get_discussion_board(ticker, limit=limit)
