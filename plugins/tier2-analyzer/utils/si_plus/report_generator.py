#!/usr/bin/env python3
"""SI+ 리포트 생성기

종목에 대한 멀티소스 센티먼트 리포트 생성
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트 기준 .env 로드
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path)

# cwd에서도 .env 로드 (fallback)
load_dotenv(Path.cwd() / ".env")

from .unified_collector import collect_all_sources
from .base import analyze_sentiment, get_sentiment_label


async def generate_report(
    ticker: str,
    stock_name: str,
    aliases: list,
    theme_keywords: list,
    output_dir: Path,
):
    """SI+ 리포트 생성"""

    print(f"\n{'='*60}")
    print(f"SI+ 리포트 생성: {stock_name} ({ticker})")
    print(f"{'='*60}")

    # config에서 텔레그램 채널 로드
    config_path = PROJECT_ROOT / "config" / "telegram_channels.json"
    with open(config_path) as f:
        config = json.load(f)

    telegram_channels = []
    channel_categories = {}
    for cat_name, cat_data in config["channels"].items():
        channels = cat_data.get("channels", [])
        telegram_channels.extend(channels)
        for ch in channels:
            channel_categories[ch] = {
                "category": cat_name,
                "reliability": cat_data.get("reliability", "medium"),
            }

    print(f"\n검색 조건:")
    print(f"  종목: {ticker} ({stock_name})")
    print(f"  별칭: {', '.join(aliases)}")
    print(f"  테마: {', '.join(theme_keywords)}")
    print(f"  Telegram 채널: {len(telegram_channels)}개")

    # 데이터 수집
    print(f"\n데이터 수집 중...")

    result = await collect_all_sources(
        ticker=ticker,
        aliases=aliases,
        theme_keywords=theme_keywords,
        telegram_channels=telegram_channels,
        enable_reddit=True,
        enable_naver=True,
        limit_per_source=100,
    )

    # 리포트 생성
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append(f"# {stock_name} ({ticker}) SI+ 센티먼트 리포트")
    lines.append("")
    lines.append(f"> 분석일: {now} KST | 모듈: utils/si_plus | 소스: Telegram, Reddit, Naver")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. 수집 요약
    lines.append("## 1. 수집 요약")
    lines.append("")
    lines.append("### 검색 조건")
    lines.append("")
    lines.append(f"| 항목 | 값 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 종목코드 | {ticker} |")
    lines.append(f"| 종목명 | {stock_name} |")
    lines.append(f"| 별칭 | {', '.join(aliases)} |")
    lines.append(f"| 테마 키워드 | {', '.join(theme_keywords)} |")
    lines.append("")

    # 소스별 수집 현황
    lines.append("### 소스별 수집 현황")
    lines.append("")
    lines.append("| 소스 | 수집량 | 직접 매칭 | 테마 매칭 |")
    lines.append("|------|--------|----------|----------|")

    stats = result.get("stats", {})
    by_source = stats.get("by_source", {})

    for source_result in result.get("sources", []):
        source = source_result.get("source", "unknown")
        s_stats = source_result.get("stats", {})
        total = s_stats.get("total_messages", 0)
        direct = s_stats.get("direct_count", 0)
        theme = s_stats.get("theme_count", 0)
        lines.append(f"| {source.capitalize()} | {total} | {direct} | {theme} |")

    total_msgs = stats.get("total_messages", 0)
    total_direct = stats.get("direct_count", 0)
    total_theme = stats.get("theme_count", 0)
    lines.append(f"| **합계** | **{total_msgs}** | **{total_direct}** | **{total_theme}** |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 2. 통합 센티먼트
    lines.append("## 2. 통합 센티먼트")
    lines.append("")

    combined = result.get("combined", {})
    sentiment = combined.get("sentiment", {})
    score = sentiment.get("score", 0)
    label = combined.get("sentiment_label", "N/A")

    lines.append(f"**센티먼트: {label}** (점수: {score:+.2f})")
    lines.append("")

    lines.append("| 구분 | 수량 | 비율 |")
    lines.append("|------|------|------|")

    bullish = sentiment.get("bullish_count", 0)
    bearish = sentiment.get("bearish_count", 0)
    neutral = sentiment.get("neutral_count", 0)
    total = sentiment.get("total_messages", 1)

    lines.append(f"| 상승 의견 | {bullish} | {bullish/total*100:.1f}% |")
    lines.append(f"| 하락 의견 | {bearish} | {bearish/total*100:.1f}% |")
    lines.append(f"| 중립 | {neutral} | {neutral/total*100:.1f}% |")

    rumor_ratio = stats.get("rumor_ratio", 0)
    lines.append(f"| 루머 비율 | - | {rumor_ratio:.1%} |")
    lines.append("")

    lines.append("### 센티먼트 기준")
    lines.append("")
    lines.append("| 점수 | 레이블 |")
    lines.append("|------|--------|")
    lines.append("| +0.3 이상 | Bullish |")
    lines.append("| -0.3 ~ +0.3 | Neutral |")
    lines.append("| -0.3 이하 | Bearish |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 3. 소스별 분석
    lines.append("## 3. 소스별 분석")
    lines.append("")

    for source_result in result.get("sources", []):
        source = source_result.get("source", "unknown")
        messages = source_result.get("messages", [])

        if not messages:
            continue

        s_sentiment = analyze_sentiment(messages)
        s_label = get_sentiment_label(s_sentiment["score"])

        lines.append(f"### {source.capitalize()}")
        lines.append("")
        lines.append(f"- **센티먼트**: {s_label} ({s_sentiment['score']:+.2f})")
        lines.append(f"- **메시지 수**: {len(messages)}개")
        lines.append(f"- **상승/하락/중립**: {s_sentiment['bullish_count']}/{s_sentiment['bearish_count']}/{s_sentiment['neutral_count']}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 4. 주요 상승 의견
    lines.append("## 4. 주요 상승 의견")
    lines.append("")

    top_bullish = sentiment.get("top_bullish", [])
    if top_bullish:
        for msg in top_bullish[:5]:
            source = msg.get("source", "unknown")
            text = msg.get("text", "")[:80]
            keywords = ", ".join(msg.get("keywords", []))
            lines.append(f"- [{source}] \"{text}...\"")
            lines.append(f"  - 키워드: {keywords}")
    else:
        lines.append("_상승 의견 없음_")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 5. 주요 하락 의견
    lines.append("## 5. 주요 하락 의견")
    lines.append("")

    top_bearish = sentiment.get("top_bearish", [])
    if top_bearish:
        for msg in top_bearish[:5]:
            source = msg.get("source", "unknown")
            text = msg.get("text", "")[:80]
            keywords = ", ".join(msg.get("keywords", []))
            lines.append(f"- [{source}] \"{text}...\"")
            lines.append(f"  - 키워드: {keywords}")
    else:
        lines.append("_하락 의견 없음_")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 6. 루머 체크
    lines.append("## 6. 루머 체크 (검증 필요)")
    lines.append("")

    rumors = combined.get("rumors", [])
    if rumors:
        for r in rumors[:5]:
            text = r.get("text", "")[:60]
            source = r.get("source", "unknown")
            lines.append(f"- [ ] [{source}] \"{text}...\"")
    else:
        lines.append("_감지된 루머 없음_")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 7. 테마 트렌드
    lines.append("## 7. 테마 트렌드")
    lines.append("")
    lines.append(f"검색된 테마 키워드: **{', '.join(theme_keywords)}**")
    lines.append("")

    # 테마별 메시지 카운트
    theme_counts = {}
    all_messages = combined.get("messages", [])
    for msg in all_messages:
        if msg.get("match_type") == "theme":
            kw = msg.get("matched_keyword", "기타")
            theme_counts[kw] = theme_counts.get(kw, 0) + 1

    if theme_counts:
        lines.append("| 테마 | 언급 수 |")
        lines.append("|------|---------|")
        for kw, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {kw} | {count} |")
    else:
        lines.append("_테마 키워드 매칭 없음 (직접 매칭만 존재)_")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 8. 샘플 메시지
    lines.append("## 8. 샘플 메시지 (최근 10개)")
    lines.append("")

    sample_messages = all_messages[:10]
    if sample_messages:
        for i, msg in enumerate(sample_messages, 1):
            source = msg.get("source", "unknown")
            date = msg.get("date", "N/A")
            text = msg.get("text", "")[:100]
            match_type = msg.get("match_type", "direct")
            matched = msg.get("matched_keyword", "")

            lines.append(f"**[{i}] {source.capitalize()}** - {date}")
            lines.append(f"- 매칭: {match_type} ({matched})")
            lines.append(f"- 내용: {text}...")
            lines.append("")
    else:
        lines.append("_수집된 메시지 없음_")

    lines.append("---")
    lines.append("")

    # 9. 종합 판단
    lines.append("## 9. 종합 판단")
    lines.append("")

    # 신뢰도 계산
    if rumor_ratio < 0.1:
        reliability = "High"
    elif rumor_ratio < 0.3:
        reliability = "Medium"
    else:
        reliability = "Low"

    lines.append(f"| 항목 | 판단 |")
    lines.append(f"|------|------|")
    lines.append(f"| **센티먼트** | {label} ({score:+.2f}) |")
    lines.append(f"| **신뢰도** | {reliability} (루머 {rumor_ratio:.1%}) |")
    lines.append(f"| **데이터 충분성** | {'충분' if total_msgs >= 10 else '부족'} ({total_msgs}개) |")
    lines.append("")

    # 주의사항
    warnings = []
    if total_msgs < 10:
        warnings.append("데이터 부족으로 신뢰도 낮음")
    if rumor_ratio > 0.2:
        warnings.append("루머 비율 높음, 검증 필요")
    if total_direct == 0:
        warnings.append("직접 매칭 없음 (테마 키워드만 매칭)")

    if warnings:
        lines.append("### 주의사항")
        lines.append("")
        for w in warnings:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by SI+ (Sentiment Intelligence Plus) Agent*")

    # 리포트 저장
    report_content = "\n".join(lines)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "SI_PLUS_REPORT.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n✅ 리포트 저장: {output_path}")

    return report_content


async def main():
    # 케이옥션 설정
    ticker = "102370"
    stock_name = "케이옥션"
    aliases = ["케이옥션", "K옥션", "K-Auction", "케이 옥션"]
    theme_keywords = [
        "토큰증권", "STO", "조각투자", "증권형토큰",
        "미술품투자", "대체투자", "NFT", "블록체인",
    ]

    output_dir = Path("/Users/michael/public_agents/tier2/케이옥션_102370")

    report = await generate_report(
        ticker=ticker,
        stock_name=stock_name,
        aliases=aliases,
        theme_keywords=theme_keywords,
        output_dir=output_dir,
    )

    print("\n" + "=" * 60)
    print("리포트 미리보기 (상단 50줄)")
    print("=" * 60)
    print("\n".join(report.split("\n")[:50]))


if __name__ == "__main__":
    asyncio.run(main())
