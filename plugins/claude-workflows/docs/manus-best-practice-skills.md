# Best Practice: Skills 구조와 3-File Pattern

복잡한 작업을 위한 파일 기반 워크플로우 패턴 가이드.

## 참조 프로젝트

| 항목 | 내용 |
|------|------|
| **소스** | https://github.com/OthmanAdi/planning-with-files |
| **유형** | Claude Code Skill |
| **영감** | Manus AI Context Engineering |

## 핵심 패턴: 3-File Pattern

복잡한 작업 시 3개의 마크다운 파일로 상태 관리:

| 파일 | 용도 | 업데이트 시점 |
|------|------|--------------|
| `task_plan.md` | 목표, 단계별 체크리스트, 에러 기록 | 단계 완료 즉시 |
| `notes.md` | 리서치 결과, 중간 발견사항 | 정보 수집 시 append |
| `[deliverable].md` | 최종 산출물 | 작업 완료 시 |

**핵심 인사이트**: 마크다운 파일 = 디스크상의 작업 메모리

## 워크플로우

```
1. task_plan.md 생성 (목표 + 단계)
     ↓
2. 리서치 → notes.md 기록 → task_plan.md 갱신
     ↓
3. notes.md 검토 → 산출물 생성 → task_plan.md 갱신
     ↓
4. 최종 결과물 전달
```

## 비타협적 규칙

1. **계획 우선**: 복잡한 작업 시작 전 반드시 `task_plan.md` 생성
2. **결정 전 읽기**: 중요 결정 전 항상 계획 파일 다시 읽기
3. **즉시 업데이트**: 단계 완료 즉시 체크박스 업데이트
4. **파일에 저장**: 큰 내용은 컨텍스트가 아닌 파일에 저장
5. **에러 문서화**: 모든 에러를 계획 파일에 기록

## 적용 기준

**사용해야 할 때:**
- 5단계 이상 작업
- 리서치가 포함된 태스크
- 멀티파일 수정
- 여러 도구 호출이 필요한 워크플로우

**사용하지 않아도 될 때:**
- 간단한 질문
- 단일 파일 수정
- 빠른 조회

## 안티패턴

| 안티패턴 | 문제점 |
|----------|--------|
| TodoWrite로 대체 | 세션 종료 시 휘발, 상세 기록 불가 |
| 컨텍스트 스터핑 | 큰 출력을 컨텍스트에 밀어넣기 |
| 목표 망각 | 목표를 다시 검토하지 않아 드리프트 발생 |
| 성급한 실행 | 계획 완성 전 실행 시작 |
| 에러 은폐 | 실패를 기록하지 않고 넘어가기 |

## Manus Context Engineering 6원칙

| 원칙 | 설명 | 구현 |
|------|------|------|
| Filesystem as Memory | 파일을 무제한 작업 메모리로 활용 | 큰 콘텐츠는 파일에, 컨텍스트엔 경로만 |
| Attention Manipulation | "lost in the middle" 방지 | task_plan.md 주기적 재확인 |
| Keep Failure Traces | 에러와 복구 시도 기록 | Errors Encountered 섹션 |
| Avoid Few-Shot Overfitting | 맹목적 복붙 방지 | 표현 변경, 재조정 |
| Stable Prefixes for Cache | 캐시 히트 우선 | 정적 콘텐츠 앞에, append-only |
| Append-Only Context | 이전 메시지 수정 금지 | 항상 추가만 |

## 설치 및 사용

### 전역 설치 (권장)

```bash
mkdir -p ~/.claude/skills
cd ~/.claude/skills
git clone https://github.com/OthmanAdi/planning-with-files.git
```

### 사용법

복잡한 작업 시 **현재 작업 디렉토리**에 바로 생성:

```
./                       # 현재 working directory
├── task_plan.md         # 계획 + 진행 추적
├── notes.md             # 리서치 결과
└── [deliverable].md     # 최종 산출물
```

### TodoWrite와의 관계

| 작업 유형 | 사용 도구 |
|----------|----------|
| 복잡한 작업 (5단계+) | `task_plan.md` (주력) |
| 단순한 작업 | TodoWrite OK |

## 템플릿

### task_plan.md

```markdown
# [작업명]

## 목표
[한 문장으로 목표 정의]

## 단계
- [ ] Phase 1: 계획 수립
- [ ] Phase 2: 정보 수집
- [ ] Phase 3: 실행
- [ ] Phase 4: 검증 및 전달

## 핵심 질문
- [답해야 할 질문들]

## 결정 사항
- [내린 결정과 근거]

## 발생한 에러
- [에러 내용과 해결 방법]

## 현재 상태
작업 중: Phase 1
마지막 업데이트: YYYY-MM-DD
```

### notes.md

```markdown
# 작업 노트

## 수집한 정보
### 출처 1
- URL:
- 핵심 내용:

## 발견사항
- [카테고리별 정리]

## 결정 근거
- [왜 이 방식을 선택했는지]
```

---

**참조**: [planning-with-files](https://github.com/OthmanAdi/planning-with-files)
**검증일**: 2026-01-07
