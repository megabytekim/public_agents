---
name: stock-git-add-push
description: Git add and push specific files only. Useful for agents to commit analysis results.
arguments:
  - name: files
    description: File path(s) to add and push (single path or comma-separated paths)
    required: true
  - name: message
    description: Commit message
    required: false
    default: "Update stock analysis"
---

# Stock Git Add Push Command

This command performs a **precise git add and push** for specified files only.

## Purpose

When agent workers complete analysis and write to files, this skill commits **only those specific files** without touching other staged/unstaged changes in the repository.

## Usage Examples

```bash
# Single file
/stock-git-add-push files="stock_checklist/NVIDIA_NVDA/stock_analyzer_summary.md"

# Multiple files (comma-separated)
/stock-git-add-push files="stock_checklist/삼성전자_005930/stock_analyzer_summary.md,stock_checklist/두산_034020/stock_analyzer_summary.md" message="Add Samsung and 두산 analysis"

# With custom message
/stock-git-add-push files="stock_checklist/케이옥션_102370/stock_analyzer_summary.md" message="Add 케이옥션 deep analysis"
```

## Execution Flow

### Step 0: Validate Path is Stock Analysis (CRITICAL)

```python
import re

# ONLY allow files in stock_checklist/{종목명}_{종목코드}/ format
ALLOWED_PATH_PATTERN = r"^stock_checklist/[^/]+_[^/]+/.+\.md$"

for file_path in files.split(","):
    file_path = file_path.strip()

    # Check if path matches stock analysis pattern
    if not re.match(ALLOWED_PATH_PATTERN, file_path):
        raise ValueError(f"REJECTED: {file_path}")
        print("Only stock_checklist/{{종목명}}_{{종목코드}}/ paths are allowed")
        return

    # Extract folder name and validate format
    folder_name = file_path.split("/")[1]  # e.g., "삼성전자_005930"
    if "_" not in folder_name:
        raise ValueError(f"REJECTED: Invalid folder format: {folder_name}")
        print("Folder must be {{종목명}}_{{종목코드}} format")
        return

print(f"✅ Path validated: {file_path}")
```

### Step 1: Validate Files Exist

```python
# Verify all specified files exist before proceeding
for file_path in files.split(","):
    file_path = file_path.strip()
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
```

### Step 2: Git Add (Specific Files Only)

```bash
# Add ONLY the specified files
git add {{files}}

# For multiple files:
# git add file1.md file2.md file3.md
```

### Step 3: Git Commit

```bash
# Commit with message
git commit -m "{{message}}"
```

### Step 4: Git Push

```bash
# Push to current branch
git push
```

## Safety Rules

1. **Path Validation**: ONLY allow `stock_checklist/{종목명}_{종목코드}/` paths
2. **File Validation**: Always verify files exist before git add
3. **Specific Files Only**: Never use `git add .` or `git add -A`
4. **No Force Push**: Never use `--force` flag
5. **Current Branch**: Push to the current branch only
6. **Error Handling**: If any step fails, stop and report

### Allowed Paths (Examples)
```
✅ stock_checklist/삼성전자_005930/stock_analyzer_summary.md
✅ stock_checklist/NVIDIA_NVDA/stock_analyzer_summary.md
✅ stock_checklist/케이옥션_102370/stock_analyzer_summary.md

❌ plugins/stock-analyzer-advanced/watchlist/stocks/...
❌ random/path/file.md
❌ stock_checklist/invalid_folder/file.md (no ticker code)
```

## Error Handling

```python
# If git add fails
if "fatal" in result or "error" in result:
    report_error("Git add failed", result)
    return

# If git commit fails (nothing to commit)
if "nothing to commit" in result:
    report_info("No changes to commit for specified files")
    return

# If git push fails
if "rejected" in result or "failed" in result:
    report_error("Git push failed - may need to pull first", result)
    return
```

## Execution

When this command is invoked:

```
Git Add & Push: {{files}}
Message: {{message}}

Step 0: Validating path is stock_checklist/{종목명}_{종목코드}/...
Step 1: Validating file(s) exist...
Step 2: Adding file(s) to staging...
Step 3: Committing changes...
Step 4: Pushing to remote...
```

### Implementation

```bash
# 0. Validate path is stock analysis (CRITICAL)
# Using case statement for POSIX compatibility (works in bash/zsh/sh)
for file in {{files//,/ }}; do
    # Must start with stock_checklist/
    case "$file" in
        stock_checklist/*)
            ;;
        *)
            echo "❌ REJECTED: $file"
            echo "Only stock_checklist/ paths are allowed"
            exit 1
            ;;
    esac

    # Extract folder name (second component)
    folder=$(echo "$file" | cut -d'/' -f2)

    # Folder must contain underscore (종목명_종목코드 format)
    case "$folder" in
        *_*)
            echo "✅ Path validated: $file"
            ;;
        *)
            echo "❌ REJECTED: Invalid folder format: $folder"
            echo "Folder must be {종목명}_{종목코드} format"
            exit 1
            ;;
    esac
done

# 1. Verify files exist
for file in {{files//,/ }}; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: File not found: $file"
        exit 1
    fi
done

# 2. Git add specific files only
git add {{files//,/ }}

# 3. Check if there are changes to commit
if git diff --cached --quiet; then
    echo "ℹ️ No changes to commit for specified files"
    exit 0
fi

# 4. Commit with message
git commit -m "$(cat <<'EOF'
{{message}}
EOF
)"

# 5. Push to remote
git push
```

---

## Output Format

### Success

```
Git Add & Push completed.

Files committed:
- {{file1}}
- {{file2}}

Commit: abc1234
Branch: main
Remote: origin
```

### Failure

```
Git Add & Push failed.

Error: {{error_message}}
Step: {{failed_step}}

Suggested action: {{suggestion}}
```
