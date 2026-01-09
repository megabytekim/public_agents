---
description: 논문 처리 (paper-processor/survey-processor 호출). 사용법 - /paper-process [paper_id] --slug [slug]
allowed-tools: mcp__arxiv-mcp-server, Task, Read, Write, WebFetch
argument-hint: [paper_id] --slug [slug]
---

# Paper Process - 논문 처리

다운로드된 논문을 paper-processor 또는 survey-processor 에이전트로 직접 처리합니다.

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

### 4. paper-processor 또는 survey-processor 직접 호출

```python
# Survey 여부에 따라 적절한 에이전트 선택
processor_type = "survey-processor" if is_survey else "paper-processor"
output_file = "survey_summary.md" if is_survey else "summary.md"

paper_info = {
    "id": f"arxiv:{paper_id}",
    "title": title,
    "year": int(year),
    "url": f"https://arxiv.org/abs/{paper_id}",
    "citations": citations,
    "slug": slug,
    "is_survey": is_survey,
    "file_path": f"~/.arxiv-mcp-server/papers/{paper_id}.md"
}

Task(
    subagent_type=f"vehicle-contamination-or:{processor_type}",
    prompt=f"""
논문 정보:
{json.dumps(paper_info, indent=2, ensure_ascii=False)}

논문 파일: {paper_info["file_path"]}

저장 위치:
/Users/newyork/public_agents/plugins/vehicle-contamination-or/private/paper/{slug}/{output_file}

위 위치에 {output_file}를 생성하세요.
완료 후 결과 JSON 반환: {{"success": true, "slug": "{slug}"}}
"""
)
```

### 5. Registry 업데이트 (메인에서 직접)

```python
# Task 결과 확인 후 성공 시 registry에 추가
registry = Read("plugins/vehicle-contamination-or/private/registry.json")
today = datetime.now().strftime("%Y-%m-%d")

new_entry = {
    "id": paper_info["id"],
    "slug": slug,
    "title": title,
    "year": int(year),
    "url": paper_info["url"],
    "citations": citations if citations != "XX" else None,
    "status": "processed",
    "added": today,
    "tags": [],
    "has_pdf": True,
    "has_code": False,
    "is_survey": is_survey
}
registry["papers"].append(new_entry)
registry["last_updated"] = today

Write(
    "plugins/vehicle-contamination-or/private/registry.json",
    json.dumps(registry, indent=2, ensure_ascii=False)
)
```

### 6. 결과 출력

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

# 3. 처리 (paper-processor/survey-processor 직접 호출)
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
