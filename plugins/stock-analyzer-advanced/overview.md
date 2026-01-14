# Stock Analyzer Advanced - Overview

## 프로젝트 개요

Stock Analyzer Advanced는 Anthropic의 AI espionage 연구에서 영감을 받아 개발된 **대화형 고급 주식 시장 분석 시스템**입니다. 사용자와의 상호작용을 통해 즉각적이고 심층적인 시장 분석을 제공하며, 복잡한 투자 결정을 지원합니다.

## ⚠️ 데이터 정확성 철칙

**주식 분석의 핵심은 최신성과 정확성입니다:**

### 필수 검증 프로세스 (순서 엄수)

#### STEP 0: 오늘 날짜 확인 (최우선 필수 🗓️)
```bash
# 모든 분석 시작 전
WebFetch("https://www.google.com", "오늘 날짜 추출")
또는
WebSearch("what is today's date")
```

#### STEP 1-4: 데이터 수집
**미국 주식:**
1. **yfinance MCP** (최우선) - 가장 정확한 실시간 가격
2. **WebFetch** (MCP 없을 시) - Yahoo Finance 직접 조회
3. **WebSearch** (뉴스) - 반드시 날짜 포함 ("NVDA December 30 2025")
4. **Playwright** (차트) - 시각적 확인

**한국 주식:**
1. **Playwright → FnGuide** - 재무제표, PER/PBR 필수
2. **WebSearch** - 뉴스, 날짜 포함
3. **Naver Finance** - 실시간 가격, 공시

### 금지 사항
- ❌ **날짜 확인 없이 분석 시작**
- ❌ "today", "latest" 같은 모호한 검색어 (연도 불명확)
- ❌ 기억이나 추측으로 가격 언급
- ❌ "약 $XXX", "대충 XXX원" 같은 모호한 표현
- ❌ 날짜와 출처 없는 데이터 제공

### ✅ 올바른 예시
```
NVDA 현재가: $187.72
📅 확인: 2025-12-30 15:30 EST
📊 출처: yfinance MCP
✅ 52주 범위 내 ($86.62-$212.19)
```

## 핵심 철학

### 1. Interactive Intelligence (대화형 지능)
- **즉각적 응답**: 사용자 질문에 실시간 분석 제공
- **맥락 이해**: 대화 흐름을 파악하여 연속적 분석
- **맞춤형 인사이트**: 사용자 관심사에 맞춘 깊이 있는 분석

### 2. On-Demand Deep Analysis (온디맨드 심층 분석)
- **Multi-Source Integration**: 요청 시 다중 소스 즉시 조회
- **Real-time Processing**: 최신 데이터 기반 즉각 분석
- **Comprehensive Coverage**: 뉴스, 기술적 분석, 센티먼트 통합

### 3. Intelligent Pattern Recognition (지능형 패턴 인식)
- **Hidden Opportunities**: 대화 중 숨겨진 기회 발견
- **Risk Detection**: 잠재 리스크 사전 식별 및 경고
- **Strategic Insights**: 실행 가능한 전략 즉시 제안

## 시스템 아키텍처

### Layer 1: Intelligence Gathering (정보 수집층)
```
📡 Market Scanner
  ├── News Crawler (뉴스 크롤러)
  ├── Social Sentiment Analyzer (소셜 감성 분석)
  ├── Regulatory Filing Monitor (공시 모니터)
  ├── Alternative Data Collector (대체 데이터 수집)
  └── Market Microstructure Analyzer (시장 미세구조 분석)
```

### Layer 2: Analysis & Assessment (분석 평가층)
```
🧠 Intelligence Processor
  ├── Pattern Recognition Engine (패턴 인식 엔진)
  ├── Vulnerability Scanner (취약점 스캐너)
  ├── Opportunity Identifier (기회 식별기)
  ├── Risk Assessor (리스크 평가기)
  └── Value Classifier (가치 분류기)
```

### Layer 3: Strategy & Execution (전략 실행층)
```
⚡ Autonomous Trader
  ├── Strategy Generator (전략 생성기)
  ├── Backtesting Engine (백테스팅 엔진)
  ├── Position Manager (포지션 관리자)
  ├── Risk Controller (리스크 컨트롤러)
  └── Performance Monitor (성과 모니터)
```

## 에이전트 구성

### 1. 🕵️ Market Intelligence Agent
**역할**: 사용자 요청에 따른 즉각적 시장 정보 수집 및 분석

**핵심 기능**:
- 요청 시 즉시 뉴스 및 공시 조회
- 특정 종목/섹터 센티먼트 분석
- 최근 내부자 거래 확인
- 기관 동향 즉시 파악
- 관련 글로벌 이벤트 영향 분석

**대화형 특징**:
- "NVDA 최근 뉴스 분석해줘"
- "반도체 섹터 센티먼트 어때?"
- "최근 내부자 매도 많은 종목 찾아줘"

### 2. 🔍 Vulnerability Scanner Agent
**역할**: 요청 시 시장 취약점 및 리스크 분석

