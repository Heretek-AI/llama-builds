# Build Action Design: Standardized GitHub Action for llama.cpp Forks

**Date:** 2026-08-02
**Status:** Approved — ready for implementation planning
**Supersedes:** N/A (new design)

## Problem Statement

llama-builds has 28 open issues for packaging llama.cpp forks, bindings, and
tooling. Each has different build requirements (CMake, cibuildwheel, podman,
wasm-pack, colcon, etc.), but the core CMake-based builds share ~90% of their
pipeline. We need a standardized GitHub Action that eliminates per-fork build
boilerplate while remaining flexible enough to handle non-CMake builds.

The primary consumer is lemonade-server, which expects a specific artifact
format. We define our own contract first; lemonade compatibility is a mapping
layer.

## Goals

1. **Eliminate per-fork boilerplate** — New CMake-based targets should require
   only a `build.sh` with a METADATA header, not a custom workflow.
2. **Define our own artifact contract** — Not dictated by lemonade. Lemonade
   compatibility is an optional post-build transform.
3. **Two-tier architecture** — Core action for CMake builds (~15 issues),
   adapter pattern for non-CMake builds (~13 issues).
4. **Single target per invocation** — The caller workflow provides the matrix.
   The action is simple and composable.
5. **Traceable versioning** — Version tags encode the upstream ref + build
   number (e.g. `abc1234-3`).

## Non-Goals

- Multi-target builds within a single action invocation.
- Auto-updating upstream refs (manual refresh only).
- Publishing to PyPI, NuGet, or other package registries (only GitHub releases).

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                Caller Workflow                       │
│  (matrix.yml — provides target matrix)              │
│                                                     │
│  ┌──────────────────┐    ┌──────────────────┐      │
│  │  build-llama     │    │  build-llama-*   │      │
│  │  (composite)     │    │  (adapter)       │      │
│  │                  │    │                  │      │
│  │  CMake-based     │    │  Python wheels   │      │
│  │  forks only      │    │  OCI images      │      │
│  │                  │    │  Wasm canisters  │      │
│  │  CPU/CUDA/ROCm/  │    │  Docs            │      │
│  │  Vulkan          │    │  Bindings        │      │
│  └────────┬─────────┘    └────────┬─────────┘      │
│           │                       │                 │
│           ▼                       ▼                 │
│  ┌──────────────────────────────────────────┐      │
│  │         Artifact Contract                │      │
│  │  llama-{version}-{os}-{backend}-        │      │
│  │  {arch}[-{gpu_target}].tar.gz            │      │
│  └──────────────────────────────────────────┘      │
│           │                                         │
│           ▼                                         │
│  ┌──────────────────────────────────────────┐      │
│  │         Manifest (our schema)            │      │
│  │  + Lemonade adapter (optional)           │      │
│  └──────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

### Tier 1: Core Action (`build-llama`)

A composite GitHub Action that handles any CMake-based llama.cpp fork.

**Inputs:**

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `repo` | yes | — | GitHub `owner/repo` to build |
| `ref` | yes | — | Git SHA, tag, or branch |
| `backend` | yes | — | `cpu`, `cuda`, `rocm`, `vulkan` |
| `arch` | no | `x86_64` | Target architecture |
| `gpu_target` | no | — | GPU ISA family (e.g. `gfx1151`, `sm_89`) |
| `rocm_version` | no | — | ROCm version (e.g. `6.2.0`) |
| `cuda_version` | no | — | CUDA version (e.g. `12.6`) |
| `cmake_flags` | no | — | Extra CMake flags (space-separated) |
| `build_type` | no | `Release` | CMake build type |

**Steps:**

1. **Checkout** — Clone the target repo at the specified ref.
2. **Detect build system** — Verify `CMakeLists.txt` exists, extract upstream
   version/tag from the repo.
3. **Install dependencies** — Backend-specific:
   - CPU: No extra deps.
   - CUDA: Install CUDA toolkit via `nvidia-cuda-toolkit` or official action.
   - ROCm: Download ROCm nightly tarball from `rocm.nightlies.amd.com` (same
     approach as lemonade-sdk/llamacpp-rocm).
   - Vulkan: Install Vulkan SDK.
4. **CMake configure** — Set `CMAKE_BUILD_TYPE`, enable backend-specific flags
   (`GGML_CUDA`, `GGML_HIP`, `GGML_VULKAN`), set `CMAKE_INSTALL_PREFIX`.
5. **Build** — `cmake --build . --config Release -j$(nproc)`.
6. **Collect artifacts** — Binaries (`llama-server`, `llama-cli`, `llama-bench`,
   `llama-quantize`) + required runtime libs (ROCm: `rocblas/`, `hipblaslt/`;
   CUDA: relevant `.so` files).
7. **Set RPATH** (Linux) — `$ORIGIN` for portable distribution.
8. **Archive** — `tar.gz` with flat structure matching artifact contract.
9. **Emit manifest entry** — JSON blob as step output for downstream consumption.

