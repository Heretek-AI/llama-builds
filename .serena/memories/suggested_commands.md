# Commands

## Dev
```bash
# Generate manifest from targets
python -m scripts.generate_manifest

# Validate manifest + matrix
python -m scripts.audit_matrix

# Test upstream SHA
python -m scripts.upstream_sha_tester --repo ggml-org/llama.cpp --sha abc1234
```

## Test
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_generate_manifest.py -v

# Run with coverage
pytest tests/ --cov=scripts --cov-report=xml
```

## Lint
```bash
# Ruff lint
ruff check .

# Ruff format check
ruff format --check .

# Pre-commit (all hooks)
pre-commit run --all-files
```

## CI checks (must pass before merge)
1. `pre-commit` — whitespace, yaml/json, ruff, secrets
2. `super-linter` — Python, YAML, JSON, Shell, Markdown
3. `sonarcloud` — quality gate + coverage
4. `gitleaks` — secret detection

## Git
```bash
# Branch naming: feat/<scope>, fix/<scope>, chore/<scope>
# Commits: Conventional Commits
# PRs require linked Issue (Closes #<id>)
```
