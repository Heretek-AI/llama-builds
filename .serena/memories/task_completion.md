# Task Completion Checklist

## Before claiming done
1. `ruff check .` — must pass (zero errors)
2. `ruff format --check .` — must pass
3. `pytest tests/ -v` — all tests must pass
4. `python -m scripts.generate_manifest` — manifest regeneration works
5. `python -m scripts.audit_matrix` — manifest/matrix consistency holds

## CI checks (4 required on main)
1. `pre-commit` — all hooks pass
2. `super-linter` — no lint errors
3. `sonarcloud` — quality gate passes
4. `gitleaks` — no secrets detected

## Verification pattern
```bash
# Quick verification
ruff check . && ruff format --check . && pytest tests/ -v

# Full CI equivalent
pre-commit run --all-files
python -m scripts.generate_manifest
python -m scripts.audit_matrix
```

## Common failures
- `jsonschema` not installed → schema validation skipped (graceful, not a failure)
- YAML parse errors in matrix.yml → `_parse_matrix_targets` returns empty set
- Missing METADATA fields → `extract_metadata` returns None, target skipped
