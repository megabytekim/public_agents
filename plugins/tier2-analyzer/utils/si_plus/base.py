"""SI+ 공통 모듈

센티먼트 분석, 루머 분류 등 공통 기능
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict

# ============================================================
# 센티먼트 키워드
# ============================================================

BULLISH_KEYWORDS = [
    "급등", "상한가", "폭등", "대박", "상승", "매수", "추천", "목표가 상향",
    "호재", "돌파", "신고가", "기대", "좋아", "긍정", "오를", "상향",
    "강추", "존버", "가즈아", "풀매수", "물타기", "반등", "바닥",
    "저점", "매집", "슈팅", "떡상",
]

BEARISH_KEYWORDS = [
    "급락", "하한가", "폭락", "손절", "하락", "매도", "경고", "목표가 하향",
    "악재", "이탈", "신저가", "우려", "나빠", "부정", "내릴", "하향",
    "도망", "탈출", "물렸", "패닉", "투매", "고점", "떡락", "개미털기",
]

RUMOR_INDICATORS = [
    "카더라", "루머", "소문", "찌라시", "~일듯", "~할듯", "아마도",
    "추정", "예상", "들었는데", "한다더라", "~인듯", "~같음",
    "누가 그러는데", "확인 안됨", "비공식", "썰", "뇌피셜",
]

FACT_INDICATORS = [
    "공시", "IR", "발표", "확정", "공식", "보도", "기사", "뉴스",
    "실적", "결산", "분기", "사업보고서", "증권신고서", "확인됨",
    "금감원", "거래소", "공정위",
]

# ============================================================
# 스팸 필터링
# ============================================================

SPAM_PATTERNS = [
    # 대출/금융 스팸
    "대출", "대부", "캐피탈", "신용대출", "담보대출", "전세자금",
    "주택담보", "무직자대출", "급전", "일수", "사채",
    # 도박/성인 스팸
    "카지노", "바카라", "슬롯", "토토", "배팅", "도박",
    "성인", "19금", "출장", "마사지",
    # 홍보/광고 스팸
    "텔레그램 문의", "카톡 문의", "상담문의", "무료상담",
    "클릭", "가입하면", "이벤트 참여",
    # URL 패턴 (특정 광고성 URL)
    "fine-", "click-", "bit.ly", "tinyurl",
]


def is_spam(text: str) -> bool:
    """
    메시지가 스팸인지 판별

    Args:
        text: 메시지 텍스트

    Returns:
        스팸이면 True
    """
    text_lower = text.lower()
    for pattern in SPAM_PATTERNS:
        if pattern.lower() in text_lower:
            return True
    return False


def filter_spam(messages: List[dict]) -> List[dict]:
    """
    메시지 리스트에서 스팸 제거

    Args:
        messages: 메시지 리스트

    Returns:
        스팸 제거된 메시지 리스트
    """
    return [msg for msg in messages if not is_spam(msg.get("text", ""))]


# ============================================================
# 데이터 클래스
# ============================================================

@dataclass
class SentimentResult:
    """센티먼트 분석 결과"""
    score: float  # -1.0 ~ 1.0
    bullish_count: int
    bearish_count: int
    neutral_count: int
    total_messages: int
    top_bullish: List[dict]
    top_bearish: List[dict]

    @property
    def label(self) -> str:
        if self.score >= 0.3:
            return "Bullish"
        elif self.score <= -0.3:
            return "Bearish"
        return "Neutral"


# ============================================================
# 기본 수집기 인터페이스
# ============================================================

class BaseCollector(ABC):
    """수집기 기본 클래스"""

    source_name: str = "unknown"

    @abstractmethod
    async def collect(
        self,
        ticker: str,
        aliases: Optional[List[str]] = None,
        theme_keywords: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict:
        """
        메시지 수집

        Args:
            ticker: 종목코드
            aliases: 종목 별칭
            theme_keywords: 테마 키워드

        Returns:
            {
                "source": str,
                "ticker": str,
                "messages": List[dict],
                "stats": dict,
            }
        """
        pass


# ============================================================
# 공통 분석 함수
# ============================================================

def analyze_sentiment(messages: List[dict], prioritize_direct: bool = True) -> dict:
    """
    메시지에서 센티먼트 분석

    Args:
        messages: 메시지 리스트
        prioritize_direct: True면 top_bullish/bearish에서 직접 매칭 우선

    Returns:
        센티먼트 분석 결과
    """
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0

    # 직접 매칭과 테마 매칭 분리
    direct_bullish = []
    direct_bearish = []
    theme_bullish = []
    theme_bearish = []

    for msg in messages:
        text = msg.get("text", "")
        match_type = msg.get("match_type", "direct")

        bull_hits = sum(1 for kw in BULLISH_KEYWORDS if kw in text)
        bear_hits = sum(1 for kw in BEARISH_KEYWORDS if kw in text)

        entry = {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "date": msg.get("date"),
            "source": msg.get("source", "unknown"),
            "match_type": match_type,
            "matched_keyword": msg.get("matched_keyword", ""),
            "keywords": [],
        }

        if bull_hits > bear_hits:
            bullish_count += 1
            entry["keywords"] = [kw for kw in BULLISH_KEYWORDS if kw in text]
            if match_type == "direct":
                direct_bullish.append(entry)
            else:
                theme_bullish.append(entry)
        elif bear_hits > bull_hits:
            bearish_count += 1
            entry["keywords"] = [kw for kw in BEARISH_KEYWORDS if kw in text]
            if match_type == "direct":
                direct_bearish.append(entry)
            else:
                theme_bearish.append(entry)
        else:
            neutral_count += 1

    # top 선택: 직접 매칭 우선, 부족하면 테마로 채움
    if prioritize_direct:
        top_bullish = direct_bullish[:5]
        if len(top_bullish) < 5:
            top_bullish.extend(theme_bullish[:5 - len(top_bullish)])
        top_bearish = direct_bearish[:5]
        if len(top_bearish) < 5:
            top_bearish.extend(theme_bearish[:5 - len(top_bearish)])
    else:
        top_bullish = (direct_bullish + theme_bullish)[:5]
        top_bearish = (direct_bearish + theme_bearish)[:5]

    total = len(messages)
    score = (bullish_count - bearish_count) / total if total > 0 else 0.0

    return {
        "score": round(score, 3),
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": neutral_count,
        "total_messages": total,
        "top_bullish": top_bullish,
        "top_bearish": top_bearish,
    }


def classify_rumor(text: str) -> dict:
    """
    메시지를 루머 vs 팩트로 분류

    Args:
        text: 메시지 텍스트

    Returns:
        분류 결과
    """
    rumor_hits = [ind for ind in RUMOR_INDICATORS if ind in text]
    fact_hits = [ind for ind in FACT_INDICATORS if ind in text]

    rumor_score = len(rumor_hits)
    fact_score = len(fact_hits)
    total = rumor_score + fact_score

    if total == 0:
        return {
            "is_rumor": False,
            "confidence": 0.5,
            "indicators": [],
        }

    fact_ratio = fact_score / total

    return {
        "is_rumor": fact_ratio < 0.5,
        "confidence": max(fact_ratio, 1 - fact_ratio),
        "indicators": {
            "rumor": rumor_hits,
            "fact": fact_hits,
        },
    }


def get_sentiment_label(score: float) -> str:
    """센티먼트 점수를 레이블로 변환"""
    if score >= 0.3:
        return "Bullish"
    elif score <= -0.3:
        return "Bearish"
    return "Neutral"


def format_unified_report(
    ticker: str,
    results: List[dict],
    aliases: Optional[List[str]] = None,
    theme_keywords: Optional[List[str]] = None,
) -> str:
    """
    여러 소스의 결과를 통합 리포트로 포맷

    Args:
        ticker: 종목코드
        results: 각 소스별 수집 결과 리스트
        aliases: 종목 별칭
        theme_keywords: 테마 키워드

    Returns:
        마크다운 리포트
    """
    lines = []
    lines.append(f"# SI+ 통합 센티먼트 리포트: {ticker}")
    lines.append("")

    if aliases:
        lines.append(f"**검색어**: {', '.join(aliases)}")
    if theme_keywords:
        lines.append(f"**테마 키워드**: {', '.join(theme_keywords[:5])}...")
    lines.append("")

    # 소스별 요약
    lines.append("## 소스별 수집 현황")
    lines.append("")
    lines.append("| 소스 | 메시지 수 | 직접 | 테마 |")
    lines.append("|------|----------|------|------|")

    all_messages = []
    for result in results:
        source = result.get("source", "unknown")
        stats = result.get("stats", {})
        total = stats.get("total_messages", 0)
        direct = stats.get("direct_count", 0)
        theme = stats.get("theme_count", 0)
        lines.append(f"| {source} | {total} | {direct} | {theme} |")
        all_messages.extend(result.get("messages", []))

    total_msgs = len(all_messages)
    total_direct = sum(r.get("stats", {}).get("direct_count", 0) for r in results)
    total_theme = sum(r.get("stats", {}).get("theme_count", 0) for r in results)
    lines.append(f"| **합계** | **{total_msgs}** | **{total_direct}** | **{total_theme}** |")
    lines.append("")

    # 통합 센티먼트
    if all_messages:
        sentiment = analyze_sentiment(all_messages)
        label = get_sentiment_label(sentiment["score"])

        lines.append("## 통합 센티먼트")
        lines.append("")
        lines.append(f"**{label}** (점수: {sentiment['score']:+.2f})")
        lines.append("")
        lines.append("| 구분 | 수량 | 비율 |")
        lines.append("|------|------|------|")

        total = sentiment["total_messages"]
        for cat, count in [
            ("상승", sentiment["bullish_count"]),
            ("하락", sentiment["bearish_count"]),
            ("중립", sentiment["neutral_count"]),
        ]:
            pct = count / total * 100 if total > 0 else 0
            lines.append(f"| {cat} | {count} | {pct:.1f}% |")
        lines.append("")

        # 주요 의견
        if sentiment["top_bullish"]:
            lines.append("### 주요 상승 의견")
            lines.append("")
            for msg in sentiment["top_bullish"]:
                lines.append(f"- [{msg.get('source', '')}] {msg['text']}")
                lines.append(f"  - 키워드: {', '.join(msg.get('keywords', []))}")
            lines.append("")

        if sentiment["top_bearish"]:
            lines.append("### 주요 하락 의견")
            lines.append("")
            for msg in sentiment["top_bearish"]:
                lines.append(f"- [{msg.get('source', '')}] {msg['text']}")
                lines.append(f"  - 키워드: {', '.join(msg.get('keywords', []))}")
            lines.append("")

    return "\n".join(lines)
