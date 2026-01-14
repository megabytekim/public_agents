---
name: stock-analyze
description: Comprehensive stock analysis with parallel MI/SI/TI worker execution. Main context orchestrates directly without PI agent.
arguments:
  - name: ticker
    description: Stock symbol to analyze (e.g., NVDA, 005930, Samsung)
    required: true
  - name: depth
    description: Analysis depth (quick/standard/deep)
    required: false
    default: standard
---

# Stock Analysis Command

This command performs comprehensive stock analysis by **orchestrating MI/SI/TI workers directly from main context**.

## Architecture

```
/stock-analyze (Main Context - Orchestrator)
    │
    ├─→ STEP 0: Date verification (WebSearch)
    ├─→ STEP 1: Basic data collection (yfinance MCP / WebFetch)
    │
    ├─→ Parallel Task dispatch:
    │   ├─→ Task(MI): Deep market data
    │   ├─→ Task(SI): Sentiment analysis
    │   └─→ Task(TI): Technical indicators (if depth=deep)
    │
    ├─→ STEP 2: Integrate results + Strategic analysis
    ├─→ STEP 3: Generate report
    └─→ STEP 4: Append to watchlist (always append, never overwrite)
```

## Critical Rules

### Data Accuracy Protocol (MANDATORY)

1. **STEP 0 - Date First**: Always verify current date before any data collection
   - ⚠️ **Do NOT include explicit year numbers** in date search queries (e.g., "2025", "2026")
   - Use: `"what is today's date"` or `"current date"` (without year)
   - Reason: Hardcoded years become outdated and cause incorrect searches
2. **Source Attribution**: ALL data must include source + timestamp
3. **No Speculation**: Never guess prices or make up numbers
4. **Cross-Validation**: Verify data across multiple sources when possible

### Storage Rule (Important)

**Always APPEND, never overwrite.**

Stock data changes constantly. Each analysis should be appended with timestamp:

```markdown
## Analysis: 2025-01-12 14:30 KST

[New analysis content]

---

## Analysis: 2025-01-11 09:15 KST

[Previous analysis content]
```

This preserves historical context for trend analysis.

---

## Plugin Path (IMPORTANT)

```python
# All paths MUST be relative to project root, prefixed with plugin directory
PLUGIN_DIR = "plugins/stock-analyzer-advanced"

# Examples:
# ✅ Correct: f"{PLUGIN_DIR}/watchlist/stocks/{ticker}/"
# ❌ Wrong:   f"watchlist/stocks/{ticker}/"  (creates at project root!)
```

---

## Execution Flow

### Phase 1: Setup & Date Verification

```python
# 1. Verify current date (CRITICAL)
# ⚠️ IMPORTANT: Do NOT include year numbers in date search queries!
# Bad:  "today's date 2025" (year may be outdated)
# Good: "what is today's date" or "current date"
WebSearch("what is today's date")

# 2. Determine market type
market = "KRX" if ticker.isdigit() else "US"

# 3. Create/check work directory
# ⚠️ IMPORTANT: Use plugin-relative path, NOT project root!
PLUGIN_DIR = "plugins/stock-analyzer-advanced"
work_dir = f"{PLUGIN_DIR}/watchlist/stocks/{ticker}/"
```

### Phase 2: Parallel Worker Dispatch

**Main context dispatches MI + SI + TI in parallel (single message, multiple Task calls)**

