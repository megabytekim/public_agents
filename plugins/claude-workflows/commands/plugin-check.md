---
description: 플러그인 수정 후 검증. 사용법 - /plugin-check [plugin-name] (예- vehicle-contamination-or)
allowed-tools: Read, Glob, Bash
argument-hint: [plugin-name]
---

# Plugin Check - 플러그인 수정 후 검증

플러그인 수정 후 필요한 체크리스트를 자동으로 검증합니다.

## 캐시 경로 정보

> **공식 확인**: 아래 캐시 경로는 [Claude Code GitHub Issue #16453](https://github.com/anthropics/claude-code/issues/16453)에서 확인된 공식 경로입니다.

| 경로 | 용도 |
|------|------|
| `~/.claude/plugins/cache/` | 플러그인 캐시 (복사된 파일들) |
| `~/.claude/plugins/marketplaces/` | 마켓플레이스 git 저장소 |

```
~/.claude/plugins/cache/{marketplace-name}/{plugin-name}/{version-or-commit}/
```

## 작업 순서

### Step 1: 인자 파싱

```python
plugin_name = args[0] if args else None  # 특정 플러그인 또는 전체
base_path = "/Users/newyork/public_agents"
marketplace_path = f"{base_path}/.claude-plugin/marketplace.json"
```

### Step 2: marketplace.json 로드

```python
marketplace = Read(marketplace_path)
plugins = marketplace["plugins"]

if plugin_name:
    plugins = [p for p in plugins if p["name"] == plugin_name]
```

### Step 3: 각 플러그인 검증

#### 3.1 파일 존재 체크

```python
for plugin in plugins:
    source_dir = plugin["source"]  # "./plugins/xxx"

    # Commands 체크
    for cmd_path in plugin.get("commands", []):
        full_path = f"{base_path}/{source_dir}/{cmd_path.lstrip('./')}"
        if not file_exists(full_path):
            errors.append(f"❌ Missing command: {full_path}")

    # Agents 체크
    for agent_path in plugin.get("agents", []):
        full_path = f"{base_path}/{source_dir}/{agent_path.lstrip('./')}"
        if not file_exists(full_path):
            errors.append(f"❌ Missing agent: {full_path}")
```

#### 3.2 실제 파일 vs marketplace 비교

```python
# 실제 agents 폴더의 파일 목록
actual_agents = Glob(f"{source_dir}/agents/*.md")
registered_agents = [a.lstrip('./') for a in plugin.get("agents", [])]

for actual in actual_agents:
    if actual not in registered_agents:
        warnings.append(f"⚠️ Unregistered agent: {actual}")

# 실제 commands 폴더의 파일 목록
actual_commands = Glob(f"{source_dir}/commands/*.md")
registered_commands = [c.lstrip('./') for c in plugin.get("commands", [])]

for actual in actual_commands:
    if actual not in registered_commands:
        warnings.append(f"⚠️ Unregistered command: {actual}")
```

#### 3.3 캐시 vs 실제 파일 비교 (Orphaned Cache 탐지)

> **중요**: Claude Code는 플러그인을 캐시에 저장합니다. 실제 파일이 삭제되어도 캐시에 남아있으면 에이전트 목록에 계속 나타납니다.

```python
# 캐시 경로
cache_base = "~/.claude/plugins/cache/megabytekim-agents"
plugin_cache_path = f"{cache_base}/{plugin_name}"

# 캐시된 버전들 확인
cached_versions = Bash(f"ls {plugin_cache_path}/ 2>/dev/null")

for version in cached_versions:
    cached_agents = Glob(f"{plugin_cache_path}/{version}/agents/*.md")

    for cached in cached_agents:
        filename = os.path.basename(cached)
        actual_path = f"{source_dir}/agents/{filename}"

        if not file_exists(actual_path):
            warnings.append(f"👻 Orphaned cache: {filename} (캐시에만 존재)")
```

**Orphaned Cache 해결:**
```bash
# 특정 파일만 삭제
rm ~/.claude/plugins/cache/megabytekim-agents/{plugin_name}/{version}/agents/{file}.md

# 플러그인 캐시 전체 삭제 (재설치됨)
rm -rf ~/.claude/plugins/cache/megabytekim-agents/{plugin_name}/
```

#### 3.4 캐시 누락 탐지 (Missing from Cache)

> **중요**: 소스에 새 파일을 추가해도 캐시는 자동 업데이트되지 않습니다. `plugin update` 명령은 버전 번호만 비교하므로 파일 변경을 감지하지 못합니다.

```python
# 소스 파일 목록
source_agents = Glob(f"{source_dir}/agents/*.md")

for source_file in source_agents:
    filename = os.path.basename(source_file)
    cached_path = f"{plugin_cache_path}/{version}/agents/{filename}"

    if not file_exists(cached_path):
        errors.append(f"🔄 Missing from cache: {filename} (소스에만 존재, 재설치 필요)")
```

**Missing from Cache 해결:**
```bash
# 플러그인 재설치 (권장)
claude plugin uninstall {plugin_name}@megabytekim-agents
claude plugin install {plugin_name}@megabytekim-agents

# 또는 수동 복사
cp {source_dir}/agents/{file}.md ~/.claude/plugins/cache/megabytekim-agents/{plugin_name}/{version}/agents/
```

> ⚠️ **주의**: `claude plugin update`는 버전이 동일하면 "already at the latest version"을 반환합니다. 파일 변경 시에는 반드시 uninstall → install 순서로 재설치해야 합니다.

### Step 4: Git Status 체크

```bash
cd {base_path} && git status --porcelain
```

- `M`: 수정됨, `A`: 새 파일, `D`: 삭제됨, `??`: 추적 안됨

### Step 5: 결과 출력

```markdown
## 🔍 Plugin Check 결과

### 대상: {plugin_name or "전체"}

### ✅ 파일 검증
| 유형 | 등록 | 실제 | 상태 |
|------|------|------|------|
| Agents | 5 | 5 | ✅ |
| Commands | 4 | 4 | ✅ |

### ❌ 오류
- Missing agent: ./agents/xxx.md

### ⚠️ 경고
- Unregistered command: ./commands/yyy.md

### 👻 Orphaned Cache (캐시에만 존재)
| 파일 | 조치 |
|------|------|
| paper-researcher.md | `rm ~/.claude/plugins/cache/.../agents/paper-researcher.md` |

### 🔄 Missing from Cache (소스에만 존재)
| 파일 | 조치 |
|------|------|
| financial-intelligence.md | `claude plugin uninstall && install` 또는 수동 복사 |

### 📝 Git Status
M  plugins/xxx/agents/paper-processor.md

### 📋 다음 단계
1. [ ] 오류 수정
2. [ ] 미등록 파일 marketplace.json에 추가
3. [ ] Claude Code 재시작
```

---

## 검증 항목 요약

| # | 검증 항목 | 설명 |
|---|-----------|------|
| 1 | 파일 존재 | marketplace.json에 등록된 파일이 실제 존재하는지 |
| 2 | 미등록 파일 | 실제 존재하지만 marketplace.json에 없는 파일 |
| 3 | Orphaned Cache | 캐시에만 존재하고 실제 폴더에 없는 파일 (👻) |
| 4 | Missing from Cache | 소스에 존재하지만 캐시에 없는 파일 (🔄) |
| 5 | Git 상태 | 커밋 안 된 변경사항 |

---

## 재시작이 필요한 경우

다음 파일 변경 시 Claude Code 재시작 필요:
- `marketplace.json`, `agents/*.md`, `commands/*.md`, `.claude/settings.json`

```bash
Ctrl+C && claude  # 또는 /quit
```

---

## 사용 예시

```bash
/plugin-check vehicle-contamination-or  # 특정 플러그인
/plugin-check                            # 전체 플러그인
```
