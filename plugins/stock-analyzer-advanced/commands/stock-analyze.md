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

## Execution Flow

### Phase 1: Setup & Date Verification

```python
# 1. Verify current date (CRITICAL)
WebSearch("what is today's date")

# 2. Determine market type
market = "KRX" if ticker.isdigit() else "US"

# 3. Create/check work directory
work_dir = f"watchlist/stocks/{ticker}/"
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

# TI Worker (only for deep analysis)
if depth == "deep":
    Task(
        subagent_type="stock-analyzer-advanced:technical-intelligence",
        prompt=f"""
        Technical analysis for {ticker}:
        1. RSI (14-day)
        2. MACD + Signal line
        3. Bollinger Bands
        4. Support/Resistance levels
        5. Buy/Sell signals interpretation
        """,
        description=f"TI: {ticker} technicals"
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
obsidian_append_content(
    filepath=f"watchlist/stocks/{ticker}/analysis.md",
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
