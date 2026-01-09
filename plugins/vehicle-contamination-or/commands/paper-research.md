---
description: 논문 검색부터 처리까지 전체 워크플로우. 사용법 - /paper-research [query] --limit [N]
allowed-tools: mcp__arxiv-mcp-server, Task, Read, Write, WebFetch
argument-hint: [query] --limit [N]
---

# Paper Research - 전체 워크플로우

논문 검색 → 다운로드 → Citation 조회 → 처리 → Registry 업데이트까지 한 번에 수행합니다.

## 사용법

```bash
/paper-research ordinal regression --limit 5
/paper-research ti:"survey" ordinal regression --limit 3
/paper-research "deep learning" age estimation --limit 10
```

## 전체 워크플로우

```
┌─────────────────────────────────────────────────────────┐
│  /paper-research (메인 컨텍스트, MCP 접근 가능)           │
│                                                         │
│  1. arXiv 검색 (MCP)                                    │
│  2. Registry 중복 체크                                   │
│  3. 논문 다운로드 (MCP)                                  │
│  4. Citation 조회 (Semantic Scholar)                    │
│  5. Slug 생성                                           │
│  6. paper-researcher 에이전트 호출 (Task)               │
│       └→ survey-processor 또는 paper-processor          │
│       └→ registry 업데이트                              │
└─────────────────────────────────────────────────────────┘
```

---

## 작업 순서

### Step 1: 인자 파싱

```python
query = " ".join(args)  # "ordinal regression"
limit = args.get("--limit", 5)
categories = args.get("--categories", ["cs.CV", "cs.LG", "cs.AI"])
```

### Step 2: Registry 로드 (중복 체크용)

```python
registry = Read("plugins/vehicle-contamination-or/private/registry.json")
existing_ids = set()
for paper in registry["papers"]:
    existing_ids.add(paper["id"])
    existing_ids.add(paper["url"])
    existing_ids.add(paper["title"].lower().strip())
```

### Step 3: arXiv 검색

```python
results = mcp__arxiv-mcp-server__search_papers(
    query=query,
    categories=categories,
    max_results=limit * 2,  # 중복 제거 대비
    sort_by="relevance"
)
```

### Step 4: 중복 필터링

```python
new_papers = []
for paper in results["papers"]:
    paper_id = f"arxiv:{paper['id'].split('v')[0]}"
    if paper_id not in existing_ids:
        new_papers.append(paper)
        existing_ids.add(paper_id)

    if len(new_papers) >= limit:
        break

print(f"검색 결과: {len(results['papers'])}개")
print(f"신규 논문: {len(new_papers)}개")
```

### Step 5: 각 논문 준비 (다운로드 + Citation + Slug)

```python
papers_to_process = []

for paper in new_papers:
    paper_id = paper["id"].split("v")[0]  # 버전 제거

    # 5.1 다운로드
    mcp__arxiv-mcp-server__download_paper(paper_id=paper_id)

    # 5.2 Citation 조회
    citation_response = WebFetch(
        url=f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{paper_id}?fields=citationCount",
        prompt="Extract citationCount from JSON"
    )
    citations = citation_response.citationCount or "XX"

    # 5.3 Slug 생성
    title_part = paper["title"].lower()
    title_part = re.sub(r'[^a-z0-9\s]', '', title_part)
    title_part = '-'.join(title_part.split()[:4])
    year = paper["published"][:4]
    slug = f"{title_part}-{year}-c{citations}"[:60]

    # 5.4 Survey 여부 판별
    is_survey = any(word in paper["title"].lower() for word in ["survey", "review", "overview"])

    # 5.5 배치 목록에 추가
    papers_to_process.append({
        "id": f"arxiv:{paper_id}",
        "title": paper["title"],
        "year": int(year),
        "url": f"https://arxiv.org/abs/{paper_id}",
        "citations": citations if citations != "XX" else None,
        "slug": slug,
        "is_survey": is_survey,
        "file_path": f"~/.arxiv-mcp-server/papers/{paper_id}.md"
    })
```

### Step 6: paper-researcher 에이전트 호출 (배치)

```python
# 배치 형태로 paper-researcher 호출 (오케스트레이터)
Task(
    subagent_type="vehicle-contamination-or:paper-researcher",
    prompt=f"""
배치 논문 처리 요청:

{{
  "papers": {json.dumps(papers_to_process, indent=2, ensure_ascii=False)},
  "options": {{
    "retry_failed": true,
    "max_retries": 2,
    "continue_on_error": true
  }}
}}

위 논문들을 처리해주세요:
1. 각 논문에 대해 중복 체크
2. survey-processor 또는 paper-processor 호출 (재시도 포함)
3. 성공한 논문만 registry.json에 일괄 추가
4. 상세 리포트 출력 (성공/실패/스킵 목록)
"""
)
```

### Step 7: 최종 보고

```markdown
## ✅ Paper Research 완료

### 검색 정보
- 쿼리: {query}
- 카테고리: {categories}

### 처리 결과
| # | ID | 제목 | 연도 | 유형 | 상태 |
|---|-----|------|------|------|------|
| 1 | arxiv:2503.00952 | A Survey on... | 2025 | Survey | ✅ |
| 2 | arxiv:1901.07884 | CORAL... | 2019 | 일반 | ✅ |
...

### 통계
- 검색 결과: {total}개
- 중복 제거: {duplicates}개
- 처리 완료: {success}개
- 실패: {failed}개

### 저장 위치
- Registry: plugins/vehicle-contamination-or/private/registry.json
- 논문: plugins/vehicle-contamination-or/private/paper/{slug}/
```

---

## 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--limit` | 5 | 처리할 논문 개수 |
| `--categories` | cs.CV,cs.LG,cs.AI | arXiv 카테고리 필터 |
| `--survey-only` | false | Survey 논문만 검색 |

## 예시

```bash
# 기본 검색
/paper-research ordinal regression --limit 5

# Survey만 검색
/paper-research ti:"survey" ordinal regression --limit 3

# 특정 도메인
/paper-research "ordinal regression" "age estimation" --limit 5

# 카테고리 지정
/paper-research ordinal regression --categories cs.CV --limit 10
```

---

## 🎯 Project Context

차량 오염도(Lv1~Lv4) 분류를 위한 **Ordinal Regression** 기법 탐색용.
파이프라인: Car Part Detection → 부위별 OR → Threshold 판정 → 세차 권장
