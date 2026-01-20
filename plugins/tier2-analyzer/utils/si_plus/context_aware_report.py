"""SI+ Context-Aware 리포트 생성기

기존 분석 파일을 읽고 맥락에 맞는 센티먼트 리포트 생성
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from dotenv import load_dotenv

# 프로젝트 루트 기준 .env 로드
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(Path.cwd() / ".env")

from .unified_collector import collect_all_sources
from .base import analyze_sentiment, get_sentiment_label
from .context_extractor import (
    StockContext,
    extract_context_from_analysis,
    context_to_search_config,
)


async def generate_context_aware_report(
    analysis_file: Path,
    output_dir: Optional[Path] = None,
    telegram_channels: Optional[List[str]] = None,
) -> str:
    """
    기존 분석 파일 기반 Context-Aware SI+ 리포트 생성

    Args:
        analysis_file: stock_analyzer_summary.md 경로
        output_dir: 출력 디렉토리 (없으면 analysis_file과 같은 디렉토리)
        telegram_channels: 텔레그램 채널 (없으면 config에서 로드)

    Returns:
        생성된 리포트 내용
    """
    # 1. 컨텍스트 추출
    print(f"\n{'='*60}")
    print(f"SI+ Context-Aware 리포트 생성")
    print(f"{'='*60}")
    print(f"\n분석 파일: {analysis_file}")

    ctx = extract_context_from_analysis(analysis_file)
    if not ctx:
        raise ValueError(f"분석 파일을 읽을 수 없습니다: {analysis_file}")

    print(f"\n컨텍스트 추출 완료:")
    print(f"  종목: {ctx.stock_name} ({ctx.ticker})")
    print(f"  별칭: {', '.join(ctx.aliases)}")
    print(f"  사업 키워드: {', '.join(ctx.business_keywords[:5])}...")
    print(f"  테마 키워드: {', '.join(ctx.theme_keywords[:5])}...")

    # 2. 텔레그램 채널 로드
    if telegram_channels is None:
        config_path = PROJECT_ROOT / "config" / "telegram_channels.json"
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            telegram_channels = []
            for cat_data in config.get("channels", {}).values():
                telegram_channels.extend(cat_data.get("channels", []))
            print(f"  Telegram 채널: {len(telegram_channels)}개 (config에서 로드)")
        else:
            telegram_channels = []
            print(f"  Telegram 채널: 없음")

    # 3. 센티먼트 수집
    search_config = context_to_search_config(ctx)
    print(f"\n데이터 수집 중...")
    print(f"  검색 테마: {', '.join(search_config['theme_keywords'][:8])}...")

    result = await collect_all_sources(
        ticker=search_config["ticker"],
        aliases=search_config["aliases"],
        theme_keywords=search_config["theme_keywords"],
        telegram_channels=telegram_channels,
        enable_reddit=True,
        enable_naver=True,
        limit_per_source=100,
    )

    # 4. 리포트 생성
    report = _generate_narrative_report(ctx, result)

    # 5. 저장
    if output_dir is None:
        output_dir = analysis_file.parent

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "SI_PLUS_REPORT.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ 리포트 저장: {output_path}")

    return report


def _generate_narrative_report(ctx: StockContext, result: Dict) -> str:
    """서술형 리포트 생성"""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    stats = result.get("stats", {})
    combined = result.get("combined", {})
    sentiment = combined.get("sentiment", {})
    score = sentiment.get("score", 0)
    label = combined.get("sentiment_label", "N/A")

    # 헤더
    lines.append(f"# {ctx.stock_name} ({ctx.ticker}) SI+ 센티먼트 분석")
    lines.append("")
    lines.append(f"> 분석일: {now} KST | Context-Aware Mode")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. Executive Summary
    lines.append("## Executive Summary")
    lines.append("")

    total_msgs = stats.get("total_messages", 0)
    direct_count = stats.get("direct_count", 0)
    theme_count = stats.get("theme_count", 0)

    bullish = sentiment.get("bullish_count", 0)
    bearish = sentiment.get("bearish_count", 0)

    if total_msgs > 0:
        lines.append(f"**{ctx.stock_name}**에 대한 커뮤니티 센티먼트는 **{label}** (점수: {score:+.2f})입니다.")
        lines.append("")

        if direct_count > 0:
            lines.append(f"- 종목 직접 언급: **{direct_count}건** (종목명/코드 매칭)")
        if theme_count > 0:
            lines.append(f"- 연관 테마 언급: **{theme_count}건** ({', '.join(ctx.theme_keywords[:3])} 등)")
        lines.append("")

        if bullish > bearish * 2:
            lines.append("전반적으로 **긍정적** 분위기가 우세합니다.")
        elif bearish > bullish * 2:
            lines.append("전반적으로 **부정적** 분위기가 우세합니다.")
        else:
            lines.append("**중립적** 분위기로, 뚜렷한 방향성이 없습니다.")
    else:
        lines.append(f"**{ctx.stock_name}**에 대한 커뮤니티 데이터가 부족합니다.")
        lines.append("")
        lines.append("- 소형주 특성상 개인 투자자 관심이 낮을 수 있습니다.")
        lines.append("- 테마 키워드를 통한 간접 분석을 권장합니다.")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 2. 수집 현황
    lines.append("## 데이터 수집 현황")
    lines.append("")
    lines.append("| 소스 | 수집량 | 직접 매칭 | 테마 매칭 |")
    lines.append("|------|--------|----------|----------|")

    for source_result in result.get("sources", []):
        source = source_result.get("source", "unknown")
        s_stats = source_result.get("stats", {})
        total = s_stats.get("total_messages", 0)
        direct = s_stats.get("direct_count", 0)
        theme = s_stats.get("theme_count", 0)
        lines.append(f"| {source.capitalize()} | {total} | {direct} | {theme} |")

    lines.append(f"| **합계** | **{total_msgs}** | **{direct_count}** | **{theme_count}** |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 3. 센티먼트 분석
    lines.append("## 센티먼트 분석")
    lines.append("")
    lines.append(f"### 종합 점수: **{label}** ({score:+.2f})")
    lines.append("")

    if total_msgs > 0:
        neutral = sentiment.get("neutral_count", 0)
        lines.append("| 의견 | 비율 |")
        lines.append("|------|------|")
        lines.append(f"| 🟢 상승 | {bullish/total_msgs*100:.1f}% ({bullish}건) |")
        lines.append(f"| 🔴 하락 | {bearish/total_msgs*100:.1f}% ({bearish}건) |")
        lines.append(f"| ⚪ 중립 | {neutral/total_msgs*100:.1f}% ({neutral}건) |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 4. 주요 의견 (Context-aware)
    lines.append("## 주요 의견")
    lines.append("")

    top_bullish = sentiment.get("top_bullish", [])
    top_bearish = sentiment.get("top_bearish", [])

    # 직접 매칭 우선 표시
    direct_bullish = [m for m in top_bullish if m.get("match_type") == "direct"]
    direct_bearish = [m for m in top_bearish if m.get("match_type") == "direct"]

    if direct_bullish or direct_bearish:
        lines.append("### 종목 직접 언급")
        lines.append("")

        if direct_bullish:
            lines.append("**상승 의견:**")
            for msg in direct_bullish[:3]:
                text = msg.get("text", "")[:60]
                source = msg.get("source", "")
                lines.append(f"- [{source}] \"{text}...\"")
            lines.append("")

        if direct_bearish:
            lines.append("**하락 의견:**")
            for msg in direct_bearish[:3]:
                text = msg.get("text", "")[:60]
                source = msg.get("source", "")
                lines.append(f"- [{source}] \"{text}...\"")
            lines.append("")

    # 테마 매칭
    theme_bullish = [m for m in top_bullish if m.get("match_type") == "theme"]
    theme_bearish = [m for m in top_bearish if m.get("match_type") == "theme"]

    if theme_bullish or theme_bearish:
        lines.append("### 연관 테마 동향")
        lines.append("")
        lines.append(f"검색 테마: {', '.join(ctx.theme_keywords[:5])}")
        lines.append("")

        if theme_bullish:
            lines.append("**긍정적 시그널:**")
            for msg in theme_bullish[:3]:
                text = msg.get("text", "")[:60]
                kw = msg.get("matched_keyword", "")
                lines.append(f"- [{kw}] \"{text}...\"")
            lines.append("")

        if theme_bearish:
            lines.append("**부정적 시그널:**")
            for msg in theme_bearish[:3]:
                text = msg.get("text", "")[:60]
                kw = msg.get("matched_keyword", "")
                lines.append(f"- [{kw}] \"{text}...\"")
            lines.append("")

    if not (direct_bullish or direct_bearish or theme_bullish or theme_bearish):
        lines.append("_의미 있는 의견이 수집되지 않았습니다._")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 5. 테마 트렌드
    lines.append("## 테마 트렌드")
    lines.append("")

    all_messages = combined.get("messages", [])
    theme_counts = {}
    for msg in all_messages:
        if msg.get("match_type") == "theme":
            kw = msg.get("matched_keyword", "기타")
            theme_counts[kw] = theme_counts.get(kw, 0) + 1

    if theme_counts:
        lines.append("| 테마 | 언급 수 | 비중 |")
        lines.append("|------|---------|------|")
        total_theme_msgs = sum(theme_counts.values())
        for kw, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:7]:
            pct = count / total_theme_msgs * 100
            lines.append(f"| {kw} | {count} | {pct:.1f}% |")
        lines.append("")

        # 테마 인사이트
        top_theme = max(theme_counts, key=theme_counts.get)
        lines.append(f"가장 활발한 테마는 **{top_theme}**로, 관련 논의가 활발합니다.")
    else:
        lines.append("_테마 키워드 매칭 없음_")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 6. 루머 체크
    rumors = combined.get("rumors", [])
    rumor_ratio = stats.get("rumor_ratio", 0)

    lines.append("## 정보 신뢰도")
    lines.append("")
    lines.append(f"루머 비율: **{rumor_ratio:.1%}**")
    lines.append("")

    if rumor_ratio < 0.1:
        lines.append("✅ 대부분 신뢰할 수 있는 정보입니다.")
    elif rumor_ratio < 0.3:
        lines.append("⚠️ 일부 확인되지 않은 정보가 포함되어 있습니다.")
    else:
        lines.append("🚨 루머 비율이 높습니다. 교차 검증이 필요합니다.")

    if rumors:
        lines.append("")
        lines.append("**검증 필요:**")
        for r in rumors[:3]:
            text = r.get("text", "")[:50]
            lines.append(f"- \"{text}...\"")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 7. 종합 판단 (with context)
    lines.append("## 종합 판단")
    lines.append("")

    lines.append("| 항목 | 판단 |")
    lines.append("|------|------|")
    lines.append(f"| 센티먼트 | {label} ({score:+.2f}) |")
    lines.append(f"| 데이터 충분성 | {'충분' if total_msgs >= 50 else '보통' if total_msgs >= 10 else '부족'} ({total_msgs}건) |")
    lines.append(f"| 직접 언급 비율 | {direct_count/total_msgs*100:.1f}% |" if total_msgs > 0 else "| 직접 언급 비율 | N/A |")
    lines.append(f"| 정보 신뢰도 | {'높음' if rumor_ratio < 0.1 else '보통' if rumor_ratio < 0.3 else '낮음'} |")
    lines.append("")

    # 컨텍스트 기반 인사이트
    if ctx.summary:
        lines.append("### 기존 분석과의 연계")
        lines.append("")
        lines.append(f"기존 분석에서는 \"{ctx.summary[:100]}...\"로 평가했습니다.")
        lines.append("")

        # 센티먼트와 기존 분석 비교
        if score > 0.3 and "적자" in ctx.summary:
            lines.append("⚠️ 커뮤니티 센티먼트는 긍정적이나, 재무 상황(적자)과 괴리가 있습니다.")
        elif score < -0.3 and "회복" in ctx.summary:
            lines.append("⚠️ 커뮤니티 센티먼트는 부정적이나, 펀더멘털 회복 조짐과 괴리가 있습니다.")
        else:
            lines.append("센티먼트가 기존 분석 방향과 일관성이 있습니다.")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by SI+ Context-Aware Agent*")

    return "\n".join(lines)


# CLI 실행 지원
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python context_aware_report.py <analysis_file>")
        sys.exit(1)

    analysis_file = Path(sys.argv[1])
    asyncio.run(generate_context_aware_report(analysis_file))
