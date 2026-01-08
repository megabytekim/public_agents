# Project Rules

모든 workflow는 종료 전 반드시 정확성을 검증하세요 (Validation Thinking).

## Git 규칙

- 커밋 메시지와 PR에 Claude signature를 추가하지 마세요 (예: "🤖 Generated with Claude Code", "Co-Authored-By: Claude" 등)

## 최신 정보 수집 규칙

최신 정보를 수집해야 할 때는 다음 순서를 따르세요:
1. **날짜 확인 우선**: WebSearch로 "today's date" 또는 "current date time"을 먼저 검색하여 정확한 날짜 확인
2. **검색 쿼리에 날짜 포함**: 확인된 날짜를 검색 쿼리에 포함 (예: "Claude Code best practices 2025", "latest trends January 2025")
3. **최신성 검증**: 검색 결과의 게시 날짜를 확인하여 오래된 정보 필터링

## TDD 개발 규칙 (Augmented Coding)

> Kent Beck의 "Augmented Coding" 원칙 기반

### TDD 사이클 준수

```
Red → Green → Refactor
```

1. **Red**: 실패하는 테스트 먼저 작성
2. **Green**: 테스트 통과하는 최소 코드 작성
3. **Refactor**: 구조 개선 (테스트 통과 유지)

### AI 길잃음 신호 감지

다음 신호 감지 시 즉시 개입:

- ❌ 루프 구조가 과도하게 복잡해지는 경우
- ❌ 요청하지 않은 기능을 추가하는 경우
- ❌ 테스트를 삭제하거나 비활성화하는 경우 (부정행위)

### 개발 흐름

```
PRD → plan.md → TDD
```

1. **PRD 작성**: 요구사항 명세
2. **plan.md 작성**: 단계별 구현 계획
3. **TDD 실행**: 테스트 → 구현 → 리팩토링

### 금지 사항

- 테스트 삭제/비활성화 금지
- 요청하지 않은 기능 추가 금지
- 구조적 변경과 기능 변경 동시 진행 금지
