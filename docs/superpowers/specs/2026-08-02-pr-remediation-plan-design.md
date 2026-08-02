# PR Remediation Plan Design

**Date:** 2026-08-02
**Status:** Approved
**Author:** Team review (6 parallel reviewers)

## Problem

6 open PRs on Heretek-AI/llama-builds have review findings that must be resolved before merging. PRs form a dependency chain, and 3 of them have blocking issues.

## PR Dependency Graph

```
#38 (sonarcloud bump)     ─── independent
#39 (repo cleanup)        ─── independent ──→ #40
#41 (build template)      ─── independent
#40 (manifest foundation) ─── depends on #39 ──→ #42, #43
#42 (upstream SHA tester) ─── depends on #40
#43 (Pages workflow)      ─── depends on #40
```

## Approach: Parallel Fix → Dependency-Ordered Merge

### Phase 1: Fix (Parallel)

All 6 PRs get fix commits pushed to existing branches simultaneously. Fixes are independent — no cross-PR coordination needed during this phase.

| PR | Findings to Fix | Commit Message |
|----|----------------|---------------|
| #38 | None (approved as-is) | — |
| #39 | Add `.mcp.json` to `.gitignore`; update AGENTS.md to remove `.mcp.json` from project structure | `fix: add .mcp.json to gitignore, update AGENTS.md` |
| #41 | Extend placeholder test to validate all 6 METADATA fields; add ref minimum length assertion; add slug exclusion test for `_template` | `fix: extend template tests for full field coverage` |
| #40 | Fix duplicate audit error reporting; skip disabled matrix entries in `_parse_matrix_targets`; validate backend vs directory name; add schema versioning documentation; fix METADATA blank-line early termination; warn on missing `arch` instead of silent default; align README/runbook references | `fix: address review findings — audit dedup, disabled entries, metadata parsing` |
| #42 | Validate `repo` parameter format (`owner/repo`); fix `SCHEMA_PATH` to absolute path; replace hardcoded timestamp with dynamic; catch `json.JSONDecodeError`; surface git stderr in errors; add tests for clone_repo, schema validation, and no-METADATA paths | `fix: input validation, error handling, and test coverage` |
| #43 | Add `workflow_dispatch` trigger; use `with` context managers for file I/O; consistent `python` (not `python3`); remove unused `safe` variable; add explicit top-level key filtering in redaction | `fix: workflow_dispatch, file handles, redaction defense-in-depth` |

### Phase 2: Merge (Dependency-Ordered)

Each merge waits for all 4 required CI checks to pass (super-linter, pre-commit, sonarcloud, gitleaks).

**Step 1 — Parallel merge (no dependencies):**
- Merge #38 (sonarcloud bump) — squash merge
- Merge #39 (repo cleanup) — squash merge
- Merge #41 (build template) — squash merge

**Step 2 — Rebase and merge #40:**
- Rebase `feat/ci/manifest-foundation` onto updated main (may conflict with #39's `.gitignore` and scaffolding)
- Resolve conflicts if any (expected: simple `.gitignore` additions)
- Push, wait for CI, squash merge

**Step 3 — Parallel merge (both depend on #40):**
- Rebase #42 onto updated main, push, wait for CI, squash merge
- Rebase #43 onto updated main, push, wait for CI, squash merge

**Branch cleanup:**
- Delete each remote branch after merge (`git push origin --delete <branch>`)

### Phase 3: Post-Merge Verification

1. `ruff check .` on main — confirm lint passes
2. `python -m scripts.generate_manifest` — verify manifest generation
3. `python -m scripts.audit_matrix --matrix .github/workflows/matrix.yml --manifest manifest.json --schema schemas/manifest.schema.json` — verify audit passes
4. `gh workflow run manifest-pages.yml --ref main` — verify Pages workflow triggers
5. `git log --oneline main` — confirm all 6 PRs merged

## Risk Mitigation

**Rebase conflicts:** PR #40 most likely to conflict with #39 (both touch repo structure). Conflicts will be simple `.gitignore` and directory additions.

**CI failures on fix commits:** Fix-forward with additional commits. Do not revert. Pre-commit hooks catch lint issues early via PostToolUse hook.

**Merge order enforcement:** Do not merge dependent PRs before their prerequisites. #42 and #43 MUST wait for #40 to land on main.

## Critical Findings Reference

| Severity | Count | PRs Affected |
|----------|-------|--------------|
| Critical | 2 | #43 (missing scripts/schemas, missing workflow_dispatch) |
| High | 6 | #40 (3 correctness bugs), #42 (2 security/reliability issues) |
| Medium | 8 | Across #40, #42, #41, #39 |
| Low | 10 | Style, test coverage, documentation |
