"""SI+ 컨텍스트 추출기

기존 분석 파일에서 센티먼트 검색에 필요한 컨텍스트 추출
"""

import re
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class StockContext:
    """종목 분석 컨텍스트"""
    ticker: str
    stock_name: str
    aliases: List[str]
    business_keywords: List[str]  # 사업 관련 키워드
    theme_keywords: List[str]  # 테마/이슈 키워드
    risk_keywords: List[str]  # 리스크 관련 키워드
    summary: str  # 핵심 요약


def extract_context_from_analysis(file_path: Path) -> Optional[StockContext]:
    """
    stock_analyzer_summary.md 파일에서 컨텍스트 추출

    Args:
        file_path: 분석 파일 경로

    Returns:
        StockContext 또는 None
    """
    if not file_path.exists():
        return None

    content = file_path.read_text(encoding="utf-8")

    # 1. 기본 정보 추출
    ticker = _extract_ticker(content)
    stock_name = _extract_stock_name(content)

    # 2. 사업 키워드 추출
    business_keywords = _extract_business_keywords(content)

    # 3. 테마 키워드 추출
    theme_keywords = _extract_theme_keywords(content)

    # 4. 리스크 키워드 추출
    risk_keywords = _extract_risk_keywords(content)

    # 5. 별칭 생성
    aliases = _generate_aliases(stock_name, ticker)

    # 6. 핵심 요약 추출
    summary = _extract_summary(content)

    return StockContext(
        ticker=ticker,
        stock_name=stock_name,
        aliases=aliases,
        business_keywords=business_keywords,
        theme_keywords=theme_keywords,
        risk_keywords=risk_keywords,
        summary=summary,
    )


def _extract_ticker(content: str) -> str:
    """종목코드 추출"""
    # # 케이옥션 (102370) Analysis
    match = re.search(r'#\s+\S+\s+\((\d{6})\)', content)
    if match:
        return match.group(1)
    return ""


def _extract_stock_name(content: str) -> str:
    """종목명 추출"""
    match = re.search(r'#\s+(\S+)\s+\(\d{6}\)', content)
    if match:
        return match.group(1)
    return ""


def _extract_business_keywords(content: str) -> List[str]:
    """사업 관련 키워드 추출"""
    keywords = set()

    # 기업 개요 섹션에서 추출
    overview_match = re.search(r'### 기업 개요.*?(?=###|\Z)', content, re.DOTALL)
    if overview_match:
        overview = overview_match.group(0)

        # 사업 내용에서 핵심어 추출
        business_match = re.search(r'\*\*사업 내용\*\*:\s*(.+)', overview)
        if business_match:
            # "미술품 경매 중개 서비스" -> ["미술품", "경매"]
            text = business_match.group(1)
            keywords.update(_extract_nouns(text))

        # 주요 제품에서 추출
        products = re.findall(r'-\s+([^()\n]+)', overview)
        for product in products:
            keywords.update(_extract_nouns(product))

    # 산업 동향에서 추출
    sector_match = re.search(r'### 산업 동향.*?(?=###|\Z)', content, re.DOTALL)
    if sector_match:
        sector = sector_match.group(0)
        # 성장 드라이버에서 추출
        drivers = re.findall(r'\d+\.\s+(.+?)(?:\(|$)', sector)
        for driver in drivers:
            keywords.update(_extract_nouns(driver))

    return list(keywords)[:15]  # 최대 15개


def _extract_theme_keywords(content: str) -> List[str]:
    """테마/이슈 키워드 추출"""
    keywords = set()

    # 뉴스 섹션에서 테마 추출
    news_match = re.search(r'### 최신 뉴스.*?(?=###|\Z)', content, re.DOTALL)
    if news_match:
        news = news_match.group(0)

        # 전략적 의미에서 키워드 추출
        meanings = re.findall(r'전략적 의미:\s*(.+)', news)
        for meaning in meanings:
            keywords.update(_extract_nouns(meaning))

    # Tags에서 추출
    tags_match = re.search(r'\*Tags:\s*(.+)\*', content)
    if tags_match:
        tags = tags_match.group(1)
        keywords.update(re.findall(r'#(\w+)', tags))

    # 투자 테마 패턴 매칭
    theme_patterns = [
        r'(토큰증권|STO|조각투자|NFT|블록체인)',
        r'(ESG|친환경|신재생|2차전지|반도체|AI|메타버스)',
        r'(턴어라운드|구조조정|M&A|IPO)',
    ]
    for pattern in theme_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        keywords.update(m.upper() if len(m) <= 3 else m for m in matches)

    return list(keywords)[:10]


def _extract_risk_keywords(content: str) -> List[str]:
    """리스크 관련 키워드 추출"""
    keywords = set()

    # 리스크 섹션에서 추출
    risk_match = re.search(r'## \d+\. 리스크.*?(?=##|\Z)', content, re.DOTALL)
    if risk_match:
        risk = risk_match.group(0)

        # 각 리스크 항목에서 핵심어 추출
        items = re.findall(r'\*\*(.+?)\*\*:', risk)
        keywords.update(items)

    # Bearish 의견에서 추출
    bearish_match = re.search(r'\*\*Bearish\*\*:.*?(?=\*\*|\Z)', content, re.DOTALL)
    if bearish_match:
        bearish = bearish_match.group(0)
        points = re.findall(r'-\s+(.+)', bearish)
        for point in points:
            keywords.update(_extract_nouns(point)[:2])

    return list(keywords)[:10]


def _extract_nouns(text: str) -> List[str]:
    """텍스트에서 명사 추출 (간단 버전)"""
    # 한글 단어 추출 (2글자 이상)
    words = re.findall(r'[가-힣]{2,}', text)

    # 불용어 제거
    stopwords = {
        '이다', '있다', '하다', '되다', '수준', '정도', '경우', '중심',
        '기반', '통한', '위한', '관련', '등', '및', '의', '에서',
        '으로', '부터', '까지', '에게', '대한', '아닌', '같은',
    }

    return [w for w in words if w not in stopwords]


def _generate_aliases(stock_name: str, ticker: str) -> List[str]:
    """종목 별칭 생성"""
    aliases = [stock_name]

    # 한글 줄임말 패턴
    if len(stock_name) > 2:
        # 케이옥션 -> 케옥
        aliases.append(stock_name[0] + stock_name[-1])

    # 영문 변환 (케이옥션 -> K-Auction)
    if '케이' in stock_name:
        aliases.append(stock_name.replace('케이', 'K'))
        aliases.append(stock_name.replace('케이', 'K-'))

    return aliases


def _extract_summary(content: str) -> str:
    """핵심 요약 추출"""
    # 최종 요약 섹션에서 추출
    summary_match = re.search(r'### 최종 요약\n(.+?)(?=\n\*\*|\Z)', content, re.DOTALL)
    if summary_match:
        return summary_match.group(1).strip()

    # 결론 섹션에서 추출
    conclusion_match = re.search(r'## \d+\. 결론.*?(?=##|\Z)', content, re.DOTALL)
    if conclusion_match:
        return conclusion_match.group(0)[:500]

    return ""


def context_to_search_config(ctx: StockContext) -> Dict:
    """
    StockContext를 SI+ 검색 설정으로 변환

    Returns:
        collect_all_sources()에 전달할 설정
    """
    return {
        "ticker": ctx.ticker,
        "aliases": ctx.aliases,
        "theme_keywords": list(set(ctx.business_keywords + ctx.theme_keywords)),
    }
