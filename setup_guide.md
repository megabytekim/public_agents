# Public Agents - Setup Guide

다른 PC에서 이 프로젝트 환경을 재현하기 위한 완전한 셋업 가이드입니다.

---

## Table of Contents

1. [Current Environment Status](#current-environment-status)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [MCP Server Configuration](#mcp-server-configuration)
5. [Plugin Installation](#plugin-installation)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Current Environment Status

### System Info (Reference Machine)
| Item | Value |
|------|-------|
| OS | macOS Darwin 23.5.0 |
| Platform | Apple Silicon (darwin arm64) |
| Claude Code Version | 2.1.2+ |

### Installed Tools
| Tool | Version | Path |
|------|---------|------|
| Python | 3.8.10 | `~/.pyenv/shims/python3` |
| Node.js | v24.6.0 | `/opt/homebrew/bin/node` |
| npm | 11.5.1 | - |
| uv | 0.8.6 | `uv`, `uvx` |
| Homebrew | 5.0.9 | `/opt/homebrew/bin/brew` |
| jq | 1.8.1 | `/opt/homebrew/bin/jq` |

### Enabled Plugins
| Plugin | Status |
|--------|--------|
| stock-analyzer-advanced | Enabled |
| research-papers | Enabled |
| claude-workflows | Enabled |
| web3-ai | Enabled |
| vehicle-contamination-or | Enabled |

### MCP Servers
| Server | Purpose |
|--------|---------|
| mcp-obsidian | Obsidian vault integration |
| playwright | Browser automation |
| context7 | Library documentation |
| memory | Knowledge graph storage |
| arxiv | Academic paper search/download |
| yfinance | Stock market data |

---

## Prerequisites

### 1. Required Software

```bash
# macOS (Homebrew)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add to PATH (Apple Silicon)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 2. Node.js & npm
```bash
brew install node
# Verify
node --version  # v24.x.x
npm --version   # 11.x.x
```

### 3. Python & pyenv
```bash
brew install pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Install Python
pyenv install 3.8.10
pyenv global 3.8.10
```

### 4. uv (Modern Python package manager)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Verify
uv --version
uvx --version
```

### 5. jq (JSON processor - required for hooks)
```bash
brew install jq
```

### 6. Obsidian (Optional but recommended)
- Download from: https://obsidian.md/
- Install Local REST API plugin (for mcp-obsidian)

---

## Step-by-Step Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/megabytekim/public_agents.git ~/public_agents
cd ~/public_agents
```

### Step 2: Install Claude Code

```bash
# Via npm (global installation)
npm install -g @anthropic-ai/claude-code

# Verify
claude --version
```

### Step 3: Install Python Dependencies

```bash
cd ~/public_agents/plugins/stock-analyzer-advanced/utils
pip install -r requirements.txt
```

**requirements.txt 내용:**
```
pykrx>=1.0.0
pandas>=1.5.0
numpy>=1.20.0
pytest>=7.0.0
pytest-mock>=3.0.0
```

**추가 권장 패키지:**
```bash
pip install beautifulsoup4 lxml requests
```

### Step 4: Setup Notification Hook (Optional)

```bash
# Create hooks directory
mkdir -p ~/.claude/hooks

# Create notify.sh
cat > ~/.claude/hooks/notify.sh << 'EOF'
#!/bin/bash
# Claude Code Notification Hook
LOG_FILE="/tmp/claude-hook-debug.log"
echo "=== $(date) ===" >> "$LOG_FILE"

JSON_INPUT=$(cat)
echo "Input: $JSON_INPUT" >> "$LOG_FILE"

NOTIFICATION_TYPE=$(echo "$JSON_INPUT" | jq -r '.notification_type // empty')
MESSAGE=$(echo "$JSON_INPUT" | jq -r '.message // "Claude Code 알림"')

case "$NOTIFICATION_TYPE" in
  "permission_prompt")
    TITLE="Claude Code"
    SUBTITLE="권한 승인 필요"
    SOUND="Ping"
    ;;
  "idle_prompt")
    TITLE="Claude Code"
    SUBTITLE="입력 대기 중"
    SOUND="Blow"
    ;;
  *)
    exit 0
    ;;
