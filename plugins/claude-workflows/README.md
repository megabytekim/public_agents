# Claude Workflows Plugin

Claude Code 사용을 더 효과적으로 만들어주는 워크플로우 및 생산성 도구 모음입니다.

## Commands

### /explain [concept] [--save|--local]
Claude Code 개념을 설명해주는 명령어입니다.

#### 지원하는 개념
| 개념 | 설명 |
|------|------|
| `agents` | AI 서브에이전트 |
| `commands` | 슬래시 명령어 |
| `skills` | 재사용 가능한 전문 지식 |
| `hooks` | 자동화 이벤트 훅 |
| `mcp` | Model Context Protocol |
| `plugins` | 확장 패키지 |
| `memory` | CLAUDE.md 메모리 |
| `model` | AI 모델 옵션 |
| `tools` | 기본 제공 도구 |

#### 저장 옵션
| 플래그 | 저장 위치 | Git |
|--------|----------|-----|
| (없음) | 출력만 | - |
| `--save` | `docs/concepts/` | ✅ 커밋 |
| `--local` | `local/notes/` | 🚫 gitignored |

#### 사용 예시
```
/claude-workflows:explain agents           # 설명만 출력
/claude-workflows:explain hooks --save     # docs/concepts/hooks-guide.md 저장
/claude-workflows:explain mcp --local      # local/notes/mcp-guide.md 저장 (개인용)
```

## Agents

### 1. claude-code-guide-agent
**Claude Code 사용법 전문가**

Claude Code의 기능, 명령어, 플러그인 개발, 설정 방법을 안내합니다.

#### 주요 기능
- 슬래시 명령어 안내 (`/help`, `/model`, `/plugin` 등)
- 플러그인 개발 가이드 (구조, frontmatter, 배포)
- CLAUDE.md 메모리 활용법
- MCP 서버 설정 방법
- Hooks 자동화 설정

#### 사용 예시
```
"Claude Code 명령어 뭐 있어?"
"플러그인 어떻게 만들어?"
"CLAUDE.md 뭐야?"
"MCP 서버 설정하는 법 알려줘"
```

### 2. agentic-dev-trends-agent
**AI 개발 워크플로우 트렌드 검색 전문가**

Claude Code, Cursor, Copilot 등 AI 코딩 도구를 활용한 코드리뷰, 리팩토링, 테스트 워크플로우 트렌드를 검색하고 분석합니다.

#### 검색 토픽
- `code-review`: AI 코드리뷰 트렌드
- `refactoring`: AI 리팩토링 패턴
- `testing`: AI 테스트 자동화
- `agentic`: 에이전틱 코딩 전반
- `all`: 모든 토픽 종합

#### 사용 예시
```
"AI 코드리뷰 트렌드 검색해줘"
"Claude Code 리팩토링 워크플로우 동향"
"에이전틱 코딩 최신 트렌드"
"AI 테스트 자동화 어떻게 하는지"
```

## 예정된 Agents

- **plugin-developer**: 플러그인 개발 자동화 (구조 생성, 검증)
- **project-onboarding**: 새 프로젝트 구조 파악 및 설명
- **workflow-automator**: 반복 작업 자동화 설정

## 디렉토리 구조

```
plugins/claude-workflows/
├── agents/
│   ├── claude-code-guide-agent.md    # Claude Code 가이드 에이전트
│   ├── agentic-dev-trends-agent.md   # AI 개발 워크플로우 트렌드 검색
│   ├── code-analyzer-agent.md        # 외부 코드/repo 분석
│   └── plugin-refactor-agent.md      # 플러그인 구조 리팩토링
├── commands/
│   └── explain.md              # 개념 설명 명령어
├── skills/                      # (예정) 재사용 가능한 지식
├── docs/                        # ✅ Git 커밋 (레퍼런스, 예시)
│   └── concepts/               # /explain --save 저장 위치
└── local/                       # 🚫 Gitignored (개인 노트)
    └── notes/                  # /explain --local 저장 위치
```

## 사용 방법

1. 플러그인 설치 후 자동으로 에이전트 사용 가능
2. Claude Code 관련 질문 시 자동으로 `claude-code-guide-agent` 에이전트 호출
3. 또는 명시적으로 "claude-code-guide 에이전트로 ..." 요청

## 기여하기

새로운 에이전트나 명령어 제안은 언제든 환영합니다!
