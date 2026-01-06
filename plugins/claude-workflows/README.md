# Claude Workflows Plugin

Claude Code 사용을 더 효과적으로 만들어주는 워크플로우 및 생산성 도구 모음입니다.

## Commands

### /explain [concept]
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

#### 사용 예시
```
/claude-workflows:explain agents
/claude-workflows:explain hooks
/claude-workflows:explain mcp
```

## Agents

### 1. claude-code-guide
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

## 예정된 Agents

- **plugin-developer**: 플러그인 개발 자동화 (구조 생성, 검증)
- **project-onboarding**: 새 프로젝트 구조 파악 및 설명
- **workflow-automator**: 반복 작업 자동화 설정

## 디렉토리 구조

```
plugins/claude-workflows/
├── agents/
│   └── claude-code-guide.md    # Claude Code 가이드 에이전트
├── commands/                    # (예정) 유틸리티 명령어
└── skills/                      # (예정) 재사용 가능한 지식
```

## 사용 방법

1. 플러그인 설치 후 자동으로 에이전트 사용 가능
2. Claude Code 관련 질문 시 자동으로 `claude-code-guide` 에이전트 호출
3. 또는 명시적으로 "claude-code-guide 에이전트로 ..." 요청

## 기여하기

새로운 에이전트나 명령어 제안은 언제든 환영합니다!
