# Stock Analyzer Advanced 리팩토링 계획

## 현재 구조 분석

### 디렉토리 구조

```
stock-analyzer-advanced/
├── README.md                    # 데이터 정확성 프로토콜
├── overview.md                  # 시스템 아키텍처
├── SETUP_VERIFICATION.md        # 셋업 체크리스트
│
├── agents/                      # 5개 에이전트
│   ├── portfolio-intelligence.md   # PI - 오케스트레이터 (opus)
│   ├── market-intelligence.md      # MI - 시장 데이터 (sonnet)
│   ├── sentiment-intelligence.md   # SI - 센티먼트 (sonnet)
│   ├── technical-intelligence.md   # TI - 기술적 분석 (sonnet)
│   └── financial-ml-analyst.md     # 인프라 개발용
│
├── commands/
│   └── 기업분석.md              # 단일 명령어
│
├── docs/
│   ├── anthropic-ai-espionage-insights.md
│   └── company-analysis-template.md
│
├── utils/                       # Python 유틸리티
│   ├── data_fetcher.py          # pykrx wrapper (7개 함수)
│   ├── indicators.py            # 기술적 지표 (7개 함수)
│   ├── web_scraper.py           # 네이버 스크래핑
│   ├── requirements.txt
│   └── PRD.md, plan.md
│
├── tests/                       # pytest 테스트
│   ├── conftest.py
│   ├── test_indicators.py
│   └── test_data_fetcher.py
│
└── watchlist/                   # 분석 결과 저장
    ├── stocks/{ticker}/
    │   ├── task_plan.md
    │   ├── notes.md
    │   └── {ticker}_분석.md
    └── daily_summaries/
```

### 에이전트 아키텍처

```
PI (Portfolio Intelligence) - Orchestrator
    ├─→ MI (Market Intelligence) - 가격/뉴스/재무
    ├─→ SI (Sentiment Intelligence) - 커뮤니티/이상징후
    └─→ TI (Technical Intelligence) - RSI/MACD/볼린저
```

---

## vehicle-contamination-or 플러그인과 비교

| 항목 | vehicle-contamination-or | stock-analyzer-advanced |
|------|--------------------------|------------------------|
| **목적** | 논문 연구 자동화 | 주식 분석 자동화 |
| **에이전트** | 4개 (finder/processor×2/ml) | 5개 (PI/MI/SI/TI/ML) |
| **명령어** | 4개 (search/download/process/research) | 1개 (기업분석) |
| **데이터 저장** | `private/paper/{slug}/` | `watchlist/stocks/{ticker}/` |
| **레지스트리** | ✅ registry.json + index.txt | ❌ 없음 |
| **Few-shot 예제** | ✅ 11개 예제 | ❌ 없음 |
| **병렬 처리** | ✅ max 8 배치 | ⚠️ PI가 순차 호출 |
| **Python 유틸** | ❌ 없음 | ✅ utils/ (21개 함수) |
| **테스트** | ❌ 없음 | ✅ pytest (35+ 케이스) |

---

## 개선 포인트

### 1. 명령어 세분화

**현재**: 단일 `기업분석` 명령어

**개선안**: 파이프라인 분리
```
commands/
├── stock-search.md      # 종목 검색 (티커/이름 → 기본 정보)
├── stock-analyze.md     # 분석 실행 (MI/SI/TI 병렬 호출)
├── stock-report.md      # 리포트 생성 (분석 결과 → 문서화)
└── stock-research.md    # 통합 워크플로우 (검색→분석→리포트)
```

### 2. 레지스트리 도입

**목적**: 분석한 종목 메타데이터 관리

```json
// private/registry.json
{
  "stocks": [
    {
      "id": "000660",
      "slug": "sk-hynix-000660",
      "name": "SK하이닉스",
      "market": "KOSPI",
      "sector": "반도체",
      "last_analyzed": "2025-12-30",
      "analysis_count": 3,
      "status": "active"
    }
  ]
}
```

