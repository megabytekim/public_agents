# Vehicle Contamination OR Plugin

차량 오염 탐지를 위한 Object Detection + Ordinal Regression 연구 및 구현 지원 플러그인입니다.

## Domain

**차량 오염 탐지 (Vehicle Contamination Detection)**
- **오염 위치 탐지 (Object Detection)**: 차량 이미지에서 오염된 부분을 탐지
- **오염도 등급 측정 (Ordinal Regression)**: 탐지된 오염의 심각도를 순서형 등급으로 분류

> 현재 MLOps 플랫폼에 image regression은 구현되어 있으나, ordinal regression은 미구현 상태

## Agents

### 1. paper-researcher
**논문/사례 리서치 전문 에이전트**

OR + OD 관련 논문 및 유사 도메인 사례를 검색합니다.

#### 주요 기능
- 다양한 소스에서 논문 검색 (arXiv, Semantic Scholar, Google Scholar, IEEE)
- private/ 폴더의 읽은 논문 참조하여 중복 제외
- 다양한 도메인의 OR+OD 사례 수집

#### 검색 대상 도메인
- Vehicle damage detection (차량 손상 탐지)
- Diabetic retinopathy grading (당뇨망막병증 등급)
- Product quality grading (제품 품질 등급)
- Skin condition scoring (피부 상태 점수)
- Surface defect detection (표면 결함 탐지)
- Food quality assessment (식품 품질 평가)
- Age estimation (나이 추정)
- Aesthetic quality assessment (미적 품질 평가)

#### 이미 알고 있는 방법론
- **SORD** (Soft Ordinal Regression)
- **CORN** (Conditional Ordinal Regression)
- **ORD2SEQ** (Ordinal to Sequence)

### 2. ml-agent
**벤치마크 수집 + 코드 생성 에이전트**

공개 벤치마크 데이터셋을 찾고 PyTorch boilerplate 코드를 생성합니다.

#### 주요 기능
- 공개 벤치마크 데이터셋 검색 및 수집
- PyTorch 기반 boilerplate 코드 생성
- 찾은 논문 내용 바탕으로 구현

#### 검색 소스
- Kaggle
- Papers with Code
- GitHub
- Hugging Face Datasets

## Directory Structure

```
plugins/vehicle-contamination-or/
├── agents/
│   ├── paper-researcher.md   # 논문/사례 검색 에이전트
│   └── ml-agent.md           # 벤치마크 + 코드 생성 에이전트
├── private/                  # gitignore (내부 정보)
│   ├── read-papers.md        # 이미 읽은 논문 목록
│   └── requirements.md       # 내부 요구사항
├── results/                  # 분석 결과 저장
├── README.md
└── .gitignore
```

## Usage

### 논문 리서치
```bash
# paper-researcher 에이전트 실행
agent paper-researcher

# 사용 예시
"ordinal regression object detection 논문 찾아줘"
"차량 손상 탐지 관련 최신 연구 검색해줘"
"medical image grading 사례 찾아줘"
```

### 벤치마크 + 코드 생성
```bash
# ml-agent 에이전트 실행
agent ml-agent

# 사용 예시
"ordinal regression 벤치마크 데이터셋 찾아줘"
"CORN 방식으로 PyTorch 코드 생성해줘"
"찾은 데이터셋으로 학습 코드 만들어줘"
```

## Workflow

### 연구 워크플로우
1. **paper-researcher**로 관련 논문 검색
2. private/에 핵심 내용 정리
3. **ml-agent**로 벤치마크 데이터셋 수집
4. boilerplate 코드 생성
5. 별도 repo에서 실제 구현

### 성능 검증
- 공개 벤치마크 데이터셋으로 성능 검증
- 실제 구현은 별도 repo에서 진행

## Private Folder

`private/` 폴더는 gitignore 처리되어 있습니다.
- 회사 내부 정보
- 읽은 논문 상세 정리
- 프로젝트 요구사항

## Tech Stack

- **Language**: Python
- **Framework**: PyTorch
- **Task**: Object Detection + Ordinal Regression