esac

osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\" subtitle \"$SUBTITLE\" sound name \"$SOUND\"" 2>> "$LOG_FILE"
exit 0
EOF

# Make executable
chmod +x ~/.claude/hooks/notify.sh
```

---

## MCP Server Configuration

### Claude Code Settings (`~/.claude/settings.json`)

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/YOUR_USERNAME/.claude/hooks/notify.sh",
            "timeout": 10
          }
        ]
      }
    ]
  },
  "mcpServers": {
    "mcp-obsidian": {
      "command": "/opt/homebrew/bin/uvx",
      "args": ["mcp-obsidian"],
      "env": {
        "OBSIDIAN_API_KEY": "YOUR_OBSIDIAN_API_KEY",
        "OBSIDIAN_HOST": "127.0.0.1",
        "OBSIDIAN_PORT": "27123",
        "NO_PROXY": "127.0.0.1,localhost"
      }
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "arxiv": {
      "command": "uv",
      "args": [
        "tool", "run", "arxiv-mcp-server",
        "--storage-path", "/Users/YOUR_USERNAME/public_agents/plugins/vehicle-contamination-or/private/paper"
      ]
    },
    "yfinance": {
      "command": "uvx",
      "args": ["yfmcp@latest"]
    }
  }
}
```

> **Note**: `YOUR_USERNAME`을 실제 사용자명으로 변경하세요.

### Obsidian Local REST API Setup (mcp-obsidian용)

1. Obsidian 실행
2. Settings > Community plugins > Browse
3. "Local REST API" 검색 및 설치
4. 플러그인 활성화
5. Settings에서 API Key 복사
6. `~/.claude/settings.json`의 `OBSIDIAN_API_KEY`에 붙여넣기

### MCP Server 별 설치 명령

```bash
# playwright (브라우저 자동화)
npx @playwright/mcp@latest --help

# context7 (라이브러리 문서)
npx @upstash/context7-mcp@latest

# memory (지식 그래프)
npx @modelcontextprotocol/server-memory

# arxiv (논문 검색)
uv tool install arxiv-mcp-server

# yfinance (주식 데이터)
uvx yfmcp@latest

# mcp-obsidian (Obsidian 연동)
uvx mcp-obsidian
```

---

## Plugin Installation

### Method 1: Via Claude Code Marketplace (Recommended)

```bash
cd ~/public_agents
claude

# Claude Code 내에서:
# /install-plugin megabytekim-agents
```

### Method 2: Manual Installation

플러그인은 이미 repository에 포함되어 있습니다. `~/.claude/settings.json`에서 활성화하면 됩니다:

```json
{
  "enabledPlugins": {
    "stock-analyzer-advanced@megabytekim-agents": true,
    "research-papers@megabytekim-agents": true,
    "claude-workflows@megabytekim-agents": true,
    "web3-ai@megabytekim-agents": true,
    "vehicle-contamination-or@megabytekim-agents": true
  }
}
```

### Plugin Structure

```
plugins/
├── stock-analyzer-advanced/    # 주식 분석 (TI/MI/SI/FI)
│   ├── agents/
│   │   ├── technical-intelligence.md
│   │   ├── market-intelligence.md
│   │   ├── sentiment-intelligence.md
│   │   ├── financial-intelligence.md
│   │   └── financial-ml-analyst.md
│   ├── commands/
│   │   └── stock-analyze.md
│   ├── utils/                  # Python utilities
│   │   ├── data_fetcher.py
│   │   ├── indicators.py
│   │   ├── ti_analyzer.py
│   │   ├── financial_scraper.py
│   │   └── requirements.txt
│   └── watchlist/              # 분석 결과 저장
│
├── research-papers/            # 논문 분석
├── claude-workflows/           # Claude Code 워크플로우
├── web3-ai/                    # Web3/AI 개발
└── vehicle-contamination-or/   # 차량 오염도 연구
```

