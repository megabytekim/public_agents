---
description: arXiv 논문 검색. 사용법 - /arxiv-search [query] (예- ordinal regression survey)
allowed-tools: mcp__arxiv-mcp-server, Read, Write
argument-hint: [query]
---

# arXiv Search - 논문 검색

arXiv MCP를 사용하여 논문을 검색합니다.

## 사용법

```bash
/arxiv-search ordinal regression        # 기본 검색
/arxiv-search ti:"survey" ordinal       # 제목 한정 검색
/arxiv-search --limit 5 deep learning   # 개수 제한
```

## 작업 순서

### 1. 쿼리 파싱

사용자 입력에서 옵션과 검색어 추출:
- `--limit N`: 결과 개수 (기본: 10)
- `--category`: 카테고리 필터 (기본: cs.CV, cs.LG, cs.AI)
- 나머지: 검색 쿼리

### 2. arXiv MCP 호출

```python
mcp__arxiv-mcp-server__search_papers(
    query=user_query,
    categories=["cs.CV", "cs.LG", "cs.AI"],
    max_results=limit,
    sort_by="relevance"
)
```

### 3. 결과 포맷팅

검색 결과를 테이블로 출력:

```markdown
## 검색 결과: "{query}"

| # | ID | 제목 | 연도 | Survey |
|---|-----|------|------|--------|
| 1 | 2503.00952 | A Survey on Ordinal Regression... | 2025 | Yes |
| 2 | 1901.07884 | CORAL: Rank consistent... | 2019 | No |
```

### 4. 다음 단계 안내

```
다운로드하려면: /arxiv-download {paper_id}
전체 처리하려면: /paper-process {paper_id}
```

## 쿼리 가이드

| 유형 | 쿼리 예시 |
|------|----------|
| 기본 | `ordinal regression` |
| 제목 한정 | `ti:"ordinal regression"` |
| Survey | `ti:"survey" AND "ordinal regression"` |
| 저자 | `au:"Hinton"` |
| 연도 제한 | `"ordinal regression"` + date_from/date_to |

## Survey 논문 판별

제목에 다음이 포함되면 `is_survey: true`:
- "survey"
- "review"
- "overview"
- "comprehensive study"
