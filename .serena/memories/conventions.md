# Conventions

## Code style
- Python: ruff-enforced (lint + format)
- Type hints: used throughout (`dict | None`, `list[str]`, `tuple[str, int]`)
- Docstrings: Google-style (Args/Returns/Raises sections)
- `from __future__ import annotations` — always at top
- `Path` for all file operations (never string paths)

## Python patterns
- Scripts as modules: `python -m scripts.<name>` (not standalone scripts)
- `main(argv=None)` pattern — accepts sys.argv or explicit args for testing
- `sys.exit(main())` at module level
- `argparse` for CLI argument parsing
- `warnings.warn()` for non-fatal issues (missing optional fields)
- Functions return `list[str]` for errors (empty = success)

## METADATA block format
```bash
# METADATA
# name=Human-readable name
# repo=owner/repo
# ref=<pinned-sha-or-tag>
# backend=cpu|cuda|rocm|vulkan|docs
# arch=x86_64|aarch64
# capabilities=chat,embed
```
Parsed by `scripts/generate_manifest.py::extract_metadata()`.

## File organization
- `scripts/` — CI tooling (not a Python package, no __init__.py)
- `src/heretek_builds/` — Python package (empty, placeholder)
- `tests/test_<script>.py` — one test file per script
- `targets/<slug>/build.sh` — one directory per build target

## Naming
- Target slugs: lowercase, hyphen-separated (`upstream-cpu`)
- Script files: snake_case (`generate_manifest.py`)
- Test files: `test_<script>.py` matching script name
- Manifest keys match target slug exactly

## Git
- Branch: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`
- Commits: Conventional Commits
- PRs: linked Issue required (`Closes #<id>`)
- No direct pushes to `main`