---

## Verification

### 1. Check Claude Code

```bash
claude --version
```

### 2. Check MCP Servers

```bash
# Claude Code 시작 후 MCP 서버 상태 확인
claude
# 내부에서: /mcp status
```

### 3. Check Python Environment

```bash
python3 -c "import pykrx; import pandas; import numpy; print('OK')"
```

### 4. Test Stock Analyzer

```bash
cd ~/public_agents
claude
# 내부에서: /stock-analyze 삼성전자 --depth quick
```

### 5. Run Plugin Tests

```bash
cd ~/public_agents/plugins/stock-analyzer-advanced/utils
python -m pytest test_utils.py -v
```

---

## Project Configuration Files

### CLAUDE.md (프로젝트 규칙)

프로젝트 루트의 `CLAUDE.md`에 다음 규칙이 정의되어 있습니다:
- Git commit 시 Claude signature 제거
- 최신 정보 수집 시 날짜 확인 우선
- TDD 개발 규칙 (Red → Green → Refactor)

### Directory Structure

```
public_agents/
├── CLAUDE.md                   # 프로젝트 규칙
├── setup_guide.md              # 이 파일
├── plugins/                    # 플러그인 디렉토리
│   ├── stock-analyzer-advanced/
│   ├── research-papers/
│   ├── claude-workflows/
│   ├── web3-ai/
│   └── vehicle-contamination-or/
├── notes_*.md                  # 리서치 노트
├── task_plan.md                # 작업 계획
└── week6_*.md                  # 강의 자료 등
```

---

## Troubleshooting

### Issue 1: MCP Server 연결 실패

```bash
# uvx 경로 확인
which uvx  # /opt/homebrew/bin/uvx 또는 ~/.local/bin/uvx

# settings.json에서 절대 경로 사용
"command": "/opt/homebrew/bin/uvx"
```

### Issue 2: pykrx Import Error

```bash
pip install --upgrade pykrx pandas numpy
```

### Issue 3: Obsidian MCP 연결 실패

1. Obsidian이 실행 중인지 확인
2. Local REST API 플러그인 활성화 확인
3. API Key가 올바른지 확인
4. Port 27123이 열려있는지 확인

```bash
curl http://127.0.0.1:27123/
```

### Issue 4: Node.js 관련 오류

```bash
# npm cache 정리
npm cache clean --force

# Node.js 재설치
brew uninstall node
brew install node
```

### Issue 5: Playwright 브라우저 미설치

```bash
npx playwright install chromium
```

---

## Quick Setup Script

전체 설정을 자동화하는 스크립트:

```bash
#!/bin/bash
# setup.sh

echo "=== Public Agents Setup Script ==="

# 1. Check prerequisites
echo "Checking prerequisites..."
command -v brew >/dev/null 2>&1 || { echo "Installing Homebrew..."; /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; }
command -v node >/dev/null 2>&1 || { echo "Installing Node.js..."; brew install node; }
command -v jq >/dev/null 2>&1 || { echo "Installing jq..."; brew install jq; }
command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }

# 2. Install Python dependencies
echo "Installing Python dependencies..."
pip install pykrx pandas numpy requests beautifulsoup4 lxml pytest

# 3. Create hooks directory
echo "Setting up hooks..."
mkdir -p ~/.claude/hooks

# 4. Done
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Configure ~/.claude/settings.json with MCP servers"
echo "2. Run 'claude' in the project directory"
echo "3. Enable plugins via /install-plugin"
```

---

## Version History

| Date | Changes |
|------|---------|
| 2026-01-14 | Initial setup guide created |

---

*Generated for public_agents project*