```python
# Dispatch all workers in ONE message (parallel execution)

# MI Worker
Task(
    subagent_type="stock-analyzer-advanced:market-intelligence",
    prompt=f"""
    Collect market data for {ticker}:
    1. Current price + change (with source, timestamp)
    2. 52-week high/low
    3. Recent news (5 items with dates)
    4. Financial metrics (PER, PBR, ROE)
    5. Analyst ratings/target prices

    Return structured data with ALL sources cited.
    """,
    description=f"MI: {ticker} market data"
)

# SI Worker
Task(
    subagent_type="stock-analyzer-advanced:sentiment-intelligence",
    prompt=f"""
    Collect sentiment for {ticker}:

    Korean stocks:
    - Naver Stock Forum (종토방)
    - Community reactions

    US stocks:
    - Reddit (WSB, r/stocks)
    - StockTwits bullish/bearish ratio

    Output:
    1. Sentiment score (-2 to +2)
    2. Bullish/Bearish percentage
    3. Key opinions summary
    4. Anomaly check (pump-and-dump, manipulation)
    """,
    description=f"SI: {ticker} sentiment"
)

# TI Worker (only for deep analysis) - Uses local utils, NOT web search
if depth == "deep":
    Task(
        subagent_type="general-purpose",
        prompt=f"""
        ## TI Worker: Technical Analysis for {ticker}

        **CRITICAL**: You MUST use Bash to execute Python code with local utils.
        Do NOT use WebSearch for technical indicators - use pykrx data directly.

        ### Execute this Python code via Bash:

        ```bash
        cd /Users/newyork/public_agents/plugins/stock-analyzer-advanced && python3 << 'PYEOF'
import sys
sys.path.insert(0, '/Users/newyork/public_agents/plugins/stock-analyzer-advanced')

from utils import (
    get_ohlcv, get_ticker_name, get_fundamental,
    sma, ema, rsi, macd, bollinger, stochastic, support_resistance
)

ticker = "{ticker}"

# 종목명
name = get_ticker_name(ticker)
print(f"# TI 기술적 분석: {{name}} ({{ticker}})")
print()

# OHLCV 조회
df = get_ohlcv(ticker, days=60)
if df is None:
    print("ERROR: 데이터 조회 실패")
    exit()

close = df['종가']
high = df['고가']
low = df['저가']

print(f"## 기본 정보")
print(f"| 항목 | 값 |")
print(f"|------|-----|")
print(f"| 현재가 | {{close.iloc[-1]:,}}원 |")

# 52주 고/저
df_year = get_ohlcv(ticker, days=252)
if df_year is not None and not df_year.empty:
    print(f"| 52주 최고 | {{df_year['고가'].max():,}}원 |")
    print(f"| 52주 최저 | {{df_year['저가'].min():,}}원 |")
print()

# 기술지표
print(f"## 기술지표")
print(f"| 지표 | 값 | 신호 |")
print(f"|------|-----|------|")

# RSI
rsi_val = rsi(close).iloc[-1]
rsi_signal = "과매수" if rsi_val > 70 else "과매도" if rsi_val < 30 else "중립"
print(f"| RSI(14) | {{rsi_val:.1f}} | {{rsi_signal}} |")

# MACD
macd_line, signal_line, hist = macd(close)
macd_signal = "매수 (골든크로스)" if macd_line.iloc[-1] > signal_line.iloc[-1] else "매도 (데드크로스)"
print(f"| MACD | {{macd_line.iloc[-1]:.0f}} / Signal {{signal_line.iloc[-1]:.0f}} | {{macd_signal}} |")

# 스토캐스틱
k, d = stochastic(high, low, close)
stoch_signal = "과매수" if k.iloc[-1] > 80 else "과매도" if k.iloc[-1] < 20 else "중립"
print(f"| 스토캐스틱 %K | {{k.iloc[-1]:.1f}} | {{stoch_signal}} |")

# 볼린저
upper, middle, lower = bollinger(close)
curr = close.iloc[-1]
if curr > upper.iloc[-1]:
    bb_pos = "상단 돌파 (과열)"
elif curr < lower.iloc[-1]:
    bb_pos = "하단 이탈 (침체)"
else:
    bb_pos = "밴드 내"
print(f"| 볼린저 | {{lower.iloc[-1]:,.0f}} ~ {{upper.iloc[-1]:,.0f}} | {{bb_pos}} |")
print()

# 지지/저항
sr = support_resistance(high, low, close)
print(f"## 지지/저항선")
print(f"| 레벨 | 가격 |")
print(f"|------|------|")
print(f"| R2 (저항2) | {{sr['r2']:,.0f}}원 |")
print(f"| R1 (저항1) | {{sr['r1']:,.0f}}원 |")
print(f"| Pivot | {{sr['pivot']:,.0f}}원 |")
print(f"| S1 (지지1) | {{sr['s1']:,.0f}}원 |")
print(f"| S2 (지지2) | {{sr['s2']:,.0f}}원 |")
print()

