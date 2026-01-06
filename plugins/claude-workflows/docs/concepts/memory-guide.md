# CLAUDE.md 메모리 파일 가이드

프로젝트 컨텍스트를 저장하여 Claude가 기억하게 하는 설정 파일입니다.

---

## 파일 위치 & 우선순위

| 순위 | 위치 | 범위 | 공유 |
|------|------|------|------|
| 1 (최우선) | `./CLAUDE.local.md` | 프로젝트 + 개인 | 🚫 (gitignored) |
| 2 | `./.claude/rules/*.md` | 프로젝트 | ✅ 팀 |
| 3 | `./CLAUDE.md` 또는 `./.claude/CLAUDE.md` | 프로젝트 | ✅ 팀 |
| 4 | `~/.claude/CLAUDE.md` | 사용자 전역 | 🚫 개인 |
| 5 (최하위) | 시스템 레벨 | Enterprise | 조직 전체 |

**우선순위 규칙**: 숫자가 낮을수록 우선순위 높음 (덮어씀)

---

## 파일별 용도

### `./CLAUDE.md` (프로젝트 메모리)
팀과 공유하는 프로젝트 설정
```markdown
# 프로젝트 가이드

## 빌드 명령어
- `npm run build` - 프로덕션 빌드
- `npm test` - 테스트 실행

## 코드 스타일
- 2칸 들여쓰기
- 세미콜론 사용
- 함수명은 camelCase
```

### `./CLAUDE.local.md` (개인 프로젝트 설정)
Git에 커밋하지 않는 개인 설정
```markdown
# 내 설정 (gitignored)

- 테스트 서버: http://localhost:3000
- 내 API 키 위치: ~/.env.local
- 선호하는 테스트 데이터: user_123
```

### `~/.claude/CLAUDE.md` (사용자 전역)
모든 프로젝트에 적용되는 개인 설정
```markdown
# 전역 설정

- 한국어로 답변
- 커밋 메시지는 영어로
- 코드 주석은 간결하게
```

### `./.claude/rules/*.md` (모듈형 규칙)
주제별로 분리된 규칙 파일
```
.claude/rules/
├── code-style.md     # 코드 스타일
├── testing.md        # 테스트 규칙
├── api.md            # API 개발 규칙
└── security.md       # 보안 규칙
```

---

## 경로별 규칙 (Path-specific)

특정 파일에만 적용되는 규칙:

```markdown
---
paths: src/api/**/*.ts
---

# API 규칙

- 모든 엔드포인트에 입력 검증 필수
- OpenAPI 주석 포함
```

**지원 패턴**:
- `**/*.ts` - 모든 TS 파일
- `src/**/*` - src 하위 전체
- `{src,lib}/**/*.ts` - 복수 경로

---

## 파일 임포트

다른 파일 참조하기:

```markdown
프로젝트 개요는 @README 참고
npm 명령어는 @package.json 참고

자세한 가이드: @docs/guidelines.md
```

**제한사항**:
- 코드 블록 내에서는 임포트 안 됨
- 최대 5단계 깊이까지

---

## 관리 명령어

| 명령어 | 설명 |
|--------|------|
| `/init` | CLAUDE.md 초기화 (프로젝트 정보 자동 생성) |
| `/memory` | 메모리 파일 편집기 열기 |

---

## 권장 내용

### 포함하면 좋은 것
- 빌드/테스트/배포 명령어
- 코드 스타일 규칙
- 아키텍처 패턴
- 네이밍 컨벤션
- Git 워크플로우

### 좋은 예시 vs 나쁜 예시

| 나쁜 예시 | 좋은 예시 |
|----------|----------|
| "코드를 잘 작성해라" | "2칸 들여쓰기, 세미콜론 사용" |
| "테스트 잘 해라" | "`npm test` 실행 후 커버리지 80% 이상" |
| "보안 신경 써라" | "API 키는 환경변수로, 하드코딩 금지" |

---

## 대규모 프로젝트 구조

```
my-project/
├── CLAUDE.md                    # 메인 설정
├── CLAUDE.local.md              # 개인 설정 (gitignored)
└── .claude/
    ├── CLAUDE.md                # 대안 위치
    └── rules/
        ├── frontend/
        │   ├── react.md
        │   └── styles.md
        ├── backend/
        │   ├── api.md
        │   └── database.md
        └── general.md
```

---

## 자동 검색 동작

Claude Code는 현재 디렉토리에서 **위로 올라가며** 모든 CLAUDE.md 검색:

```
/home/user/project/src/components/  ← 현재 위치
         ↓ 검색
/home/user/project/src/CLAUDE.md
/home/user/project/CLAUDE.md
/home/user/CLAUDE.md
~/.claude/CLAUDE.md
```

---

## 요약

| 용도 | 파일 |
|------|------|
| 팀 공유 설정 | `./CLAUDE.md` |
| 개인 프로젝트 설정 | `./CLAUDE.local.md` |
| 전역 개인 설정 | `~/.claude/CLAUDE.md` |
| 모듈형 규칙 | `./.claude/rules/*.md` |
