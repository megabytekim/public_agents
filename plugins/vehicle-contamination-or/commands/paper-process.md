---
description: 논문 처리 (paper-researcher 호출). 사용법 - /paper-process [paper_id] --slug [slug]
allowed-tools: mcp__arxiv-mcp-server, Task, Read, Write, WebFetch
argument-hint: [paper_id] --slug [slug]
---

# Paper Process - 논문 처리

다운로드된 논문을 paper-researcher 에이전트로 처리합니다.

## 사용법

```bash
/paper-process 2503.00952 --slug survey-ordinal-regression-2025-c0
/paper-process 1901.07884 --slug coral-rank-consistent-ordinal-2019-c259
/paper-process 2503.00952 --slug survey-ordinal-regression-2025-c0 --survey
```

## 작업 순서

### 1. 인자 파싱

```python
paper_id = args[0]  # 2503.00952
slug = args["--slug"]  # survey-ordinal-regression-2025-c0
is_survey = "--survey" in args or "survey" in slug.lower()
```

### 2. 논문 정보 조회 (필요시)

논문 제목/연도가 없으면 arXiv MCP로 조회:

```python
paper_info = mcp__arxiv-mcp-server__search_papers(
    query=f"id:{paper_id}",
    max_results=1
)

title = paper_info["papers"][0]["title"]
year = paper_info["papers"][0]["published"][:4]
```

### 3. Citation 조회 (없으면)

slug에 `cXX`가 있으면 citation 조회:

```python
if "cXX" in slug:
    response = WebFetch(
        url=f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{paper_id}?fields=citationCount",
        prompt="Extract citationCount"
    )
    citations = response.citationCount or "XX"

    # slug 업데이트
    slug = slug.replace("cXX", f"c{citations}")
```

### 4. paper-researcher 에이전트 호출

```python
Task(
    subagent_type="vehicle-contamination-or:paper-researcher",
    prompt=f"""
논문 처리 요청:

{{
  "paper": {{
    "id": "arxiv:{paper_id}",
    "title": "{title}",
    "year": {year},
    "url": "https://arxiv.org/abs/{paper_id}",
    "citations": {citations},
    "slug": "{slug}",
    "is_survey": {str(is_survey).lower()},
    "file_path": "~/.arxiv-mcp-server/papers/{paper_id}.md"
  }}
}}

위 논문을 처리해주세요:
1. 중복 체크
2. {"survey-processor" if is_survey else "paper-processor"} 호출
3. registry.json 업데이트
"""
)
```

### 5. 결과 출력

```markdown
## 처리 완료

| 항목 | 값 |
|------|-----|
| ID | arxiv:{paper_id} |
| Slug | {slug} |
| 유형 | {"Survey" if is_survey else "일반"} |
| 저장 위치 | private/paper/{slug}/ |
| Registry | 업데이트 완료 |
```

---

## 전체 워크플로우

```bash
# 1. 검색
/arxiv-search ordinal regression survey

# 2. 다운로드 (citation + slug 생성)
/arxiv-download 2503.00952
# → 출력: slug = survey-ordinal-regression-2025-c0

# 3. 처리 (paper-researcher → processor → registry)
/paper-process 2503.00952 --slug survey-ordinal-regression-2025-c0
```

---

## Survey 자동 감지

다음 조건 중 하나라도 만족하면 `is_survey: true`:
- `--survey` 플래그 사용
- slug에 "survey" 포함
- 제목에 "survey", "review", "overview" 포함

---

## 옵션

| 옵션 | 설명 |
|------|------|
| `--slug` | 저장 폴더명 (필수) |
| `--survey` | Survey 논문으로 강제 처리 |
| `--title` | 논문 제목 (조회 생략) |
| `--year` | 출판 연도 (조회 생략) |
| `--citations` | 인용수 (조회 생략) |
