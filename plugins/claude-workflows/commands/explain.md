---
description: Claude Code 개념 설명. 사용법 - /explain [concept] [--save|--local] (예- agents, commands, skills, hooks, mcp)
argument-hint: [concept] [--save|--local]
allowed-tools: Read, Write
---

# Claude Code 개념 설명

사용자 입력: **$ARGUMENTS**

## 파싱 규칙
- `$1` = 개념 (agents, commands, skills, hooks, mcp, plugins, memory, model, tools)
- `--save` 플래그 → `plugins/claude-workflows/docs/concepts/` 에 저장 (Git 커밋용)
- `--local` 플래그 → `plugins/claude-workflows/local/notes/` 에 저장 (개인용, gitignored)
- 플래그 없음 → 설명만 출력

## 저장 시 파일명
- `{concept}-guide.md` 형식 (예: `agents-guide.md`, `hooks-guide.md`)

아래 개념들 중 해당하는 내용을 **한국어로** 간결하게 설명해주세요.
저장 플래그가 있으면 설명 내용을 해당 경로에 마크다운 파일로 저장하세요.

---

## 📚 개념 사전

### agents (에이전트)
**정의**: 특정 작업에 특화된 AI 서브에이전트

**특징**:
- Claude가 작업에 따라 자동으로 위임
- 별도의 컨텍스트 윈도우에서 실행
- 커스텀 시스템 프롬프트 사용 가능
- 도구 제한 가능 (`tools` 필드)

**파일 위치**: `plugins/xxx/agents/agent-name.md`

**Frontmatter 예시**:
```yaml
---
name: my-agent
description: 언제 이 에이전트를 사용하는지 설명
tools: Read, Grep, Glob
model: sonnet
skills: skill1, skill2
---
```

**호출 방식**: Claude가 자동 위임 또는 "my-agent 에이전트로 해줘"

---

### commands (명령어)
**정의**: `/`로 시작하는 슬래시 명령어

**특징**:
- 사용자가 직접 `/plugin:command`로 호출
- 인자 전달 가능 (`$ARGUMENTS`, `$1`, `$2`)
- 빠른 반복 작업에 적합

**파일 위치**: `plugins/xxx/commands/command-name.md`

**Frontmatter 예시**:
```yaml
---
description: 명령어 설명
argument-hint: [arg1] [arg2]
allowed-tools: Bash(git:*), Read
---
```

**호출 방식**: `/plugin-name:command-name arg1 arg2`

---

### skills (스킬)
**정의**: 에이전트가 사용하는 전문 지식/가이드

**특징**:
- Claude가 필요할 때 자동으로 선택
- 메인 대화 컨텍스트와 공유 (에이전트와 다름)
- Progressive disclosure: SKILL.md는 간결하게, 상세 내용은 별도 파일

**파일 위치**: `plugins/xxx/skills/skill-name/SKILL.md`

**Frontmatter 예시**:
```yaml
---
name: my-skill
description: 무엇을 하고 언제 사용하는지
allowed-tools: Read, Bash(python:*)
---
```

---

### hooks (훅)
**정의**: 특정 이벤트 발생 시 자동 실행되는 스크립트

**주요 이벤트**:
| 이벤트 | 시점 |
|--------|------|
| `PreToolUse` | 도구 사용 전 |
| `PostToolUse` | 도구 사용 후 |
| `UserPromptSubmit` | 프롬프트 제출 시 |
| `SessionStart/End` | 세션 시작/종료 |

**파일 위치**: `hooks/hooks.json` 또는 `plugin.json` 내 인라인

**예시**:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{ "type": "command", "command": "./scripts/format.sh" }]
    }]
  }
}
```

---

### mcp (Model Context Protocol)
**정의**: 외부 도구/서비스를 Claude에 연결하는 프로토콜

**용도**:
- 데이터베이스 연결
- API 호출
- 커스텀 도구 추가

**파일 위치**: `.mcp.json`

**예시**:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["@company/mcp-server"]
    }
  }
}
```

**관리 명령어**: `/mcp`

---

### plugins (플러그인)
**정의**: commands, agents, skills, hooks를 묶은 확장 패키지

**구조**:
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json      # 메타데이터 (필수)
├── commands/
├── agents/
├── skills/
├── hooks/
└── .mcp.json
```

**관리 명령어**: `/plugin`

**설치**: `/install-plugin [url]`

---

### memory (메모리 / CLAUDE.md)
**정의**: 프로젝트 컨텍스트를 저장하는 마크다운 파일

**위치 우선순위**:
1. `./CLAUDE.md` (현재 디렉토리)
2. `~/.claude/CLAUDE.md` (전역)

**저장 내용**:
- 프로젝트 구조
- 코딩 컨벤션
- 자주 사용하는 명령어
- 중요 파일 위치

**관리 명령어**: `/memory`, `/init`

---

### model (모델)
**옵션**:
| 별칭 | 설명 |
|------|------|
| `sonnet` | Claude 3.5 Sonnet (기본, 빠름) |
| `opus` | Claude Opus (강력, 복잡한 작업) |
| `haiku` | Claude Haiku (경량, 간단한 작업) |

**변경 명령어**: `/model`

---

### tools (도구)
**기본 제공 도구**:
| 도구 | 용도 |
|------|------|
| `Read` | 파일 읽기 |
| `Write` | 파일 쓰기 |
| `Edit` | 파일 수정 |
| `Glob` | 파일 패턴 검색 |
| `Grep` | 내용 검색 |
| `Bash` | 쉘 명령 실행 |
| `WebFetch` | 웹 페이지 가져오기 |
| `WebSearch` | 웹 검색 |
| `Task` | 서브에이전트 실행 |

**제한 방법**: `allowed-tools` 또는 `tools` frontmatter 필드

---

## 응답 가이드

1. `$ARGUMENTS`에 해당하는 개념을 찾아 설명
2. 없는 개념이면 가장 유사한 것 제안
3. 예시와 함께 실용적으로 설명
4. 관련 명령어가 있으면 함께 안내
