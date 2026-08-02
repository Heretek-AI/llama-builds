# llama-builds — Core

## What it is
CI/CD registry for llama.cpp family builds. Builds, validates, publishes manifests for upstream llama.cpp and community forks.

## Key components
- `action.yml` — Composite GitHub Action for building CMake-based llama.cpp forks
- `targets/*/build.sh` — Each target has METADATA header scraped by generate_manifest
- `scripts/generate_manifest.py` — Walks targets, extracts METADATA, emits manifest.json
- `scripts/audit_matrix.py` — Validates manifest↔matrix consistency + schema
- `scripts/version_tag.py` — Generates `{sha_prefix}-{build_number}` tags
- `scripts/upstream_sha_tester.py` — Tests new upstream SHAs before release
- `schemas/manifest.schema.json` — JSON Schema v2 for manifest validation
- `src/heretek_builds/` — Python package (currently empty `__init__.py`)
- `manifest.json` — Generated output (targets + version info)

## Architecture
Flat structure. No web server. No database. Purely file-based CI tooling.
- Scripts are run as `python -m scripts.<name>`
- Tests in `tests/` mirror script structure (test_<script>.py)
- `targets/_template/build.sh` — Template for new targets

## Invariants
- `manifest.json` version field is integer const (currently 2), bump on schema changes
- Target slugs: `^[a-z0-9][a-z0-9-]*$` (lowercase alphanumeric + hyphens)
- Version tags: `{7-char-sha}-{build_number}` format
- METADATA required fields: name, repo, ref, backend, arch, capabilities
- Backends: cpu, cuda, rocm, vulkan, docs

## Entry points
- `python -m scripts.generate_manifest` → writes manifest.json
- `python -m scripts.audit_matrix` → validates manifest + matrix
- `python -m scripts.upstream_sha_tester --repo X --sha Y` → tests upstream SHA
- `python -m heretek_builds --help` → (empty package, placeholder)

## File references
- Spec: `docs/superpowers/specs/`
- Runbooks: `docs/superpowers/runbooks/`
- Plans: `docs/superpowers/plans/`
