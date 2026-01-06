# Claude Code Hooks (훅) 가이드

## 훅이란?

**훅(Hooks)**은 Claude Code에서 특정 이벤트가 발생할 때 자동으로 실행되는 스크립트입니다. 코드 포맷팅, 린팅, 알림 등을 자동화할 수 있습니다.

## 주요 이벤트

| 이벤트 | 시점 | 용도 예시 |
|--------|------|-----------|
| `PreToolUse` | 도구 사용 전 | 권한 검사, 로깅 |
| `PostToolUse` | 도구 사용 후 | 자동 포맷팅, 린팅 |
| `UserPromptSubmit` | 프롬프트 제출 시 | 입력 검증, 컨텍스트 추가 |
| `SessionStart` | 세션 시작 | 환경 설정 |
| `SessionEnd` | 세션 종료 | 정리 작업, 로깅 |

## 설정 파일 위치

- **전역 설정**: `~/.claude/settings.json`
- **프로젝트 설정**: `.claude/settings.json`
- **플러그인 내**: `plugin.json`

## 설정 예시

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write $CLAUDE_FILE_PATH"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/validate-command.sh"
          }
        ]
      }
    ]
  }
}
```

## 환경 변수

훅 스크립트에서 사용할 수 있는 환경 변수:

| 변수 | 설명 |
|------|------|
| `$CLAUDE_FILE_PATH` | 대상 파일 경로 |
| `$CLAUDE_TOOL_NAME` | 실행된 도구 이름 |
| `$CLAUDE_SESSION_ID` | 현재 세션 ID |

## 실용적인 활용 사례

### 1. 파일 저장 후 자동 포맷팅

```json
{
  "PostToolUse": [{
    "matcher": "Write|Edit",
    "hooks": [{ "type": "command", "command": "npm run format" }]
  }]
}
```

### 2. Git 커밋 전 린트 검사

```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{ "type": "command", "command": "./scripts/pre-commit.sh" }]
  }]
}
```

### 3. 세션 시작 시 환경 확인

```json
{
  "SessionStart": [{
    "hooks": [{ "type": "command", "command": "./scripts/check-env.sh" }]
  }]
}
```

## 훅 차단 (Blocking)

훅이 **0이 아닌 종료 코드**를 반환하면 해당 작업이 차단됩니다. 이를 통해 위험한 명령 실행을 방지할 수 있습니다.

```bash
#!/bin/bash
# validate-command.sh
if [[ "$CLAUDE_COMMAND" == *"rm -rf"* ]]; then
  echo "위험한 명령어 차단됨"
  exit 1
fi
exit 0
```

## 관련 명령어

- `/hooks` - 현재 설정된 훅 확인
- 훅 설정은 JSON 파일을 직접 편집

## 더 알아보기

- [공식 문서](https://docs.anthropic.com/en/docs/claude-code)
- 플러그인에서 훅 사용: `plugin.json`의 `hooks` 필드 참조