**경량 인덱스** (중복 체크용):
```
// private/registry-index.txt
000660
005930
NVDA
TSLA
```

### 3. Few-shot 예제 추가

```
private/examples/
├── analysis/
│   ├── 01-semiconductor-hynix.md    # 반도체 분석 예시
│   ├── 02-tech-nvidia.md            # 빅테크 분석 예시
│   ├── 03-ev-tesla.md               # EV 분석 예시
│   └── README.md                    # 예제 사용법
└── sentiment/
    ├── bullish-example.md           # 강세 센티먼트 예시
    └── bearish-example.md           # 약세 센티먼트 예시
```

### 4. 병렬 처리 명시화

**현재**: PI가 MI/SI를 순차 호출

**개선안**: 명령어 레벨에서 병렬 Task 호출
```markdown
# stock-analyze.md에서 병렬 호출 패턴

## 실행 방식
1. 단일 메시지에서 MI + SI + TI Task를 동시 호출
2. 최대 3개 에이전트 병렬 실행
3. 결과 수집 후 통합

## 예시
- Task(MI): 가격/뉴스/재무 수집
- Task(SI): 센티먼트/이상징후 수집
- Task(TI): 기술적 지표 계산
(위 3개를 single message에서 parallel 호출)
```

### 5. Slug 표준화

**형식**: `{종목명}-{티커}` (소문자, 하이픈 구분)

**예시**:
- `sk-hynix-000660`
- `samsung-electronics-005930`
- `nvidia-nvda`
- `tesla-tsla`

---

## 목표 구조 (리팩토링 후)

```
stock-analyzer-advanced/
├── README.md
├── overview.md
│
├── agents/                      # 역할별 에이전트
│   ├── portfolio-intelligence.md   # PI - 오케스트레이터
│   ├── market-intelligence.md      # MI - 시장 데이터
│   ├── sentiment-intelligence.md   # SI - 센티먼트
│   ├── technical-intelligence.md   # TI - 기술적 분석
│   └── financial-ml-analyst.md     # 인프라 개발
│
├── commands/                    # 세분화된 명령어
│   ├── stock-search.md          # 종목 검색
│   ├── stock-analyze.md         # 분석 실행 (병렬)
│   ├── stock-report.md          # 리포트 생성
│   └── stock-research.md        # 통합 워크플로우
│
├── private/                     # 내부 데이터 (gitignore)
│   ├── registry.json            # 종목 메타데이터
│   ├── registry-index.txt       # 경량 인덱스
│   ├── stocks/{slug}/           # 분석 결과
│   │   ├── notes.md
│   │   ├── task_plan.md
│   │   └── analysis.md
│   └── examples/                # Few-shot 예제
│       ├── analysis/
│       └── sentiment/
│
├── utils/                       # Python 유틸리티 (유지)
├── tests/                       # pytest (유지)
└── docs/                        # 문서 (유지)
```

---

## 우선순위

| 순위 | 작업 | 난이도 | 효과 |
|------|------|--------|------|
| P0 | 레지스트리 도입 | 중 | 높음 |
| P1 | 명령어 세분화 | 중 | 높음 |
| P2 | Few-shot 예제 | 낮음 | 중간 |
| P3 | 병렬 처리 강화 | 높음 | 높음 |
| P4 | Slug 표준화 | 낮음 | 낮음 |

---

## 참고: vehicle-contamination-or 핵심 패턴

### 1. Registry 이중화
- `registry.json`: 전체 메타데이터
- `registry-index.txt`: 경량 dedup 체크

### 2. Slug 표준화
- 형식: `{제목-4단어}-{연도}-c{인용수}`
- 예: `coral-rank-consistent-ordinal-2019-c150`

### 3. 병렬 배치 처리
- 최대 8개 동시 처리
- Context 안정성 유지

### 4. Survey 자동 감지
- 제목 키워드로 자동 라우팅
- processor vs survey-processor 분기