**핵심 기능**:
- 특정 종목의 가격 괴리 확인
- 섹터별 유동성 리스크 평가
- 정보 비대칭 상황 분석
- 이상 거래 패턴 탐지
- 포트폴리오 리스크 진단

**대화형 특징**:
- "KOSPI 과매도 종목 찾아줘"
- "이 종목 유동성 위험 있어?"
- "최근 이상 거래 패턴 보이는 종목 분석해줘"

### 3. 🎯 Opportunity Hunter Agent
**역할**: 사용자 맞춤형 투자 기회 발굴

**핵심 기능**:
- 사용자 기준에 맞는 종목 스크리닝
- 단기/중기/장기 기회 구분
- 테마별 유망 종목 발굴
- 이벤트 기반 투자 기회 제시
- 리스크-리턴 분석

**대화형 특징**:
- "PER 10 이하 성장주 찾아줘"
- "다음 주 실적 발표 종목 중 기회 있는 거"
- "AI 테마 숨은 보석 찾아줘"

### 4. 🤖 Strategic Advisor Agent
**역할**: 대화를 통한 맞춤형 전략 수립

**핵심 기능**:
- 사용자 투자 스타일 파악
- 맞춤형 포트폴리오 구성
- 진입/청산 타이밍 조언
- 헤징 전략 제안
- 리밸런싱 시점 추천

**대화형 특징**:
- "내 포트폴리오 진단해줘"
- "이 종목 언제 사는 게 좋을까?"
- "리스크 줄이는 방법 추천해줘"

### 5. 🛡️ Risk Sentinel Agent
**역할**: 요청 기반 리스크 분석 및 경고

**핵심 기능**:
- 포트폴리오 리스크 즉시 계산
- 시나리오별 손실 예측
- 상관관계 분석
- 블랙스완 리스크 평가
- 헤징 방안 제시

**대화형 특징**:
- "내 포트폴리오 VaR 계산해줘"
- "금리 1% 오르면 영향 분석해줘"
- "현재 가장 큰 리스크가 뭐야?"

### 6. 📊 Performance Analyst Agent
**역할**: 투자 성과 분석 및 개선점 제시

**핵심 기능**:
- 수익률 분석 및 원인 파악
- 벤치마크 대비 성과 평가
- 실수 패턴 식별
- 개선 방안 구체적 제시
- 성공 요인 분석

**대화형 특징**:
- "이번 달 투자 성과 분석해줘"
- "왜 손실이 났는지 분석해줘"
- "투자 스타일 개선점 찾아줘"

## 혁신적 기능

### 1. Interactive Multi-Phase Analysis
```python
사용자: "테슬라 투자할만해?"

Phase 1: Quick Assessment (즉시 평가)
  - 현재 가격 및 추세 확인
  - 최근 주요 뉴스 스캔

Phase 2: Deep Dive (심층 분석)
  - 재무제표 분석
  - 경쟁사 비교
  - 산업 전망 평가

Phase 3: Risk Analysis (리스크 분석)
  - 주요 리스크 요인 식별
  - 시나리오별 영향 분석

Phase 4: Strategy Recommendation (전략 추천)
  - 진입 가격 및 타이밍
  - 포지션 크기 제안
  - 손절/익절 레벨

Phase 5: Follow-up (후속 대화)
  - "더 자세히 설명해줘"
  - "다른 대안은?"
  - "리스크 헤징 방법은?"
```

### 2. Context-Aware Intelligence
- **대화 맥락 유지**: 이전 질문과 연계된 분석
- **사용자 프로필 학습**: 투자 성향에 맞춘 조언
- **점진적 심화**: 대화가 진행될수록 더 깊은 인사이트

### 3. Real-time Interactive Updates
- **즉시 업데이트**: "방금 나온 뉴스 반영해줘"
- **비교 분석**: "어제 분석과 뭐가 달라졌어?"
- **What-if 시나리오**: "만약 금리가 오르면?"

### 4. Conversational Learning
- **실수 인정**: "아, 그 부분은 놓쳤네요. 다시 분석하면..."
- **사용자 피드백 반영**: "그 관점은 생각 못했는데..."
- **지속적 개선**: 대화를 통한 분석 품질 향상

## 사용 시나리오

### Scenario 1: Morning Market Check
```
사용자: "오늘 시장 어때?"
AI: "미국 증시가 2% 상승 마감했고, 특히 반도체가 강세였습니다.
     KOSPI는 상승 출발이 예상되는데, 삼성전자와 SK하이닉스를
     주목하세요. 다만 원달러 환율이 1,300원을 넘어서..."

사용자: "삼성전자 더 자세히 분석해줘"
AI: [심층 분석 제공]
```

### Scenario 2: Investment Decision Support
```
사용자: "10만불 있는데 어디 투자할까?"
AI: "투자 기간과 리스크 성향을 알려주시겠어요?"

사용자: "3년 정도, 중간 리스크"
AI: "3년 투자라면 다음 포트폴리오를 추천합니다:
     1. 우량 성장주 40% (MSFT, GOOGL...)
     2. 배당주 30% (JNJ, KO...)
     3. 신흥시장 20% (한국, 인도...)
     4. 현금 10%
     각각 이유를 설명드릴까요?"
```

