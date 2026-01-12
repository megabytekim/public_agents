# Setup Guide

다른 컴퓨터에서 이 repo를 사용하기 위한 설정 가이드입니다.

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) 설치
- Node.js 18+ (npx 사용)
- Python 3.10+ & uv/uvx (MCP 서버용)

---

## 1. Clone Repository

```bash
git clone https://github.com/megabytekim/public_agents.git
cd public_agents
```

---

## 2. MCP Servers 설정

MCP 서버는 **글로벌 설정** (`~/.claude.json`)에 추가해야 합니다.

### 방법 1: Claude Code CLI로 추가

```bash
# Context7 (라이브러리 문서 검색)
claude mcp add context7 -- npx --yes @upstash/context7-mcp@latest

# Playwright (브라우저 자동화)
claude mcp add playwright -- npx --yes @playwright/mcp@latest --isolated --headless

# Memory (지식 그래프)
claude mcp add memory -- npx --yes @modelcontextprotocol/server-memory

# arXiv (논문 검색)
claude mcp add arxiv-mcp-server -- uvx arxiv-mcp-server

# Jupyter (노트북 실행)
claude mcp add jupyter -- uvx jupyter-mcp-server@latest
```

### 방법 2: 직접 ~/.claude.json 편집

`~/.claude.json`의 `mcpServers` 섹션에 추가:

```json
{
  "mcpServers": {
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["--yes", "@upstash/context7-mcp@latest"],
      "env": {}
    },
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["--yes", "@playwright/mcp@latest", "--isolated", "--headless"],
      "env": {}
    },
    "memory": {
      "type": "stdio",
      "command": "npx",
      "args": ["--yes", "@modelcontextprotocol/server-memory"],
      "env": {}
    },
    "arxiv-mcp-server": {
      "type": "stdio",
      "command": "uvx",
      "args": ["arxiv-mcp-server"],
      "env": {}
    },
    "jupyter": {
      "type": "stdio",
      "command": "uvx",
      "args": ["jupyter-mcp-server@latest"],
      "env": {
        "JUPYTER_URL": "http://localhost:8888",
        "JUPYTER_TOKEN": "YOUR_TOKEN",
        "ALLOW_IMG_OUTPUT": "true"
      }
    }
  }
}
```

### 선택적: Obsidian MCP

Obsidian을 사용하는 경우:

```bash
claude mcp add mcp-obsidian -- uvx mcp-obsidian
```

환경변수 설정 필요:
```json
{
  "env": {
    "OBSIDIAN_API_KEY": "your-api-key",
    "OBSIDIAN_HOST": "127.0.0.1",
    "OBSIDIAN_PORT": "27123",
    "NO_PROXY": "127.0.0.1,localhost"
  }
}
```

---

## 3. 프로젝트 권한 설정

권한 설정은 두 가지 파일로 관리됩니다:

| 파일 | 용도 | Git |
|------|------|-----|
| `.claude/settings.json` | 공유 권한 (팀/다른 PC) | 커밋됨 |
| `.claude/settings.local.json` | 개인 권한 (Obsidian 등) | 무시됨 |

**공유 권한** (이미 설정됨, 수정 불필요):
```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(domain:arxiv.org)",
      "Write(/plugins/vehicle-contamination-or/private/paper/**)"
    ]
  }
}
```

> `/plugins/...`는 **프로젝트 상대 경로**로, 어떤 PC에서든 동일하게 작동합니다.

**개인 권한** (필요시 직접 추가):
```json
{
  "permissions": {
    "allow": [
      "mcp__mcp-obsidian__obsidian_simple_search"
    ]
  }
}
```

---

## 4. 프로젝트 구조

```
public_agents/
├── CLAUDE.md                    # 프로젝트 규칙
├── setup.md                     # 이 파일
├── .claude/
│   ├── settings.json            # 공유 권한 (git 커밋)
│   └── settings.local.json      # 개인 권한 (gitignored)
└── plugins/
    ├── claude-workflows/        # Claude Code 관련 에이전트
    │   └── agents/
    ├── research-papers/         # 논문 분석 에이전트
    │   └── agents/
    ├── stock-analyzer-advanced/ # 주식 분석 에이전트
    │   └── agents/
    ├── vehicle-contamination-or/# 차량 오염도 OR 연구
    │   ├── agents/
    │   └── private/             # 논문 저장소 (gitignore)
    └── web3-ai/                 # Web3/AI 에이전트
        └── agents/
```

---

## 5. Agents 사용법

### Agent 목록 확인

```bash
claude
# 실행 후 /agents 명령어로 확인
```

### Agent 호출 예시

```
# 논문 검색 (vehicle-contamination-or 플러그인)
"ordinal regression 논문 5개 찾아줘"

# 주식 분석 (stock-analyzer-advanced 플러그인)
"삼성전자 기술적 분석해줘"

# CV 논문 분석 (research-papers 플러그인)
"/analyze arxiv:2111.08851"
```

---

## 6. Skills 사용법

```bash
# 스킬 목록 확인
/help

# 사용 예시
/explore claude-code
/explain agents
```

---

## 7. 문제 해결

### MCP 서버 연결 실패

```bash
# MCP 서버 상태 확인
claude mcp list

# 서버 재시작
claude mcp restart <server-name>
```

### 권한 오류

공유 권한은 `.claude/settings.json`에 프로젝트 상대 경로로 설정되어 있어 별도 수정이 필요 없습니다.
개인 권한이 필요하면 `.claude/settings.local.json`에 추가하세요.

### uvx/npx 없음

```bash
# uv 설치 (Python)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js 설치 (npx 포함)
brew install node  # macOS
```

---

## 8. 새 컴퓨터 빠른 설정 스크립트

```bash
#!/bin/bash
# quick-setup.sh

# MCP 서버 일괄 추가
claude mcp add context7 -- npx --yes @upstash/context7-mcp@latest
claude mcp add playwright -- npx --yes @playwright/mcp@latest --isolated --headless
claude mcp add memory -- npx --yes @modelcontextprotocol/server-memory
claude mcp add arxiv-mcp-server -- uvx arxiv-mcp-server

echo "Setup complete! Run 'claude' in the project directory."
```

---

## Related Links

- [Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code)
- [MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Context7](https://github.com/upstash/context7)