# 이동평균
print(f"## 이동평균")
print(f"| MA | 값 | 현재가 대비 |")
print(f"|-----|-----|------------|")
for period in [5, 20, 60]:
    ma_val = sma(close, period).iloc[-1]
    vs = "상회" if curr > ma_val else "하회"
    print(f"| {{period}}일 | {{ma_val:,.0f}}원 | {{vs}} |")
print()

# 종합 판단
signals = []
if rsi_val < 30: signals.append("RSI 과매도")
if rsi_val > 70: signals.append("RSI 과매수")
if macd_line.iloc[-1] > signal_line.iloc[-1]: signals.append("MACD 매수")
else: signals.append("MACD 매도")
if k.iloc[-1] < 20: signals.append("스토캐스틱 과매도")
if k.iloc[-1] > 80: signals.append("스토캐스틱 과매수")

buy_signals = sum(1 for s in signals if "매수" in s or "과매도" in s)
sell_signals = sum(1 for s in signals if "매도" in s or "과매수" in s)

if buy_signals > sell_signals:
    overall = "매수"
elif sell_signals > buy_signals:
    overall = "매도"
else:
    overall = "중립"

print(f"## 종합 판단")
print(f"**신호**: {{overall}}")
print(f"**근거**: {{', '.join(signals)}}")
PYEOF
        ```

        Run the above code and return the markdown output as your result.
        If pykrx fails, report the error - do NOT fall back to web search.
        """,
        description=f"TI: {ticker} technicals (pykrx)"
    )
```

### Phase 3: Strategic Analysis (Main Context)

After workers complete, main context performs strategic analysis using sector knowledge:

```python
# Integrate MI + SI + TI results
# Apply sector knowledge (see below)
# Generate investment thesis
# Formulate entry/exit strategy
```

### Phase 4: Report Generation & Append

```python
# Generate report using template
# APPEND to existing file (never overwrite)
# ⚠️ Use plugin-relative path!
PLUGIN_DIR = "plugins/stock-analyzer-advanced"
obsidian_append_content(
    filepath=f"{PLUGIN_DIR}/watchlist/stocks/{ticker}/analysis.md",
    content=f"""
---

## Analysis: {current_datetime}

{report_content}
"""
)
```

---

## Sector Knowledge Base (Inline)

### Technology

```yaml
Semiconductor:
  Memory: DRAM, NAND, HBM (SK Hynix, Samsung, Micron)
  Non-Memory: AP, Foundry (TSMC, Samsung Foundry)
  Equipment: ASML, Lam Research, Applied Materials
  Key Metrics: ASP trends, bit growth, capex cycle

Software:
  SaaS: ARR, NRR, CAC/LTV
  AI/ML: GPU demand, inference costs
  Cloud: AWS/Azure/GCP market share
```

### Healthcare

```yaml
Pharma:
  Pipeline: Phase 1/2/3 success rates
  Patent cliff: Generic competition timing
  Key Metrics: R&D/Revenue ratio, approval timeline

Biotech:
  Gene therapy: Delivery mechanisms
  Cell therapy: CAR-T, CRISPR
  Key Metrics: Cash runway, clinical milestones
```

### Energy

```yaml
Traditional: Oil price correlation, refining margins
Renewable: Solar/Wind capacity factors, PPA prices
Battery: Cathode/Anode materials, cell-to-pack efficiency
EV: Attach rate, charging infrastructure
```

### Consumer

```yaml
Staples: Pricing power, input costs
Discretionary: Consumer confidence correlation
Luxury: China exposure, brand equity
```

---

## Moat Analysis Framework

Apply these checks during strategic analysis:

```markdown
□ Network Effects - Does value increase with more users?
□ Switching Costs - How painful to switch to competitor?
□ Cost Advantages - Scale economies, proprietary tech?
□ Intangible Assets - Brand, patents, licenses?
□ Efficient Scale - Natural monopoly characteristics?
```