### Scenario 3: Crisis Response
```
사용자: "내 포트폴리오가 -10%인데 어떻게 해?"
AI: "포트폴리오를 분석해보니 기술주 비중이 80%네요.
     현재 금리 인상 우려로 기술주가 조정받고 있습니다.

     옵션 1: 장기 투자라면 홀딩하며 추가 매수 고려
     옵션 2: 일부를 방어주로 리밸런싱
     옵션 3: 헤징을 위한 인버스 ETF 소량 편입

     어떤 방향을 선호하시나요?"
```

## 기술 스택

### Core Technologies
- **Language Model**: Claude (Opus/Sonnet)
- **Data Processing**: Parallel WebSearch, WebFetch
- **Web Automation**: Playwright
- **Data Storage**: Local file system with structured formats
- **Orchestration**: Agent-based autonomous system

### Data Sources
- **Primary**: Bloomberg, Reuters, FnGuide
- **Alternative**: Reddit, Twitter, Naver Finance
- **Regulatory**: DART, SEC EDGAR
- **Technical**: Trading View, Yahoo Finance
- **Macro**: Fed, ECB, BOJ data

## 리스크 관리

### System Safeguards
1. **Position Limits**: 자동 거래 시 포지션 한도 설정
2. **Stop Loss**: 모든 포지션에 자동 손절 설정
3. **Circuit Breakers**: 비정상 상황 시 자동 중단
4. **Human Override**: 언제든 수동 개입 가능
5. **Audit Trail**: 모든 결정 과정 기록

### Compliance & Ethics
- **규제 준수**: 자동 거래 관련 법규 준수
- **시장 조작 방지**: 불공정 거래 행위 차단
- **정보 보안**: 민감 정보 암호화 및 보호
- **투명성**: 모든 거래 로직 설명 가능

## 성과 측정

### Key Metrics
- **Sharpe Ratio**: 리스크 조정 수익률
- **Win Rate**: 승률
- **Maximum Drawdown**: 최대 손실폭
- **Alpha Generation**: 초과 수익률
- **Information Ratio**: 정보 효율성

### Reporting
- **Real-time Dashboard**: 실시간 성과 모니터링
- **Daily Summary**: 일일 거래 요약
- **Weekly Analysis**: 주간 전략 분석
- **Monthly Review**: 월간 성과 리뷰

## 향후 로드맵

### Phase 1 (Current): Foundation
- ✅ 기본 아키텍처 설계
- ⬜ 핵심 에이전트 구현
- ⬜ 데이터 파이프라인 구축
- ⬜ 백테스팅 시스템 구현

### Phase 2: Intelligence Enhancement
- ⬜ 머신러닝 모델 통합
- ⬜ 자연어 처리 고도화
- ⬜ 예측 모델 정확도 향상
- ⬜ 실시간 학습 시스템

### Phase 3: Full Autonomy
- ⬜ 완전 자율 거래 시스템
- ⬜ 자가 최적화 알고리즘
- ⬜ 다중 전략 앙상블
- ⬜ 글로벌 멀티 애셋 대응

### Phase 4: Quantum Leap
- ⬜ 양자 컴퓨팅 통합
- ⬜ 뉴로모픽 처리
- ⬜ 완전 분산형 시스템
- ⬜ AGI 수준 시장 이해

## 시작하기

### Prerequisites
```bash
# Required tools
- Claude API access
- Web browser for Playwright
- Stable internet connection
```

### Quick Start with PI (Portfolio Intelligence)
```bash
# 1. Navigate to the plugin directory
cd plugins/stock-analyzer-advanced

# 2. Run Portfolio Intelligence (최상위 에이전트)
agent portfolio-intelligence

# 3. PI가 MI와 협업하여 종합 분석
> "반도체 섹터 투자 전략 짜줘"
> PI: "섹터 지식 활용하여 분석하겠습니다..."
> PI -> MI: "반도체 최신 동향 수집 요청"
> MI: "실시간 데이터 수집 중..."
> PI: "종합 분석 결과: [watchlist 생성]"
```

### Output Structure
```yaml
# 분석 결과 저장 경로
output_path: stock_checklist/

# 폴더 구조
stock_checklist/
  ├── {종목명}_{종목코드}/
  │   └── stock_analyzer_summary.md
  ├── 삼성전자_005930/
  │   └── stock_analyzer_summary.md
  └── NVIDIA_NVDA/
      └── stock_analyzer_summary.md
```

## 결론

Stock Analyzer Advanced는 단순한 분석 도구를 넘어, 진정한 의미의 자율 투자 인텔리전스 시스템입니다. AI espionage 기술의 핵심 개념을 금융 시장에 적용함으로써, 인간의 한계를 뛰어넘는 속도와 정확도로 시장을 분석하고 기회를 포착할 수 있습니다.

이 시스템의 궁극적 목표는 투자자에게 "제2의 뇌"를 제공하여, 24시간 쉬지 않고 시장을 감시하고, 기회를 발견하며, 리스크를 관리하는 것입니다.

**"The future of investing is not human vs. machine, but human with machine."**