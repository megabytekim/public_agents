# Paper Analyst Plugin

학술 논문을 체계적으로 분석하고 인사이트를 제공하는 전문 에이전트 플러그인입니다.

## Agents

### 1. cv-paper-analyst
**Computer Vision 논문 분석 전문가**

최신 Computer Vision 논문을 체계적으로 분석하고, 실무 적용 가능성까지 평가하는 전문 에이전트입니다.

#### 주요 기능
- 📄 PDF/arXiv 논문 자동 분석
- 🔍 관련 연구 및 코드 탐색 (GitHub, 구현체)
- 📊 벤치마크 성능 비교
- 💡 핵심 인사이트 추출
- 🎯 실무 적용성 평가

#### Paper Review Template
체계적인 논문 분석을 위한 8단계 템플릿:

1. **TL;DR**: 한 문단 요약 + Key Takeaway
2. **Research Questions**: 논문이 답하는 핵심 질문들
3. **Preliminaries**: 필수 사전 지식 정의
4. **Motivation**: 연구 동기와 기존 방법의 한계
5. **Method**: 제안 방법의 핵심 요소
6. **Key Takeaway**: 왜 이 방법이 작동하는가?
7. **Contributions**: 논문의 기여도
8. **Limitations**: 장단점 분석

#### 사용 방법

1. **논문 준비**
   ```bash
   # PDF 파일을 input 디렉토리에 넣기
   cp your-paper.pdf plugins/paper-analyst/staging/input/
   ```

2. **에이전트 시작**
   ```bash
   # cv-paper-analyst 에이전트 실행
   agent cv-paper-analyst
   ```

3. **분석 요청**
   ```
   # PDF 파일 분석
   "input 폴더의 YOLO 논문 분석해줘"

   # arXiv 링크 분석
   "https://arxiv.org/abs/2104.00298 논문 분석해줘"

   # 논문 제목으로 검색
   "Vision Transformer 논문 찾아서 분석해줘"
   ```

#### 고급 기능

##### 트렌드 분석
```
"2024년 Computer Vision 트렌드 분석해줘"
"최근 Object Detection 논문들 비교해줘"
```

##### 코드 리뷰
```
"이 논문의 GitHub 구현체 분석해줘"
"재현 가능성 평가해줘"
```

##### 비교 분석
```
"YOLO vs Faster R-CNN 비교 분석해줘"
"최근 Transformer 기반 방법들 비교표 만들어줘"
```

## 디렉토리 구조

```
plugins/paper-analyst/
├── agents/
│   └── cv-paper-analyst.md    # CV 논문 분석 에이전트
├── staging/
│   ├── input/                 # 📥 논문 PDF 파일 업로드
│   ├── analysis/              # 🔬 분석 중간 결과
│   └── memory/                # 🧠 분석 히스토리 저장
└── results/                   # 📊 최종 분석 보고서
```

## 워크플로우 예시

### 단일 논문 심층 분석
1. PDF 파일을 `staging/input/`에 업로드
2. **cv-paper-analyst**로 Template 기반 분석
3. 관련 코드 및 구현체 탐색
4. 실무 적용성 평가
5. 결과를 `results/`에 마크다운으로 저장

### 연구 트렌드 파악
1. 특정 주제 키워드 제공
2. **cv-paper-analyst**가 최신 논문들 검색
3. 주요 논문들 비교 분석
4. 트렌드 리포트 생성

### 논문 구현 검증
1. 논문과 함께 구현 검증 요청
2. GitHub 레포지토리 자동 탐색
3. 코드 구조 및 사용법 분석
4. 재현 가능성 보고서 작성

## MCP Skills 활용

### WebSearch
- 최신 논문 검색
- 관련 연구 탐색
- 저자 정보 수집
- 인용 관계 파악

### Playwright
- GitHub 코드 탐색
- arXiv 페이지 접근
- 벤치마크 리더보드 확인
- 블로그/튜토리얼 수집

### Context7
- PyTorch/TensorFlow 구현 예제
- 관련 라이브러리 문서
- API 레퍼런스 확인
- 코드 스니펫 수집

## 실무 적용성 평가 기준

| 항목 | 설명 | 평가 요소 |
|-----|------|----------|
| **성능** | SOTA 대비 성능 | 정확도, 속도, 효율성 |
| **구현 난이도** | 재현 복잡도 | 코드 가용성, 문서화 수준 |
| **일반화** | 도메인 확장성 | 다양한 데이터셋 성능 |
| **실용성** | 제품 적용 가능성 | 리소스 요구사항, 라이센스 |
| **혁신성** | 새로운 아이디어 | 패러다임 전환, 창의성 |

## 팁과 모범 사례

### 효과적인 논문 분석
- 먼저 Abstract와 Conclusion 읽고 전체 맥락 파악
- Figure와 Table 중심으로 핵심 아이디어 이해
- Related Work 섹션으로 연구 배경 파악
- Ablation Study로 각 컴포넌트 중요도 평가

### 메모리 활용
- 분석한 논문들은 자동으로 `memory/`에 저장
- 이전 분석과 비교하여 연구 발전 추적
- 관련 논문 네트워크 구축

### 결과물 관리
- 모든 분석은 `results/`에 마크다운으로 저장
- 날짜별, 주제별 정리 가능
- 팀과 공유 가능한 형식

## 지원 예정 기능

- 📚 **ml-paper-analyst**: 일반 ML 논문 분석
- 🤖 **nlp-paper-analyst**: NLP 논문 분석
- 🧬 **bio-paper-analyst**: BioML 논문 분석
- 📈 **paper-trend-tracker**: 자동 트렌드 추적
- 🔄 **paper-reproduce**: 논문 재현 자동화

## 예시 출력

```markdown
# YOLO v8: 실시간 객체 탐지의 새로운 기준

## TL;DR
YOLO v8은 anchor-free 설계와 개선된 손실 함수를 통해 실시간 객체 탐지에서
SOTA 성능을 달성했습니다. 이전 버전 대비 정확도는 5% 향상, 속도는 20% 개선되었으며,
다양한 하드웨어 환경에서 효율적으로 동작합니다.
**Key Takeaway: 실시간 처리와 높은 정확도를 동시에 달성한 실용적 모델**

## Research Questions
1. 어떻게 anchor-free 방식이 성능 향상을 가져왔는가?
2. 실시간 처리 속도를 유지하면서 정확도를 높인 비결은?
3. 다양한 객체 크기에 대한 robustness는 어떻게 확보했나?
...
```

## 문의 및 피드백

논문 분석을 통해 최신 연구를 깊이 있게 이해하고, 실무에 적용해보세요! 🚀
