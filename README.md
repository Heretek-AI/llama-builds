# llama-builds

CI/CD registry for the llama.cpp ecosystem — builds, validates, and publishes
manifests for upstream llama.cpp and community forks.

## Quick start

```bash
# Generate manifest from targets
python -m scripts.generate_manifest

# Validate manifest against matrix
python -m scripts.audit_matrix
```

## Project structure

```
targets/          Build targets (targets/*/build.sh with METADATA headers)
schemas/          JSON Schema definitions (manifest.schema.json)
scripts/          CI tooling (generate_manifest.py, audit_matrix.py)
tests/            Test suite
docs/             Design docs, specs, and runbooks
```

## Tracking

This project is seeded from `seeds/llama-builds.yaml`. Re-running the seed
script is idempotent — issues are matched by seed-id and will not duplicate:

```bash
# Re-seed issues (idempotent)
./scripts/seed-issues.sh seeds/llama-builds.yaml
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming, commit conventions,
and PR requirements.