**Outputs:**

| Output | Description |
|--------|-------------|
| `artifact_path` | Path to the archived build |
| `manifest_entry` | JSON string — single target entry for manifest schema |
| `resolved_sha` | Full SHA of the built ref |
| `version_tag` | Generated version tag (e.g. `abc1234-1`) |

**Backend-specific build flags:**

| Backend | CMake Flags | Dependencies |
|---------|-------------|--------------|
| `cpu` | (none — defaults) | None |
| `cuda` | `-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES={sm_*}` | CUDA toolkit |
| `rocm` | `-DGGML_HIP=ON -DGGML_HIP_NARCH=1 -DKOMPILE_VERSION={gfx}` | ROCm tarball |
| `vulkan` | `-DGGML_VULKAN=ON` | Vulkan SDK |

### Tier 2: Adapters

Each adapter is a standalone composite action for non-CMake builds. All adapters
output to the same artifact contract.

**Planned adapters:**

| Adapter | Issues | Build System | Output |
|---------|--------|--------------|--------|
| `build-llama-python` | #22, #23 | cibuildwheel / pip | Wheel files |
| `build-llama-oci` | #31 | podman / buildah | OCI image tarball |
| `build-llama-wasm` | #32 | wasm-pack | .wasm file |
| `build-llama-docs` | #34 | Static site gen | Markdown/HTML |
| `build-llama-bindings` | #24–#27 | Varied | Language-specific artifacts |

**Adapter contract:**

Each adapter must:
1. Accept `repo` and `ref` inputs (same as core action).
2. Accept adapter-specific inputs (e.g. `python_versions` for Python).
3. Output `artifact_path`, `manifest_entry`, `resolved_sha`, `version_tag`.
4. Use the same version tag format: `{upstream_ref_prefix}-{build_number}`.

**Non-adapter targets** (issues where the build is too unique to generalize):
- #30 paddler, #29 llama-swap, #28 LlamaFactory — full applications, not
  llama.cpp builds. Their `build.sh` scripts handle everything directly.

---

## Artifact Contract

### Naming Convention

```
llama-{version}-{os}-{backend}-{arch}[-{gpu_target}].tar.gz
```

Examples:
- `llama-abc1234-1-ubuntu-cpu-x86_64.tar.gz`
- `llama-abc1234-1-ubuntu-rocm-x86_64-gfx1151.tar.gz`
- `llama-abc1234-1-ubuntu-cuda-x86_64-sm_89.tar.gz`

### Version Format

`{upstream_ref_prefix}-{build_number}`

- `upstream_ref_prefix`: First 7 chars of the upstream SHA (e.g. `abc1234`).
- `build_number`: Sequential integer per upstream ref (starts at 1, increments
  on rebuild of the same ref).
- Full example: `abc1234-3` means "3rd build of upstream commit abc1234".

### Archive Contents

Flat directory structure:

```
llama-server          # Main server binary
llama-cli             # CLI binary
llama-bench           # Benchmark binary (if built)
llama-quantize        # Quantization tool (if built)
lib/                  # Required runtime libraries (backend-specific)
  rocblas/            # ROCm only — pre-tuned kernels
  hipblaslt/          # ROCm only — pre-tuned kernels
  ...
```

### Manifest Entry Schema

Extends the existing `schemas/manifest.schema.json` with new fields:

```json
{
  "name": "llama.cpp CPU baseline",
  "repo": "ggml-org/llama.cpp",
  "ref": "abc1234def5678",
  "backend": "cpu",
  "arch": "x86_64",
  "gpu_target": null,
  "capabilities": ["chat", "embed"],
  "version": "abc1234-1",
  "build": {
    "runner": "ubuntu-latest",
    "script": "targets/upstream-cpu/build.sh",
    "os": "ubuntu",
    "artifact": "llama-abc1234-1-ubuntu-cpu-x86_64.tar.gz"
  }
}
```

New fields (added to schema, not breaking existing entries):
- `version` (string) — The build version tag.
- `gpu_target` (string or null) — GPU ISA family.
- `build.os` (string) — Operating system used for the build.
- `build.artifact` (string) — Filename of the archived build.

---

## Lemonade Compatibility

Lemonade compatibility is a **post-build mapping layer**, not the primary
output format.

### Transform Script

`scripts/lemonade_adapter.py` transforms our manifest entries to lemonade's
expected format:

```python
def transform_to_lemonade(our_entry: dict) -> dict:
    """Transform our manifest entry to lemonade's expected format."""
    return {
        "repo": "lemonade-sdk/llamacpp-rocm",
        "filename": f"llama-{lemonade_tag}-{os}-rocm-{gpu_family}-x64.zip",
        "version": lemonade_tag,
        "sha256": compute_checksum(artifact_path),
    }
```

