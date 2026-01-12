# Public Agents

Custom Claude Code plugin collection for research and productivity workflows.

## Quick Start (New PC Setup)

### 1. Clone Repository

```bash
git clone https://github.com/megabytekim/public_agents.git
cd public_agents
```

### 2. Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- Node.js 18+ (npx)
- Python 3.10+ & [uv](https://github.com/astral-sh/uv) (MCP 서버용)

```bash
# uv 설치 (아직 없다면)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. MCP Servers 설정

```bash
# 필수 MCP 서버 일괄 추가
claude mcp add context7 -- npx --yes @upstash/context7-mcp@latest
claude mcp add playwright -- npx --yes @playwright/mcp@latest --isolated --headless
claude mcp add memory -- npx --yes @modelcontextprotocol/server-memory
claude mcp add arxiv-mcp-server -- uvx arxiv-mcp-server

# 선택: Jupyter (노트북 실행)
claude mcp add jupyter -- uvx jupyter-mcp-server@latest
```

### 4. Run Claude Code

```bash
cd public_agents
claude
```

> 상세 설정은 [setup.md](./setup.md) 참조

---

## Plugins

| Plugin | Description | Commands | Agents |
|--------|-------------|----------|--------|
| **claude-workflows** | Claude Code 생산성 도구 | `/explain`, `/explore` | 4 |
| **research-papers** | 학술 논문 분석 | `/analyze` | 1 |
| **stock-analyzer-advanced** | 한국 주식 분석 | `/stock-analyze` | 4 |
| **vehicle-contamination-or** | OR 논문 리서치 | `/arxiv-search`, `/paper-research` | 4 |
| **web3-ai** | Web3/AI 에이전트 개발 | - | 3 |

---

### claude-workflows

Claude Code를 더 효과적으로 사용하기 위한 가이드와 도구입니다.

| Type | Name | Description |
|------|------|-------------|
| Command | `/explore [topic]` | 최신 트렌드 수집 (claude-code, prompting 등) |
| Command | `/explain [concept]` | 개념 설명 (agents, hooks, mcp 등) |
| Agent | `claude-code-guide-agent` | Claude Code 사용법 안내 |
| Agent | `plugin-refactor-agent` | 플러그인 구조 리팩토링 |

```
"Claude Code 명령어 뭐 있어?"
/explain hooks --save
```

---

### research-papers

학술 논문을 체계적으로 분석하고 실무 적용성을 평가합니다.

| Type | Name | Description |
|------|------|-------------|
| Command | `/analyze` | PDF, arXiv, 제목으로 논문 분석 |
| Agent | `cv-paper-analyst` | Computer Vision 논문 분석 |

```
"Analyze https://arxiv.org/abs/2103.03230"
"Vision Transformer 논문 분석해줘"
```

---

### stock-analyzer-advanced

한국 주식 종합 분석 (기술적 분석 + 시장 정보 + 커뮤니티 센티먼트).

| Type | Name | Description |
|------|------|-------------|
| Command | `/stock-analyze [종목코드]` | 종합 주식 분석 |
| Agent | `market-intelligence` | 시장 데이터 수집 |
| Agent | `sentiment-intelligence` | 커뮤니티 감성 분석 |
| Agent | `technical-intelligence` | 기술적 지표 분석 |
| Agent | `financial-ml-analyst` | 인프라/유틸리티 개발 |

```
/stock-analyze 005930
"삼성전자 기술적 분석해줘"
```

---

### vehicle-contamination-or

차량 오염도 Ordinal Regression 연구를 위한 논문 리서치 워크플로우.

| Type | Name | Description |
|------|------|-------------|
| Command | `/arxiv-search [query]` | arXiv 논문 검색 |
| Command | `/arxiv-download [id]` | 논문 다운로드 |
| Command | `/paper-process [id]` | 논문 처리 (summary 생성) |
| Command | `/paper-research [query]` | 검색→처리 전체 워크플로우 |
| Agent | `paper-finder` | 논문 검색 전담 |
| Agent | `paper-processor` | 일반 논문 처리 |
| Agent | `survey-processor` | Survey 논문 처리 |
| Agent | `ml-agent` | 벤치마크/코드 생성 |

```
/arxiv-search ordinal regression survey
/paper-research "deep ordinal regression" --limit 5
```

---

### web3-ai

Web3/Ethereum 블록체인 개발과 AI 에이전트 시스템 구축.

| Type | Name | Description |
|------|------|-------------|
| Agent | `x402-ethereum-agent` | Web3/Ethereum 스마트 컨트랙트 |
| Agent | `ai-agent` | LLM 기반 AI 에이전트 개발 |
| Agent | `humanities-web3-agent` | Web3/AI 인문학적 분석 |

```
"ERC-4337 account abstraction 구현해줘"
"LangChain으로 RAG 에이전트 만들어줘"
```

---

## Project Structure

```
public_agents/
├── CLAUDE.md                    # 프로젝트 규칙 (TDD, Git 규칙)
├── README.md                    # 이 파일
├── setup.md                     # 상세 설정 가이드
├── .gitignore
├── .claude/
│   ├── settings.json            # 공유 권한 설정 (git 커밋)
│   └── settings.local.json      # 개인 권한 설정 (gitignored)
└── plugins/
    ├── claude-workflows/
    │   ├── agents/              # 4개 에이전트
    │   ├── commands/            # /explain, /explore
    │   └── docs/                # 레퍼런스 문서
    ├── research-papers/
    │   ├── agents/              # cv-paper-analyst
    │   └── commands/            # /analyze
    ├── stock-analyzer-advanced/
    │   ├── agents/              # MI, SI, TI, ML analyst
    │   ├── commands/            # /stock-analyze
    │   ├── utils/               # pykrx 기반 유틸리티
    │   └── watchlist/           # 종목 분석 결과
    ├── vehicle-contamination-or/
    │   ├── agents/              # paper-finder, processor 등
    │   ├── commands/            # /arxiv-search, /paper-research
    │   └── private/             # 논문 저장소 (gitignored)
    └── web3-ai/
        └── agents/              # x402, ai-agent 등
```

---

## First Time Setup Checklist

- [ ] Repository clone
- [ ] Claude Code CLI 설치
- [ ] Node.js 18+, Python 3.10+ 설치
- [ ] uv 설치 (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [ ] MCP 서버 추가 (위 명령어 실행)
- [ ] `claude` 실행 후 `/agents` 또는 `/help`로 확인

> 권한 설정(`.claude/settings.json`)은 git에 포함되어 자동 적용됩니다.

---

## Troubleshooting

### MCP 서버 연결 실패

```bash
claude mcp list          # 상태 확인
claude mcp restart <name> # 재시작
```

### uvx/npx 없음

```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js (macOS)
brew install node
```

### 개인 권한 추가

`.claude/settings.local.json`에 개인 설정 추가 (예: Obsidian):

```json
{
  "permissions": {
    "allow": [
      "mcp__mcp-obsidian__obsidian_simple_search"
    ]
  }
}
```

> 공유 권한은 `.claude/settings.json`에 프로젝트 상대 경로(`/plugins/...`)로 설정되어 있어 별도 수정 불필요

---

## License

MIT
