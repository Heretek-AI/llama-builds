# llama-builds

CI/CD registry for the llama.cpp ecosystem — builds, validates, and publishes
manifests for upstream llama.cpp and community forks.

## Quick start

```bash
# Generate manifest from targets
python -m scripts.generate_manifest

# Validate manifest against matrix
python -m scripts.audit_matrix

# Run tests
pytest tests/ -v
```

## Project structure

```
action.yml        Composite GitHub Action for building llama.cpp forks
targets/          Build targets (targets/*/build.sh with METADATA headers)
schemas/          JSON Schema definitions (manifest.schema.json)
scripts/          CI tooling (generate_manifest.py, audit_matrix.py, version_tag.py)
tests/            Test suite
docs/             Design docs, specs, and runbooks
```

## Build Action

The `build-llama` composite action builds any CMake-based llama.cpp fork:

```yaml
- uses: heretek/build-llama@v1
  id: build
  with:
    repo: ggml-org/llama.cpp
    ref: ${{ github.sha }}
    backend: cpu # cpu, cuda, rocm, vulkan
```

**Inputs:** `repo`, `ref`, `backend`, `arch`, `gpu_target`, `rocm_version`, `cuda_version`, `cmake_flags`, `build_type`

**Outputs:** `artifact_path`, `manifest_entry`, `resolved_sha`, `version_tag`

See `docs/superpowers/specs/2026-08-02-build-action-design.md` for the full design.

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
