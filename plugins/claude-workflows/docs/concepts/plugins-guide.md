# Plugins (플러그인)

## 정의

Commands, agents, skills, hooks를 묶은 Claude Code 확장 패키지입니다.

## 배포 방식 비교

| 방식 | 파일 | 용도 |
|------|------|------|
| **단일 플러그인** | `plugin.json` | 플러그인 1개만 배포 |
| **마켓플레이스** | `marketplace.json` | 여러 플러그인 묶어서 배포 |

---

## 방식 1: 단일 플러그인 (plugin.json)

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json      # 단일 플러그인 메타데이터
├── commands/
├── agents/
└── skills/
```

```json
// .claude-plugin/plugin.json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "플러그인 설명",
  "commands": ["./commands/my-command.md"],
  "agents": ["./agents/my-agent.md"]
}
```

---

## 방식 2: 마켓플레이스 (marketplace.json) ← 현재 repo

여러 플러그인을 한 repo에서 배포할 때 사용합니다.

### 구조 (현재 repo)

```
public_agents/
├── .claude-plugin/
│   └── marketplace.json     # 플러그인 목록
└── plugins/
    ├── research-papers/     # 플러그인 1
    │   ├── agents/
    │   ├── commands/
    │   ├── docs/
    │   └── local/
    └── claude-workflows/    # 플러그인 2
        ├── agents/
        ├── commands/
        ├── docs/
        └── local/
```

### marketplace.json 예시 (현재 repo)

```json
{
  "name": "megabytekim-agents",
  "owner": {
    "name": "megabytekim",
    "url": "https://github.com/megabytekim"
  },
  "plugins": [
    {
      "name": "research-papers",
      "source": "./plugins/research-papers",
      "description": "학술 논문 분석 워크플로우",
      "commands": ["./commands/analyze.md"],
      "agents": ["./agents/cv-paper-analyst.md"]
    },
    {
      "name": "claude-workflows",
      "source": "./plugins/claude-workflows",
      "description": "Claude Code 생산성 도구",
      "commands": ["./commands/explain.md"],
      "agents": ["./agents/claude-code-guide.md"]
    }
  ]
}
```

---

## 플러그인 내부 구조

```
plugins/{plugin-name}/
├── agents/      # AI 에이전트
├── commands/    # 슬래시 명령어
├── skills/      # 재사용 가능한 지식
├── docs/        # 레퍼런스 문서 (Git 커밋)
└── local/       # 개인 노트 (Gitignored)
```

---

## 관리 명령어

| 명령어 | 설명 |
|--------|------|
| `/plugin` | 플러그인 관리 UI |
| `/install-plugin [url]` | GitHub URL에서 설치 |
| `claude plugin validate .` | 플러그인 구조 검증 |

## 설치 방법

```bash
# Marketplace에서 설치
/install-plugin https://github.com/megabytekim/public_agents

# 로컬에서 테스트
claude --plugin-dir ./plugins/claude-workflows
```

---

## 구성 요소 비교

| 구성 요소 | 호출 방식 | 용도 |
|----------|----------|------|
| Commands | `/plugin:command` | 반복 작업 자동화 |
| Agents | Claude 자동 위임 | 복잡한 멀티스텝 작업 |
| Skills | Claude 자동 선택 | 전문 지식 제공 |
| Hooks | 이벤트 트리거 | 자동화 스크립트 |

---

## 참고

- 관련 명령어: `/plugin`, `/mcp`, `/hooks`
