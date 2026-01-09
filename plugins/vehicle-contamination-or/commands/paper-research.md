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
│  2. Index 중복 체크 (registry-index.txt, 경량)          │
│  3. 논문 다운로드 (MCP)                                  │
│  4. Citation 조회 (Semantic Scholar)                    │
│  5. Slug 생성                                           │
│  6. 병렬 Task 호출 ─────────────────────┐               │
│       ├─ paper-processor (일반 논문)    │ 병렬          │
│       └─ survey-processor (Survey)     │               │
│  7. Registry 업데이트 (2개 파일 동시!)   ◀──────────────┘ │
│       ├─ registry.json (전체 메타데이터)                │
│       └─ registry-index.txt (ID만)                     │
│  8. 최종 보고                                           │
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

### Step 2: Index 로드 (중복 체크용)

> **컨텍스트 최적화**: registry.json 대신 경량 index 파일 사용 (~20바이트/논문)

```python
# 경량 인덱스 파일 읽기 (registry.json 대신)
index_content = Read("plugins/vehicle-contamination-or/private/registry-index.txt")
existing_ids = set()
for line in index_content.strip().split("\n"):
    line = line.strip()
    if line and not line.startswith("#"):  # 주석 제외
        existing_ids.add(line)
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

### Step 6: 병렬 Task 호출 (paper-processor / survey-processor)

> **중요**: 단일 메시지에서 여러 Task를 병렬로 호출합니다.
> Nested Task 제한으로 인해 중간 오케스트레이터 없이 직접 호출합니다.

```python
# 논문 유형별 분류
survey_papers = [p for p in papers_to_process if p["is_survey"]]
regular_papers = [p for p in papers_to_process if not p["is_survey"]]

# 병렬 Task 호출 (단일 메시지에 여러 Task)
tasks = []

for paper in regular_papers:
    tasks.append(Task(
        subagent_type="vehicle-contamination-or:paper-processor",
        description=f"Process {paper['slug'][:20]}",
        prompt=f"""
논문 정보:
{json.dumps(paper, indent=2, ensure_ascii=False)}

논문 파일: {paper["file_path"]}

저장 위치:
/Users/newyork/public_agents/plugins/vehicle-contamination-or/private/paper/{paper["slug"]}/summary.md

위 위치에 summary.md를 생성하세요.
완료 후 결과 JSON 반환: {{"success": true, "slug": "{paper['slug']}"}}
"""
    ))

for paper in survey_papers:
    tasks.append(Task(
        subagent_type="vehicle-contamination-or:survey-processor",
        description=f"Process survey {paper['slug'][:20]}",
        prompt=f"""
논문 정보:
{json.dumps(paper, indent=2, ensure_ascii=False)}

논문 파일: {paper["file_path"]}

저장 위치:
/Users/newyork/public_agents/plugins/vehicle-contamination-or/private/paper/{paper["slug"]}/survey_summary.md

위 위치에 survey_summary.md를 생성하세요.
완료 후 결과 JSON 반환: {{"success": true, "slug": "{paper['slug']}"}}
"""
    ))

# 모든 Task 결과 수집
results = await gather(tasks)
```

### Step 7: Registry 업데이트 (메인에서 직접)

> **중요**: `registry.json`과 `registry-index.txt` 두 파일을 **반드시 동시에** 업데이트해야 합니다.
> 동기화가 어긋나면 중복 체크 실패 또는 데이터 불일치 발생.

```python
# 1. registry.json 로드 (업데이트용 - 이때만 전체 파일 읽음)
registry = Read("plugins/vehicle-contamination-or/private/registry.json")
today = datetime.now().strftime("%Y-%m-%d")

# 2. 성공한 논문 수집
new_ids = []
for paper in papers_to_process:
    if paper_succeeded(paper):
        new_entry = {
            "id": paper["id"],
            "slug": paper["slug"],
            "title": paper["title"],
            "year": paper["year"],
            "url": paper["url"],
            "citations": paper["citations"],
            "status": "processed",
            "added": today,
            "tags": [],
            "has_pdf": True,
            "has_code": False,
            "is_survey": paper["is_survey"]
        }
        registry["papers"].append(new_entry)
        new_ids.append(paper["id"])  # index용 ID 수집

# 3. registry.json 저장
registry["last_updated"] = today
Write(
    "plugins/vehicle-contamination-or/private/registry.json",
    json.dumps(registry, indent=2, ensure_ascii=False)
)

# 4. registry-index.txt에 새 ID 추가 (append)
index_content = Read("plugins/vehicle-contamination-or/private/registry-index.txt")
for new_id in new_ids:
    index_content += f"\n{new_id}"
Write(
    "plugins/vehicle-contamination-or/private/registry-index.txt",
    index_content.strip() + "\n"  # 마지막 줄바꿈 보장
)

# 5. 동기화 검증 (선택적)
assert len(registry["papers"]) == len([l for l in index_content.split("\n") if l.strip() and not l.startswith("#")])
```

#### 동기화 체크리스트

- [ ] registry.json에 새 논문 추가됨
- [ ] registry-index.txt에 새 ID 추가됨
- [ ] 두 파일의 논문 수가 일치함

### Step 8: 최종 보고

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
- Index: plugins/vehicle-contamination-or/private/registry-index.txt
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

## 병렬 처리 참고

- **최대 병렬 수**: 10개 (Claude Code 제한)
- **10개 초과 시**: 자동 큐잉
- **에러 핸들링**: 개별 Task 실패해도 다른 Task 계속 진행

---

## 🎯 Project Context

차량 오염도(Lv1~Lv4) 분류를 위한 **Ordinal Regression** 기법 탐색용.
파이프라인: Car Part Detection → 부위별 OR → Threshold 판정 → 세차 권장
