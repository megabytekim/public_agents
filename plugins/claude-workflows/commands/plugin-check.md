---
description: 플러그인 수정 후 검증. 사용법 - /plugin-check [plugin-name] (예- vehicle-contamination-or)
allowed-tools: Read, Glob, Bash
argument-hint: [plugin-name]
---

# Plugin Check - 플러그인 수정 후 검증

플러그인 수정 후 필요한 체크리스트를 자동으로 검증합니다.

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

# 등록 안 된 파일 체크
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

### Step 4: Git Status 체크

```bash
cd {base_path} && git status --porcelain
```

변경된 파일이 있으면:
- `M` (Modified): 수정됨
- `A` (Added): 새 파일
- `D` (Deleted): 삭제됨
- `??` (Untracked): 추적 안됨

### Step 5: 결과 출력

```markdown
## 🔍 Plugin Check 결과

### 대상 플러그인
- {plugin_name or "전체"}

### ✅ 파일 검증
| 유형 | 등록 | 실제 | 상태 |
|------|------|------|------|
| Agents | 5 | 5 | ✅ |
| Commands | 4 | 4 | ✅ |

### ❌ 오류 (있다면)
- Missing agent: ./agents/xxx.md

### ⚠️ 경고 (있다면)
- Unregistered command: ./commands/yyy.md

### 📝 Git Status
```
M  plugins/xxx/agents/paper-processor.md
M  .claude-plugin/marketplace.json
```

### 🔄 재시작 필요 여부
{changes_detected ? "⚠️ Claude Code 재시작 필요" : "✅ 재시작 불필요"}

### 📋 다음 단계
1. [ ] 오류 수정 (있다면)
2. [ ] 미등록 파일 marketplace.json에 추가 (필요시)
3. [ ] Claude Code 재시작: `Ctrl+C` → `claude`
4. [ ] `/agents` 또는 `/skills` 로 등록 확인
```

---

## 검증 항목 체크리스트

| # | 검증 항목 | 설명 |
|---|-----------|------|
| 1 | **파일 존재** | marketplace.json에 등록된 파일이 실제 존재하는지 |
| 2 | **미등록 파일** | 실제 존재하지만 marketplace.json에 없는 파일 |
| 3 | **Git 상태** | 커밋 안 된 변경사항 |
| 4 | **재시작 필요** | agents/commands 변경 시 재시작 필요 |

---

## 재시작이 필요한 경우

다음 파일이 변경되면 Claude Code 재시작 필요:
- `marketplace.json` (플러그인 등록 정보)
- `agents/*.md` (에이전트 정의)
- `commands/*.md` (커맨드 정의)
- `.claude/settings.json` (설정 파일)

### 재시작 방법

```bash
# 방법 1: 터미널에서
Ctrl+C  # Claude Code 종료
claude  # 재시작

# 방법 2: Claude Code 내에서
/quit   # 종료 후 재실행
```

---

## 사용 예시

```bash
# 특정 플러그인 체크
/plugin-check vehicle-contamination-or
/plugin-check claude-workflows

# 전체 플러그인 체크
/plugin-check
```

---

## 자동 수정 제안

오류 발견 시 자동 수정 옵션 제공:

### 1. 누락된 파일 marketplace.json에 추가
```
감지: agents/new-agent.md가 등록되지 않음
제안: marketplace.json의 agents 배열에 "./agents/new-agent.md" 추가?
```

### 2. 삭제된 파일 marketplace.json에서 제거
```
감지: agents/old-agent.md가 존재하지 않음
제안: marketplace.json에서 "./agents/old-agent.md" 제거?
```