---

## Valuation Framework

```python
valuation_approach = {
    "growth_stocks": ["PEG", "PSR", "Revenue Growth", "Rule of 40"],
    "value_stocks": ["PER", "PBR", "EV/EBITDA", "FCF Yield"],
    "quality_stocks": ["ROE", "ROIC", "Gross Margin stability"],
    "dividend_stocks": ["Dividend Yield", "Payout Ratio", "DPS Growth"]
}
```

---

## Analysis Depth Options

| Depth | MI Scope | SI Scope | TI Scope | Time |
|-------|----------|----------|----------|------|
| `quick` | Price + 2 news | Skip | Skip | ~2min |
| `standard` | Full data | Forum scan | Skip | ~5min |
| `deep` | + Competitor comparison | + Deep sentiment | Full technicals | ~10min |

---

## Output Template

```markdown
# {Company} ({ticker}) Analysis

**Date**: {YYYY-MM-DD HH:MM TZ}
**Depth**: {depth}
**Market**: {KRX/US}

---

## 1. Market Data (MI)

### Price
| Item | Value | Source |
|------|-------|--------|
| Current | $XXX | Yahoo Finance, {time} |
| Change | +X.X% | |
| 52W High | $XXX | |
| 52W Low | $XXX | |

### Recent News
1. [{title}]({url}) - {source}, {date}
2. ...

### Financials
| Metric | Value | Industry Avg |
|--------|-------|--------------|
| PER | XX.X | XX.X |
| PBR | X.X | X.X |
| ROE | XX% | XX% |

---

## 2. Sentiment (SI)

### Score Summary
| Platform | Score | Interpretation |
|----------|-------|----------------|
| Forum/Reddit | +X.X | Bullish/Bearish |
| StockTwits | XX% Bull | |

### Key Opinions
**Bullish**:
- ...

**Bearish**:
- ...

### Anomaly Check
- Pump-and-dump: {status}
- Manipulation signals: {status}

---

## 3. Technical Analysis (TI) - Deep only

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI (14) | XX | Overbought/Oversold/Neutral |
| MACD | X.XX | Golden/Dead Cross |
| Bollinger | {position} | |

Support: $XXX / Resistance: $XXX

---

## 4. Strategic Analysis

### Sector Position
{Analysis using sector knowledge}

### Moat Assessment
- Network Effects: {Yes/No/Partial}
- Switching Costs: {High/Medium/Low}
- ...

### Investment Thesis
- **Bull Case**: ...
- **Bear Case**: ...
- **Base Case**: ...

---

## 5. Investment Strategy

### Entry Points
| Level | Price | Allocation |
|-------|-------|------------|
| 1st | $XXX | 30% |
| 2nd | $XXX | 40% |
| 3rd | $XXX | 30% |

### Targets & Stop Loss
- Target 1: $XXX (+XX%)
- Target 2: $XXX (+XX%)
- Stop Loss: $XXX (-X%)

---

## 6. Risks

1. **{Risk 1}**: {description}
2. **{Risk 2}**: {description}
3. **Sentiment Risk**: {SI-based risk}

---

## 7. Conclusion

**Rating**: {Buy/Hold/Sell}
**Confidence**: {High/Medium/Low}

### MI vs SI Cross-Check
- Analyst View: {Buy/Neutral/Sell}
- Retail Sentiment: {Bullish/Neutral/Bearish}
- Divergence: {Yes/No} - {interpretation}

### Monitoring Points
- [ ] {Point 1}
- [ ] {Point 2}

---
*This is analysis reference only, not financial advice.*
*Tags: #analysis #{sector} #{ticker}*
```

---

## Execution

When this command is invoked:

1. **Main context** verifies date and basic info
2. **Main context** dispatches MI + SI (+ TI) workers in parallel
3. **Main context** waits for results and integrates
4. **Main context** applies sector knowledge for strategic analysis
5. **Main context** generates report and **APPENDS** to watchlist

```
Analyzing: {{ticker}}
Depth: {{depth}}

Starting parallel worker dispatch...
```
