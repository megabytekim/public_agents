# Vehicle Contamination OR Plugin

차량 오염 탐지를 위한 Object Detection + Ordinal Regression 연구 및 구현 지원 플러그인입니다.

## 🎯 Project Background

### 프로젝트 목표
차량 이미지에서 **세차 필요 여부**를 자동 판별하는 시스템 구축

### 파이프라인 (Chained Task)
```
입력 이미지 → [Car Part Detection] → [부위별 Ordinal Regression] → Threshold 판정 → 세차 권장 여부
```

### 부위 (약 20개)
후드, 루프, 트렁크, 앞/뒷범퍼, 좌/우 도어, 좌/우 펜더, 사이드미러, 휠(4개), 전면/후면유리 등

### 오염도 레벨
| Level | 설명 |
|-------|------|
| Lv1 | 깨끗 |
| Lv2 | 경미한 오염 |
| Lv3 | 중간 오염 |
| Lv4 | 심한 오염 |

### 데이터 현황
- **규모**: Balanced set X만장
- **라벨링**: 업체 진행 중
- **오염 유형**: 먼지/흙, 새똥/나뭇잎, 빗물 자국 등

### 기술 스택
- **Framework**: PyTorch
- **배포**: 일배치 서버 처리
- **현재 상황**: MLOps 플랫폼에 Image Regression 구현됨, **Ordinal Regression 미구현**

### 연구 목적
> 부위별 4단계 오염도 분류에 적합한 **Ordinal Regression 기법** 탐색

## Agents

### Agent Architecture

```
paper-researcher (Orchestrator, sonnet)
       │
       ├── paper-finder (haiku) ──→ 검색만, JSON 반환
       │
       └── paper-processor (sonnet) ──→ 1개씩 PDF+summary
              ↑ 병렬 호출 가능

ml-agent (standalone, sonnet) ──→ 벤치마크 + 코드 생성
```

### 1. paper-researcher (Orchestrator)
**논문 리서치 오케스트레이터**

sub-agent를 조율하여 대량 논문 검색/처리를 수행합니다.

#### 주요 기능
- registry.json 관리 (중복 방지)
- paper-finder 호출 → 검색 결과 수집
- paper-processor 병렬 호출 → PDF/summary 처리
- 최종 결과 집계 및 보고

#### Sub-agents

| Agent | 모델 | 역할 |
|-------|------|------|
| paper-finder | haiku | 검색 전담, JSON 목록 반환 |
| paper-processor | sonnet | 1개 논문 PDF+summary 처리 |

#### 장점
- **Context 분산**: 30개 논문도 각 processor가 독립 context 사용
- **비용 절감**: finder는 haiku (검색만 하므로 가벼움)
- **실패 격리**: 개별 processor 실패해도 나머지 계속 진행
- **병렬 처리**: 여러 processor 동시 호출 가능

#### 검색 대상 도메인
- **High**: Vehicle damage, Surface defect, Quality grading
- **Medium**: Diabetic retinopathy, Age estimation
- **Low**: Aesthetic quality, Food quality

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
│   ├── paper-researcher.md   # 오케스트레이터 (sub-agent 조율)
│   ├── paper-finder.md       # 검색 전담 sub-agent
│   ├── paper-processor.md    # 처리 전담 sub-agent
│   └── ml-agent.md           # 벤치마크 + 코드 생성
├── private/                  # gitignore (내부 정보)
│   ├── registry.json         # 논문 인덱스 (중복 방지)
│   ├── paper/                # 논문별 폴더
│   │   └── {slug}-c{N}/      # 폴더명에 citation 포함
│   │       ├── paper.pdf     # 원본 PDF
│   │       ├── summary.md    # brief_summary 형식
│   │       └── survey_summary.md  # survey 논문용
│   ├── examples/             # Few-shot 예시
│   │   ├── brief_summary/    # 방법론 요약 예시
│   │   └── survey_summary/   # survey 요약 예시
│   └── paper-examples/       # 분석 예시 템플릿
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
"ordinal regression 논문 30개 찾아줘"
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
```
1. paper-researcher로 대량 논문 검색 (30개+)
   └── paper-finder: 검색
   └── paper-processor: PDF+summary (병렬)
2. private/registry.json에 자동 등록
3. ml-agent로 벤치마크 데이터셋 수집
4. boilerplate 코드 생성
5. 별도 repo에서 실제 구현
```

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