### Integration Points

1. **Artifact renaming**: Our `.tar.gz` → lemonade's `.zip` (lemonade expects
   zip on both OSes).
2. **Version mapping**: Our `{ref_prefix}-{build_num}` → lemonade's `b####`.
   A lookup table or auto-incrementing counter in the release workflow.
3. **GPU family mapping**: Our `gfx1151` → lemonade's `gfx1151` (1:1 for most
   targets; some need mapping like `gfx1200` → `gfx120X`).
4. **Runtime lib bundling**: Our core action already bundles ROCm libs — the
   adapter verifies structure matches lemonade's expectations.

### Activation

Lemonade compatibility is optional per target. Activated by setting
`lemonade_compatible: true` in the target's METADATA block or manifest entry.

---

## Caller Workflow Patterns

### Pattern A: Single-Target Workflow

```yaml
name: Build CPU
on: [push, workflow_dispatch]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: heretek/build-llama@v1
        id: build
        with:
          repo: ggml-org/llama.cpp
          ref: ${{ github.sha }}
          backend: cpu
      - uses: actions/upload-artifact@v4
        with:
          name: llama-cpu
          path: ${{ steps.build.outputs.artifact_path }}
```

### Pattern B: Matrix Workflow (CMake Targets)

```yaml
name: Matrix Build
on: [pull_request, workflow_dispatch]
jobs:
  discover:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v7
      - id: set-matrix
        run: |
          # Build matrix from targets/*/build.sh METADATA
          # Extracts: repo, ref, backend, arch, gpu_target
  build:
    needs: discover
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJson(needs.discover.outputs.matrix) }}
    steps:
      - uses: heretek/build-llama@v1
        id: build
        with:
          repo: ${{ matrix.repo }}
          ref: ${{ matrix.ref }}
          backend: ${{ matrix.backend }}
          arch: ${{ matrix.arch }}
          gpu_target: ${{ matrix.gpu_target }}
```

### Pattern C: Mixed Workflow (Core + Adapters)

```yaml
jobs:
  cmake-targets:
    # ... uses build-llama
  python-wheels:
    # ... uses build-llama-python
  oci-images:
    # ... uses build-llama-oci
  publish:
    needs: [cmake-targets, python-wheels, oci-images]
    # ... assembles manifest from all jobs, publishes
```

### Manifest Assembly

Each job outputs its `manifest_entry` JSON. A final `publish` job collects all
entries, merges them into a single manifest, validates against our schema, and
optionally runs the lemonade adapter.

---

## Target `build.sh` Pattern

For CMake-based targets, `build.sh` becomes thin — it exists for manifest
generation and local dev:

```bash
#!/usr/bin/env bash
# METADATA
# name=llama.cpp CPU baseline
# repo=ggml-org/llama.cpp
# ref=abc1234def5678
# backend=cpu
# arch=x86_64
# capabilities=chat,embed
set -euo pipefail

# The actual build logic lives in the composite action.
# This script exists for manifest generation and local dev.
echo "Use: heretek/build-llama action with repo=$REPO ref=$REF backend=$BACKEND"
```

For non-CMake targets, `build.sh` contains the full build logic.

---

## Testing Strategy

1. **Unit tests** — Test metadata extraction, version tag generation, manifest
   entry construction (extend existing `tests/`).
2. **Integration tests** — Use `act` to run the composite action locally against
   a known-good fork (e.g. `ggml-org/llama.cpp` at a pinned SHA).
3. **Matrix validation** — Extend `scripts/audit_matrix.py` to validate that
   all matrix entries have corresponding manifest entries and vice versa.
4. **Lemonade compatibility tests** — Verify that the transform script produces
   output matching lemonade's expected format.

---

## Migration Path

1. **Phase 1**: Implement core `build-llama` action + manifest schema updates.
   Ship with upstream CPU target (#7) as proof of concept.
2. **Phase 2**: Add CUDA (#8) and Vulkan (#9) targets. Validate matrix workflow.
3. **Phase 3**: Add ROCm target (#14) + lemonade adapter. Test against
   lemonade-server.
4. **Phase 4**: Implement adapters for Python (#22), OCI (#31), etc.
5. **Phase 5**: Fill in remaining specialized forks (#10–#21, #24–#27, #28–#34).

---

## Open Questions

1. **ROCm tarball source**: lemonade uses `rocm.nightlies.amd.com`. Should we
   pin a specific ROCm version or track nightlies? (Recommendation: pin stable
   version, allow override via `rocm_version` input.)
2. **GPU runner availability**: CUDA/ROCm builds need GPU runners. Do we use
   self-hosted runners or GitHub-hosted GPU runners? (Depends on org infra.)
3. **Smoke testing**: The issues mention smoke tests (run `llama-server` with a
   prompt). Should this be part of the action or a separate job? (Recommendation:
   Separate job — keeps the action focused on building.)
