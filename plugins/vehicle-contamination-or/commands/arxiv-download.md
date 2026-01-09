---
description: arXiv 논문 다운로드. 사용법 - /arxiv-download [paper_id] (예- 2503.00952)
allowed-tools: mcp__arxiv-mcp-server, WebFetch, Read, Write
argument-hint: [paper_id]
---

# arXiv Download - 논문 다운로드

arXiv MCP를 사용하여 논문을 다운로드하고 citation을 조회합니다.

## 사용법

```bash
/arxiv-download 2503.00952              # 단일 논문
/arxiv-download 2503.00952 1901.07884   # 여러 논문
```

## 작업 순서

### 1. 논문 다운로드

```python
mcp__arxiv-mcp-server__download_paper(paper_id="2503.00952")

# 결과:
# {
#   "status": "success",
#   "resource_uri": "file:///Users/.../.arxiv-mcp-server/papers/2503.00952.md"
# }
```

### 2. Citation 조회 (Semantic Scholar)

```python
WebFetch(
    url=f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{paper_id}?fields=citationCount",
    prompt="Extract citationCount from JSON"
)
```

실패 시 `cXX` 사용 (숫자 추측 금지)

### 3. Slug 생성

```python
def generate_slug(title, year, citations):
    # 제목에서 첫 4단어 추출
    title_part = title.lower()
    title_part = re.sub(r'[^a-z0-9\s]', '', title_part)
    title_part = '-'.join(title_part.split()[:4])

    return f"{title_part}-{year}-c{citations}"

# 예시: "coral-rank-consistent-ordinal-2019-c259"
```

### 4. 결과 출력

```markdown
## 다운로드 완료

| 항목 | 값 |
|------|-----|
| ID | arxiv:2503.00952 |
| 제목 | A Survey on Ordinal Regression... |
| 연도 | 2025 |
| Citations | 0 |
| Slug | survey-ordinal-regression-2025-c0 |
| 파일 | ~/.arxiv-mcp-server/papers/2503.00952.md |

처리하려면: /paper-process 2503.00952 --slug survey-ordinal-regression-2025-c0
```

## 다중 다운로드

여러 ID가 주어지면 병렬로 처리:

```bash
/arxiv-download 2503.00952 1901.07884 2111.08851
```

결과:
```markdown
| # | ID | 제목 | Citations | Slug | 상태 |
|---|-----|------|-----------|------|------|
| 1 | 2503.00952 | Survey... | 0 | survey-...-c0 | ✅ |
| 2 | 1901.07884 | CORAL... | 259 | coral-...-c259 | ✅ |
| 3 | 2111.08851 | CORN... | 150 | corn-...-c150 | ✅ |
```
