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
| Plugin | Status | Source |
|--------|--------|--------|
| planning-with-files | Enabled | OthmanAdi/planning-with-files (Marketplace) |
| stock-analyzer-advanced | Enabled | Local |
| research-papers | Enabled | Local |
| claude-workflows | Enabled | Local |
| web3-ai | Enabled | Local |
| vehicle-contamination-or | Enabled | Local |

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

### Step 3: Install Essential Plugins (Claude Code 내에서 실행)

Claude Code를 시작한 후, 다음 플러그인들을 설치합니다:

```bash
claude
```

**planning-with-files** (Manus-style 파일 기반 계획 관리):
```
/plugin marketplace add OthmanAdi/planning-with-files
/plugin install planning-with-files@planning-with-files
```

> **Note**: 이 플러그인은 복잡한 작업 시 `task_plan.md`, `findings.md`, `progress.md` 파일을 생성하여 컨텍스트 관리를 도와줍니다. Meta가 $2B에 인수한 Manus AI의 컨텍스트 엔지니어링 패턴을 구현합니다.

설치 확인:
```
/plugins
```

### Step 4: Install Python Dependencies

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

---

## MCP Server Configuration

MCP 서버는 `claude mcp add` 명령어로 등록합니다. JSON 파일을 직접 편집하는 방식은 지원하지 않습니다.

### MCP 서버 등록 (터미널에서 실행)

```bash
# playwright (브라우저 자동화)
claude mcp add -s user playwright -- npx @playwright/mcp@latest --headless

# context7 (라이브러리 문서)
claude mcp add -s user context7 -- npx -y @upstash/context7-mcp@latest

# memory (지식 그래프)
claude mcp add -s user memory -- npx -y @modelcontextprotocol/server-memory

# arxiv (논문 검색) - storage-path는 실제 경로로 변경
claude mcp add -s user arxiv -- uv tool run arxiv-mcp-server --storage-path /Users/YOUR_USERNAME/public_agents/plugins/vehicle-contamination-or/private/paper

# yfinance (주식 데이터)
claude mcp add -s user yfinance -- uvx yfmcp@latest
```

> **Note**: `YOUR_USERNAME`을 실제 사용자명으로 변경하세요.

### 등록 확인

```bash
claude mcp list
```

### Scope 옵션

| Scope | 설명 | 설정 파일 위치 |
|-------|------|---------------|
| `-s local` | 현재 프로젝트만 | `.claude/settings.local.json` |
| `-s user` | 모든 프로젝트 (권장) | `~/.claude.json` |
| `-s project` | 프로젝트 공유용 | `.claude/settings.json` |

### MCP 서버 관리 명령어

```bash
# 서버 목록 및 상태 확인
claude mcp list

# 서버 제거
claude mcp remove <server-name>

# 도움말
claude mcp --help
```

### Obsidian MCP 서버 (Optional)

Obsidian 연동이 필요한 경우:

1. Obsidian 실행
2. Settings > Community plugins > Browse
3. "Local REST API" 검색 및 설치
4. 플러그인 활성화 후 Settings에서 API Key 복사
5. 환경변수와 함께 MCP 서버 등록:

```bash
claude mcp add -s user -e OBSIDIAN_API_KEY=YOUR_API_KEY -e OBSIDIAN_HOST=127.0.0.1 -e OBSIDIAN_PORT=27123 -e NO_PROXY=127.0.0.1,localhost mcp-obsidian -- uvx mcp-obsidian
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
# 터미널에서 MCP 서버 상태 확인
claude mcp list

# 또는 Claude Code 내부에서
/mcp
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
# MCP 서버 상태 확인
claude mcp list

# 서버 재등록
claude mcp remove <server-name>
claude mcp add -s user <server-name> -- <command> <args>

# uvx/npx 경로 확인
which uvx  # /opt/homebrew/bin/uvx 또는 ~/.local/bin/uvx
which npx  # /opt/homebrew/bin/npx
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

### Issue 6: 플러그인 enabled인데 커맨드가 안 보임 (.orphaned_at 문제)

**증상**: `/plugins`에서 플러그인이 Enabled로 표시되지만, 슬래시 커맨드 자동완성에 나타나지 않음

**원인**: 플러그인 캐시 디렉토리에 `.orphaned_at` 파일이 생성되어 플러그인이 "고아" 상태로 표시됨

**진단**:
```bash
# .orphaned_at 파일 존재 여부 확인
find ~/.claude/plugins/cache -name ".orphaned_at"
```

**해결 방법**:
```bash
# 특정 플러그인의 .orphaned_at 파일 삭제
rm ~/.claude/plugins/cache/<plugin-name>/<plugin-name>/<version>/.orphaned_at

# 예: planning-with-files
rm ~/.claude/plugins/cache/planning-with-files/planning-with-files/2.1.2/.orphaned_at

# 또는 모든 .orphaned_at 파일 일괄 삭제
find ~/.claude/plugins/cache -name ".orphaned_at" -delete
```

삭제 후 Claude Code를 재시작하세요.

### Issue 7: .orphaned_at 파일이 계속 재생성됨

**증상**: Issue 6의 방법으로 `.orphaned_at` 파일을 삭제해도 Claude Code 실행 시 다시 생성됨

**원인**: Claude Code 내부 플러그인 관리 로직이 플러그인을 orphaned로 판단하여 지속적으로 마킹함

**진단**:
```bash
# .orphaned_at 파일의 타임스탬프 확인 (삭제 후 재생성되는지)
cat ~/.claude/plugins/cache/planning-with-files/planning-with-files/2.1.2/.orphaned_at
# 출력: Unix timestamp (밀리초) - 예: 1768396911156
```

**해결 방법 (플러그인 완전 재설치)**:
```bash
# 1. Claude Code 종료

# 2. 플러그인 캐시 및 마켓플레이스 디렉토리 완전 삭제
rm -rf ~/.claude/plugins/cache/planning-with-files
rm -rf ~/.claude/plugins/marketplaces/planning-with-files

# 3. Claude Code 재시작 후 플러그인 재설치
/plugin marketplace add OthmanAdi/planning-with-files
/plugin install planning-with-files@planning-with-files

# 4. 설치 확인
/plugins
```

**대안 (자동완성 없이 사용)**:

재설치 후에도 문제가 지속되면, 슬래시 커맨드를 직접 타이핑하여 사용 가능:
```
/planning-with-files
```
(자동완성 목록에 없어도 직접 입력하면 동작함)

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

# 4. Register MCP servers
echo "Registering MCP servers..."
claude mcp add -s user playwright -- npx @playwright/mcp@latest --headless
claude mcp add -s user context7 -- npx -y @upstash/context7-mcp@latest
claude mcp add -s user memory -- npx -y @modelcontextprotocol/server-memory
claude mcp add -s user yfinance -- uvx yfmcp@latest

# 5. Verify MCP servers
echo "Verifying MCP servers..."
claude mcp list

# 6. Done
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Run 'claude' in the project directory"
echo "2. Enable plugins via /install-plugin"
```

---

## Version History

| Date | Changes |
|------|---------|
| 2026-01-14 | MCP 설정 방식을 `claude mcp add` 명령어 기반으로 변경 (JSON 직접 편집 방식 제거) |
| 2026-01-14 | Added Issue 6-7: .orphaned_at 문제 및 플러그인 재설치 방법 |
| 2026-01-14 | Added planning-with-files plugin installation (Step 3) |
| 2026-01-14 | Initial setup guide created |

---

*Generated for public_agents project*
