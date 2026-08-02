# Matrix Workflow Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `.github/workflows/matrix.yml` — a two-job workflow that dynamically discovers build targets and expands a matrix for cross-backend builds.

**Architecture:** A `discover` job globs `targets/*/build.sh`, builds a JSON matrix from directory names, and outputs it. A `build` job consumes the matrix via `fromJson()`, with an `if:` guard so empty matrices skip cleanly. Pattern follows lemonade-sdk/llamacpp-rocm's proven approach.

**Tech Stack:** GitHub Actions, shell (bash), JSON (jq-style output via echo)

## Global Constraints

- Python 3.11+, Linux x86_64 target
- Pre-commit hooks run on every file edit (ruff, trailing whitespace, YAML check)
- Four required CI checks: super-linter, pre-commit, sonarcloud, gitleaks
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`
- Commits: Conventional Commits
- PRs must link a GitHub Issue

---

### Task 1: Create the matrix workflow

**Files:**
- Create: `.github/workflows/matrix.yml`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: `.github/workflows/matrix.yml` with two jobs: `discover` and `build`

- [ ] **Step 1: Create the workflow file with triggers and the discover job**

```yaml
name: Matrix Build

on:
  pull_request:
  workflow_dispatch:

jobs:
  discover:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
      target_count: ${{ steps.set-matrix.outputs.target_count }}
    steps:
      - uses: actions/checkout@v4

      - name: Discover build targets
        id: set-matrix
        run: |
          # Glob targets/*/build.sh and build a JSON matrix
          targets=()
          for build_script in targets/*/build.sh; do
            if [ -f "$build_script" ]; then
              target=$(basename "$(dirname "$build_script")")
              targets+=("$target")
            fi
          done

          target_count=${#targets[@]}
          echo "target_count=$target_count" >> "$GITHUB_OUTPUT"

          if [ "$target_count" -eq 0 ]; then
            echo "No targets found in targets/*/build.sh"
            echo 'matrix={"include":[]}' >> "$GITHUB_OUTPUT"
            exit 0
          fi

          echo "Found $target_count target(s): ${targets[*]}"

          # Build JSON matrix with include entries
          matrix='{"include":['
          first=true
          for target in "${targets[@]}"; do
            if [ "$first" = true ]; then
              first=false
            else
              matrix+=','
            fi
            matrix+="{\"target\":\"$target\",\"backend\":\"$target\",\"arch\":\"x86_64\"}"
          done
          matrix+=']}'

          echo "matrix=$matrix" >> "$GITHUB_OUTPUT"
          echo "Generated matrix: $matrix"
```

- [ ] **Step 2: Add the build job that consumes the matrix**

Append the build job to the same file:

```yaml
  build:
    needs: discover
    if: fromJson(needs.discover.outputs.matrix).include[0]
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: ${{ fromJson(needs.discover.outputs.matrix) }}
    steps:
      - name: Print matrix info
        run: |
          echo "Target:   ${{ matrix.target }}"
          echo "Backend:  ${{ matrix.backend }}"
          echo "Arch:     ${{ matrix.arch }}"
          echo ""
          echo "Skeleton only — no build steps yet."
          echo "Real builds will be added when targets/*/build.sh"
          echo "contains actual build logic."
```

- [ ] **Step 3: Validate the YAML parses cleanly**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/matrix.yml'))"`
Expected: No output (clean parse)

- [ ] **Step 4: Run pre-commit on the new file**

Run: `pre-commit run --files .github/workflows/matrix.yml`
Expected: All hooks pass (trailing-whitespace, end-of-file-fixer, check-yaml)

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/matrix.yml
git commit -m "ci: add matrix workflow skeleton with dynamic target discovery

Creates .github/workflows/matrix.yml with a two-job pattern:
- discover job globs targets/*/build.sh and emits a JSON matrix
- build job consumes the matrix via fromJson() with fail-fast: false
- Empty matrix skips the build job cleanly via if: guard

Pattern follows lemonade-sdk/llamacpp-rocm's proven approach.

Closes #1"
```

---

### Task 2: Verify the workflow with an empty targets directory

**Files:**
- None created or modified (verification only)

**Interfaces:**
- Consumes: `.github/workflows/matrix.yml` from Task 1
- Produces: confidence that empty-matrix edge case works

- [ ] **Step 1: Confirm targets/ directory doesn't exist yet**

Run: `ls -la targets/ 2>&1 || echo "targets/ does not exist (expected)"`
Expected: "targets/ does not exist (expected)"

- [ ] **Step 2: Simulate the discover job's matrix output locally**

Run:
```bash
matrix='{"include":[]}'
echo "Matrix: $matrix"
echo "Include count: $(echo "$matrix" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['include']))")"
```
Expected: Include count: 0

- [ ] **Step 3: Verify the if: guard expression evaluates correctly**

Run:
```bash
python3 -c "
import json
matrix = json.loads('{\"include\":[]}')
# This is what GitHub evaluates: fromJson(...).include[0]
try:
    result = matrix['include'][0]
    print(f'Guard would be: {result}')
except IndexError:
    print('Guard evaluates to empty/false — job will skip (correct)')
"
```
Expected: "Guard evaluates to empty/false — job will skip (correct)"
