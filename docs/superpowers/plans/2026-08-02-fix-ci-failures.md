# Fix CI Failures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three failed GitHub Actions workflows by updating action versions, replacing gitleaks with betterleaks, and fixing file hygiene issues.

**Architecture:** Update GitHub Actions workflow files to use latest action versions (checkout v7, setup-python v7, super-linter v8), replace gitleaks (requires license for orgs) with betterleaks (MIT licensed, no license needed) via pre-commit hook, and fix trailing whitespace/newline issues in config files.

**Tech Stack:** GitHub Actions, pre-commit, betterleaks, super-linter

## Global Constraints

- Use latest stable versions: `actions/checkout@v7`, `actions/setup-python@v7`, `super-linter/super-linter@v8`
- Replace `gitleaks/gitleaks` pre-commit hook with `betterleaks/betterleaks` v1.7.3
- Delete `secret-scan.yml` workflow entirely (redundant with pre-commit hook)
- Fix trailing whitespace in `.pre-commit-config.yaml`
- Add trailing newlines to `.claude/hooks/.lockfile` and `.heretek-harness.json`

---

## Task 1: Delete secret-scan.yml Workflow

**Files:**
- Delete: `.github/workflows/secret-scan.yml`

- [ ] **Step 1: Delete the workflow file**

```bash
rm .github/workflows/secret-scan.yml
```

- [ ] **Step 2: Verify deletion**

```bash
ls -la .github/workflows/
```

Expected: `secret-scan.yml` no longer listed

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/secret-scan.yml
git commit -m "ci: remove redundant secret-scan workflow

Gitleaks license requirement for orgs makes this impractical.
Betterleaks (via pre-commit) covers the same need without licensing."
```

---

## Task 2: Update .pre-commit-config.yaml

**Files:**
- Modify: `.pre-commit-config.yaml`

- [ ] **Step 1: Replace gitleaks hook with betterleaks**

Replace:
```yaml
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks
```

With:
```yaml
  - repo: https://github.com/betterleaks/betterleaks
    rev: v1.7.3
    hooks:
      - id: betterleaks
```

- [ ] **Step 2: Fix trailing whitespace on line 20**

Remove trailing whitespace after `ruff-format` (line 20 currently has trailing spaces).

- [ ] **Step 3: Verify changes**

```bash
cat .pre-commit-config.yaml
```

Expected: No trailing whitespace, betterleaks hook present

- [ ] **Step 4: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "ci: replace gitleaks with betterleaks in pre-commit

Betterleaks is MIT licensed (no org license needed), maintained by
original gitleaks author, and has better filtering capabilities."
```

---

## Task 3: Update pre-commit.yml Workflow

**Files:**
- Modify: `.github/workflows/pre-commit.yml`

- [ ] **Step 1: Update action versions and add betterleaks install**

Replace entire file with:
```yaml
name: pre-commit
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
  pull-requests: read
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with: { python-version: "3.11" }
      - run: pip install pre-commit
      - name: Install betterleaks
        run: |
          curl -sSL https://github.com/betterleaks/betterleaks/releases/download/v1.7.3/betterleaks_1.7.3_linux_x64.tar.gz | tar xz -C /usr/local/bin betterleaks
      - run: pre-commit run --all-files --show-diff-on-failure
```

- [ ] **Step 2: Verify changes**

```bash
cat .github/workflows/pre-commit.yml
```

Expected: Uses checkout@v7, setup-python@v7, includes betterleaks install step

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/pre-commit.yml
git commit -m "ci: update pre-commit workflow to latest versions

- Bump actions/checkout to v7
- Bump actions/setup-python to v7
- Add betterleaks binary installation step"
```

---

## Task 4: Update super-linter.yml Workflow

**Files:**
- Modify: `.github/workflows/super-linter.yml`

- [ ] **Step 1: Update action path and versions**

Replace entire file with:
```yaml
name: super-linter
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
  pull-requests: read
jobs:
  super-linter:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with: { fetch-depth: 0 }
      - uses: super-linter/super-linter@v8
        env:
          DEFAULT_BRANCH: main
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          VALIDATE_ALL_CODEBASE: false
          DISABLE_ERRORS: false
          VALIDATE_PYTHON: "true"
          VALIDATE_JAVASCRIPT: "false"
          VALIDATE_TYPESCRIPT: "false"
          VALIDATE_YAML: true
          VALIDATE_JSON: true
          VALIDATE_SHELL: true
          VALIDATE_MARKDOWN: true
          VALIDATE_GITHUB_ACTIONS: true
```

- [ ] **Step 2: Verify changes**

```bash
cat .github/workflows/super-linter.yml
```

Expected: Uses super-linter/super-linter@v8 (not github/super-linter), checkout@v7

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/super-linter.yml
git commit -m "ci: update super-linter to v8

- Fix action path from github/super-linter to super-linter/super-linter
- Bump to v8.7.0 (latest)
- Bump actions/checkout to v7"
```

---

## Task 5: Update matrix.yml Workflow

**Files:**
- Modify: `.github/workflows/matrix.yml`

- [ ] **Step 1: Update action version**

Change line 18 from:
```yaml
      - uses: actions/checkout@v4
```

To:
```yaml
      - uses: actions/checkout@v7
```

- [ ] **Step 2: Verify changes**

```bash
grep -n "uses:" .github/workflows/matrix.yml
```

Expected: Shows `actions/checkout@v7`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/matrix.yml
git commit -m "ci: bump actions/checkout to v7 in matrix workflow"
```

---

## Task 6: Fix File Hygiene

**Files:**
- Modify: `.claude/hooks/.lockfile`
- Modify: `.heretek-harness.json`

- [ ] **Step 1: Add trailing newline to .claude/hooks/.lockfile**

```bash
echo "" >> .claude/hooks/.lockfile
```

- [ ] **Step 2: Add trailing newline to .heretek-harness.json**

```bash
echo "" >> .heretek-harness.json
```

- [ ] **Step 3: Verify changes**

```bash
tail -c 1 .claude/hooks/.lockfile | xxd
tail -c 1 .heretek-harness.json | xxd
```

Expected: Both files end with newline character (0a)

- [ ] **Step 4: Commit**

```bash
git add .claude/hooks/.lockfile .heretek-harness.json
git commit -m "fix: add trailing newlines to config files

Pre-commit hooks require files to end with newline."
```

---

## Final Verification

- [ ] **Step 1: Run pre-commit locally to verify**

```bash
pre-commit run --all-files
```

Expected: All hooks pass

- [ ] **Step 2: Review all changes**

```bash
git log --oneline -6
```

Expected: 6 new commits for CI fixes

- [ ] **Step 3: Push to remote**

```bash
git push origin main
```
