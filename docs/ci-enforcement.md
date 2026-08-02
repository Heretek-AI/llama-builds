# CI Enforcement

This document describes the required CI checks that must pass before any PR can merge into `main`.

## Required status checks

The following checks are enforced via GitHub branch protection rules on `main`:

| Check            | Workflow                             | What it validates                                                                               |
| ---------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------- |
| **pre-commit**   | `.github/workflows/pre-commit.yml`   | Trailing whitespace, end-of-file, YAML/JSON validity, ruff lint+format, betterleaks secret scan |
| **super-linter** | `.github/workflows/super-linter.yml` | Python (ruff), YAML, JSON, Shell, Markdown, GitHub Actions syntax                               |
| **sonarcloud**   | `.github/workflows/sonarcloud.yml`   | Code quality gate, test coverage, maintainability rating                                        |
| **betterleaks**  | (via pre-commit)                     | Secret detection across all tracked files                                                       |

## Matrix build validation

The matrix workflow (`.github/workflows/matrix.yml`) discovers targets from `targets/*/build.sh` and builds them. The `audit_matrix.py` script validates that:

1. Every manifest target has a matrix entry
2. Every matrix entry has a corresponding manifest target
3. No orphan entries exist in either direction

## How to add a new check

1. Create or update the workflow in `.github/workflows/`
2. Ensure the job name is stable (no random suffixes)
3. Add the job name to the required status checks in repo settings
4. Update this document

## How checks block merges

Branch protection rules on `main` require all listed status checks to pass before a PR can be merged. A failing secret scan, lint, or test will block the merge.
