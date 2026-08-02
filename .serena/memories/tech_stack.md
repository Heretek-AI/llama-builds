# Tech Stack

## Language
- Python 3.11+
- Bash (build scripts, CI actions)
- YAML (CI workflows, configs)
- JSON (manifests, schemas)

## Build/packaging
- `setuptools` (pyproject.toml implied by `python -m build`)
- `pip` for dependency management
- `ruff` for linting + formatting (v0.4.7 in pre-commit)

## Testing
- `pytest` — test runner
- `jsonschema` — manifest validation (optional import, graceful fallback)

## CI/CD
- GitHub Actions (5 workflows: matrix, pre-commit, sonarcloud, super-linter, manifest-pages)
- `pre-commit` hooks: trailing-whitespace, end-of-file-fixer, check-yaml, check-json, check-added-large-files, check-merge-conflict, check-case-conflict, detect-private-key, ruff, ruff-format, betterleaks
- SonarCloud integration (project: Heretek-AI_llama-builds)
- Gitleaks secret scanning

## Key dependencies (runtime)
- `yaml` (PyYAML) — matrix parsing
- `jsonschema` — optional, schema validation
- `pathlib` — file operations throughout

## OS/arch target
- Linux x86_64 (build host)
- Outputs target Linux builds for llama.cpp
