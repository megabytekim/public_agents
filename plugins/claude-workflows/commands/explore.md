---
description: 최신 Claude Code/프롬프팅 트렌드 수집. 사용법 - /explore [topic] (예- claude-code, prompting, mcp, agents)
allowed-tools: WebSearch, WebFetch, Read, Write, Glob
argument-hint: [topic]
---

# Explore - 최신 트렌드 수집

최신 Claude Code 및 프롬프팅 트렌드를 수집하여 `local/trends/`에 저장합니다.

## 작업 순서

### 1. 날짜 확인 (필수)
먼저 WebSearch로 현재 날짜를 확인하세요:
```
검색: "today's date" 또는 "current date"
```

### 2. 토픽 파악
사용자가 지정한 토픽 또는 기본값:
- `claude-code`: Claude Code 업데이트, 새 기능
- `prompting`: 프롬프팅 기법, best practices
- `mcp`: MCP 서버, 통합 도구
- `agents`: AI 에이전트 설계, 워크플로우
- (미지정 시 전체 검색)

### 3. 검색 실행
확인된 날짜를 포함하여 검색:

**Claude Code 관련**
```
"Claude Code release notes {year}"
"Claude Code new features {year}"
site:github.com/anthropics/claude-code releases
site:docs.anthropic.com claude code updates
```

**프롬프팅 관련**
```
"prompt engineering techniques {year}"
"Claude prompting best practices {year}"
"system prompt optimization {year}"
```

**MCP 관련**
```
"MCP server popular {year}"
"Model Context Protocol tools {year}"
```

**에이전트 관련**
```
"AI agent design patterns {year}"
"Claude agent workflow {year}"
```

### 4. 상세 조회
유용한 링크는 WebFetch로 상세 내용 확인

### 5. 결과 저장
파일 경로: `plugins/claude-workflows/local/trends/{YYYY-MM-DD}-{topic}.md`

```markdown
# {Topic} 트렌드 - {YYYY-MM-DD}

## 요약
- 핵심 포인트 1
- 핵심 포인트 2

## 상세 내용

### [제목 1]
**출처**: URL
**날짜**: 게시 날짜
**내용**:
요약 내용...

### [제목 2]
...

## 참고 링크
- [제목](URL)
```

## 저장 위치 안내

- `local/trends/` - 수집 결과 저장 (gitignored)
- 나중에 유용한 내용은 `docs/`로 이동 가능

## 예시

```bash
/explore claude-code    # Claude Code 최신 업데이트
/explore prompting      # 프롬프팅 기법 트렌드
/explore mcp           # MCP 생태계 동향
/explore               # 전체 트렌드 수집
```
