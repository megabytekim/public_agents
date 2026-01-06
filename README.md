# Public Agents

Custom Claude Code plugin collection for research and analysis workflows.

## Installation

Add this repository as a Claude Code plugin source:

```bash
# From Claude Code, install the plugin
/install-plugin https://github.com/newyork/public_agents
```

Or clone and use locally:

```bash
git clone https://github.com/newyork/public_agents.git
cd public_agents
```

## Available Plugins

### 1. research-papers

**Academic Paper Analysis Workflows**

Systematically analyzes Computer Vision, ML, and NLP papers with template-based reviews and practical applicability assessment.

#### Features
- 📄 PDF/arXiv paper automatic analysis
- 🔍 Related research and code exploration (GitHub, implementations)
- 📊 Benchmark performance comparison
- 💡 Key insight extraction
- 🎯 Practical applicability assessment

#### Agents
- `cv-paper-analyst` - Computer Vision paper analysis specialist

#### Commands
- `/analyze` - Analyze a paper from PDF, arXiv link, or title

#### Usage
```
# Analyze from arXiv
"Analyze https://arxiv.org/abs/2103.03230"

# Analyze from PDF
"Analyze the paper in staging/input/paper.pdf"

# Search and analyze
"Analyze the Vision Transformer paper"
```

## Directory Structure

```
public_agents/
├── .claude-plugin/
│   └── marketplace.json          # Plugin registry
├── plugins/
│   ├── research-papers/
│   │   ├── agents/
│   │   │   └── cv-paper-analyst.md
│   │   ├── commands/
│   │   │   └── analyze.md
│   │   ├── staging/
│   │   └── results/
│   └── claude-workflows/
│       ├── agents/
│       │   └── claude-code-guide.md
│       ├── commands/
│       └── skills/
└── README.md
```

### 2. claude-workflows

**Claude Code Workflows & Productivity Tools**

Claude Code 사용을 더 효과적으로 만들어주는 워크플로우 및 생산성 도구 모음입니다.

#### Commands
- `/explain [concept]` - Claude Code 개념 설명 (agents, commands, skills, hooks, mcp 등)

#### Agents
- `claude-code-guide` - Claude Code 사용법, 명령어, 플러그인 개발 가이드

#### Usage
```
"Claude Code 명령어 뭐 있어?"
"플러그인 어떻게 만들어?"
"MCP 서버 설정 방법 알려줘"
```

## Contributing

Feel free to add new plugins following the same structure pattern.

## License

MIT
