"""웹 스크래핑 유틸리티

네이버 금융 등에서 데이터를 추출하는 함수들
Playwright 결과를 후처리하거나 requests로 직접 스크래핑
"""
import re
from typing import Optional
import requests
from bs4 import BeautifulSoup


def get_naver_stock_info(ticker: str) -> Optional[dict]:
    """
    네이버 금융에서 종목 정보 스크래핑

    Args:
        ticker: 종목코드 (예: "048910")

    Returns:
        {
            "name": "대원미디어",
            "price": 7490,
            "change": -310,
            "change_pct": -3.97,
            "volume": 63512,
            "prev_close": 7800,
            "open": 7790,
            "high": 7850,
            "low": 7490,
            "market_cap": "XXX억",
            "per": 12.5,
            "pbr": 1.04,
            "foreign_ratio": 3.24
        }
        or None (실패 시)
    """
    try:
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        result = {}

        # 종목명
        wrap_company = soup.select_one("div.wrap_company h2 a")
        if wrap_company:
            result["name"] = wrap_company.text.strip()

        # 현재가
        no_today = soup.select_one("p.no_today span.blind")
        if no_today:
            result["price"] = _parse_number(no_today.text)

        # 전일대비
        no_exday = soup.select("p.no_exday span.blind")
        if len(no_exday) >= 2:
            change = _parse_number(no_exday[0].text)
            change_pct = _parse_float(no_exday[1].text.replace("%", ""))

            # 상승/하락 판단
            ico = soup.select_one("p.no_exday em")
            if ico and "down" in str(ico.get("class", [])):
                change = -change
                change_pct = -change_pct

            result["change"] = change
            result["change_pct"] = change_pct

        # 시세 테이블 (전일, 시가, 고가, 저가, 거래량)
        table = soup.select_one("table.no_info")
        if table:
            rows = table.select("tr")
            for row in rows:
                tds = row.select("td")
                for td in tds:
                    text = td.text.strip()
                    blind = td.select_one("span.blind")
                    if blind:
                        value = _parse_number(blind.text)
                        if "전일" in text:
                            result["prev_close"] = value
                        elif "시가" in text:
                            result["open"] = value
                        elif "고가" in text:
                            result["high"] = value
                        elif "저가" in text:
                            result["low"] = value
                        elif "거래량" in text:
                            result["volume"] = value

        # 투자정보 (시가총액, PER, PBR, 외국인비율)
        aside = soup.select_one("div.aside_invest_info")
        if aside:
            items = aside.select("tr")
            for item in items:
                th = item.select_one("th")
                td = item.select_one("td")
                if th and td:
                    label = th.text.strip()
                    value_elem = td.select_one("em") or td
                    value_text = value_elem.text.strip()

                    if "시가총액" in label:
                        result["market_cap"] = value_text
                    elif "PER" in label:
                        result["per"] = _parse_float(value_text)
                    elif "PBR" in label:
                        result["pbr"] = _parse_float(value_text)
                    elif "외국인" in label:
                        result["foreign_ratio"] = _parse_float(value_text.replace("%", ""))

        return result if result else None

    except Exception:
        return None


def get_naver_stock_news(ticker: str, limit: int = 5) -> Optional[list]:
    """
    네이버 금융에서 종목 뉴스 스크래핑

    Args:
        ticker: 종목코드
        limit: 최대 뉴스 개수

    Returns:
        [
            {"title": "...", "date": "01/08", "url": "..."},
            ...
        ]
        or None (실패 시)
    """
    try:
        url = f"https://finance.naver.com/item/news.naver?code={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        news_list = []
        items = soup.select("table.type5 tr")

        for item in items[:limit * 2]:  # 헤더 등 건너뛰기 위해 여유있게
            title_elem = item.select_one("td.title a")
            date_elem = item.select_one("td.date")

            if title_elem and date_elem:
                news_list.append({
                    "title": title_elem.text.strip(),
                    "date": date_elem.text.strip(),
                    "url": "https://finance.naver.com" + title_elem.get("href", "")
                })

                if len(news_list) >= limit:
                    break

        return news_list if news_list else None

    except Exception:
        return None


def get_naver_discussion(ticker: str, limit: int = 10) -> Optional[list]:
    """
    네이버 금융 종목토론방 스크래핑

    Args:
        ticker: 종목코드
        limit: 최대 게시글 개수

    Returns:
        [
            {"title": "...", "date": "01/08 10:21", "url": "..."},
            ...
        ]
        or None (실패 시)
    """
    try:
        url = f"https://finance.naver.com/item/board.naver?code={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        posts = []
        items = soup.select("table.type2 tr")

        for item in items:
            title_elem = item.select_one("td.title a")
            date_elem = item.select_one("td span.tah")

            if title_elem:
                date_text = date_elem.text.strip() if date_elem else ""
                posts.append({
                    "title": title_elem.text.strip(),
                    "date": date_text,
                    "url": "https://finance.naver.com" + title_elem.get("href", "")
                })

                if len(posts) >= limit:
                    break

        return posts if posts else None

    except Exception:
        return None


def clean_playwright_result(text: str) -> str:
    """
    Playwright 결과물 후처리 (크기 축소)

    Args:
        text: Playwright snapshot 텍스트

    Returns:
        정제된 텍스트 (크기 약 70-80% 감소)
    """
    # 1. [ref=eXXX] 제거
    text = re.sub(r'\[ref=e\d+\]', '', text)

    # 2. [cursor=pointer] 제거
    text = re.sub(r'\[cursor=\w+\]', '', text)

    # 3. 빈 괄호 정리
    text = re.sub(r'\[\s*\]', '', text)

    # 4. 연속 공백 정리
    text = re.sub(r'  +', ' ', text)

    # 5. 빈 줄 정리
    text = re.sub(r'\n\s*\n', '\n', text)

    return text.strip()


def _parse_number(text: str) -> int:
    """텍스트에서 숫자 추출 (콤마 제거)"""
    try:
        clean = re.sub(r'[^\d\-]', '', text)
        return int(clean) if clean else 0
    except:
        return 0


def _parse_float(text: str) -> float:
    """텍스트에서 실수 추출"""
    try:
        clean = re.sub(r'[^\d\.\-]', '', text)
        return float(clean) if clean else 0.0
    except:
        return 0.0
