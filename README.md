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

### 1. paper-analyst

**Academic Paper Analysis Expert**

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
│   └── paper-analyst/
│       ├── agents/
│       │   └── cv-paper-analyst.md
│       ├── commands/
│       │   └── analyze.md
│       ├── staging/
│       │   ├── input/            # Place PDF files here
│       │   ├── analysis/         # Intermediate results
│       │   └── memory/           # Analysis history
│       └── results/              # Final analysis reports
└── README.md
```

## Contributing

Feel free to add new plugins following the same structure pattern.

## License

MIT
