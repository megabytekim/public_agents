# Public Agents

Custom Claude Code plugin collection for research and productivity workflows.

## Installation

```bash
/install-plugin https://github.com/megabytekim/public_agents
```

## Plugins

| Plugin | Description | Category |
|--------|-------------|----------|
| **research-papers** | 학술 논문 분석 워크플로우 | Research |
| **claude-workflows** | Claude Code 생산성 도구 | Productivity |

---

### research-papers

학술 논문을 체계적으로 분석하고 실무 적용성을 평가합니다.

| 구성 | 이름 | 설명 |
|------|------|------|
| Agent | `cv-paper-analyst` | Computer Vision 논문 분석 |
| Command | `/analyze` | PDF, arXiv, 제목으로 논문 분석 |

```
"Analyze https://arxiv.org/abs/2103.03230"
"Vision Transformer 논문 분석해줘"
```

---

### claude-workflows

Claude Code를 더 효과적으로 사용하기 위한 가이드와 도구입니다.

| 구성 | 이름 | 설명 |
|------|------|------|
| Agent | `claude-code-guide-agent` | Claude Code 사용법 안내 |
| Command | `/explain [concept]` | 개념 설명 (agents, hooks, mcp 등) |

```
"Claude Code 명령어 뭐 있어?"
"/claude-workflows:explain hooks --save"
```

---

## Plugin Structure

각 플러그인은 다음 구조를 따릅니다:

```
plugins/{plugin-name}/
├── agents/      # AI 에이전트
├── commands/    # 슬래시 명령어
├── skills/      # 재사용 가능한 지식
├── docs/        # 레퍼런스 문서 (Git 커밋)
└── local/       # 개인 노트 (Gitignored)
```

## Contributing

새로운 플러그인이나 에이전트 제안 환영합니다.

## License

MIT
