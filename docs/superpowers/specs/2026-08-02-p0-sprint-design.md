# P0 Sprint Design: CUDA Matrix + Binary CLI

**Date**: 2026-08-02
**Status**: Approved
**Issues**: #64, #58

## Overview

This design covers two P0 features for llama-builds:
1. **CUDA Matrix Expansion** (#64) — expand from 2 to 5 CUDA builds covering 95%+ of users
2. **Binary Distribution CLI** (#58) — auto-detect GPU and install the right binary

Artifact signing (#59) is deferred until after the GitHub Action is working.

---

## Part 1: CUDA Matrix Expansion (#64)

### Problem

Currently `upstream-cuda` only builds sm_89/90 (Ada Lovelace + Hopper). Users with other GPUs (Ampere, Turing, Blackwell) can't use our builds.

### Key Insight

llama.cpp's CMakeLists.txt already supports universal builds via PTX fallback. When `CMAKE_CUDA_ARCHITECTURES` is not set, it builds for all supported architectures:
- `75-virtual 80-virtual 86-real` (always)
- `89-real 90-virtual` (CUDA 11.8+)
- `120a-real` (CUDA 12.8+)
- `121a-real` (CUDA 12.9+)

The `-virtual` suffix compiles as PTX, which gets JIT-compiled at runtime. This means one binary can run on any CUDA GPU.

### Strategy: Core + Universal

| Build | SM | Coverage | Rationale |
|-------|-----|----------|-----------|
| `upstream-cuda` | universal | All CUDA GPUs | PTX fallback, covers everything |
| `upstream-cuda-sm80` | sm_80 | A100, A30 | Datacenter Ampere |
| `upstream-cuda-sm86` | sm_86 | RTX 30xx, A10 | Consumer Ampere |
| `upstream-cuda-sm89` | sm_89 | RTX 40xx, L4, L40S | Ada Lovelace |
| `upstream-cuda-sm90` | sm_90 | H100, H200 | Hopper |

### Implementation

#### 1. Modify `upstream-cuda/build.sh`

Remove explicit `CMAKE_CUDA_ARCHITECTURES` to use llama.cpp's universal defaults:

```bash
# Before
cmake .. -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="89;90" -DCMAKE_BUILD_TYPE=Release -G Ninja

# After
cmake .. -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release -G Ninja
```

Update METADATA:
```bash
# METADATA
# name=llama.cpp upstream CUDA (universal)
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=cuda
# arch=x86_64
# capabilities=chat,embed,flash-attn
```

#### 2. Create 4 new target directories

Each directory contains a `build.sh` with METADATA header and `extra_cmake_flags`:

**`upstream-cuda-sm80/build.sh`**:
```bash
#!/usr/bin/env bash
# METADATA
# name=llama.cpp upstream CUDA (sm_80)
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=cuda
# arch=x86_64
# capabilities=chat,embed,flash-attn
# extra_cmake_flags=-DCMAKE_CUDA_ARCHITECTURES=80
```

Similar for sm_86, sm_89, sm_90.

#### 3. Update matrix workflow

The matrix workflow already discovers targets via METADATA headers. No changes needed — it will automatically find the 4 new targets.

#### 4. Artifact naming

Current: `llama-<sha>-1-ubuntu-cuda-x86_64.tar.gz`
New: `llama-<sha>-1-ubuntu-cuda-x86_64[-smXX].tar.gz`

The universal build keeps the original name. Per-SM builds get `-smXX` suffix.

#### 5. Manifest updates

The manifest schema already supports `gpu_target` and `extra_cmake_fields`. The `generate_manifest.py` script will automatically pick up the new targets.

### Trade-offs

| Pros | Cons |
|------|------|
| Covers 95%+ of users | 5x CI time for CUDA builds |
| Universal build covers everything | More artifacts to manage |
| Optimized binaries for common GPUs | Slightly more complex manifest |

---

## Part 2: Binary Distribution CLI (#58)

### Problem

Users have to manually figure out which binary to download for their GPU. There's no easy `curl | bash` install experience.

### What to Build

A `llamaup` shell script that:
1. Auto-detects GPU via `nvidia-smi`
2. Maps GPU compute capability to the right binary
3. Verifies SHA256 checksum
4. Installs to `~/.local/bin`

### Flow

```
User runs: curl -sSL https://heretek-ai.github.io/llama-builds/llamaup | bash

1. Fetch manifest.json from GitHub Pages
2. Detect GPU: nvidia-smi --query-gpu=compute_cap --format=csv,noheader
3. Map compute_cap to target:
   - 8.0 → upstream-cuda-sm80
   - 8.6 → upstream-cuda-sm86
   - 8.9 → upstream-cuda-sm89
   - 9.0 → upstream-cuda-sm90
   - fallback → upstream-cuda (universal)
4. Download artifact from manifest
5. Verify SHA256
6. Extract to ~/.local/bin
7. Done!
```

### Key Features

- **GPU auto-detection**: CUDA primary, ROCm fallback (`rocm-smi`), Vulkan fallback
- **Version management**: `--version b4102`, `--list`, `--dry-run`
- **SHA256 verification**: manifest already has hashes
- **Cross-platform**: Linux primary, macOS (Metal) future

### Implementation

#### 1. Create `scripts/llamaup`

```bash
#!/usr/bin/env bash
# llamaup - Binary distribution CLI for llama.cpp builds
# Usage: curl -sSL https://heretek-ai.github.io/llama-builds/llamaup | bash

set -euo pipefail

MANIFEST_URL="https://heretek-ai.github.io/llama-builds/manifest.json"
INSTALL_DIR="${HOME}/.local/bin"

# ... GPU detection, manifest parsing, download, verify, install
```

#### 2. Create `configs/gpu_map.json`

Maps compute capability to target slugs:

```json
{
  "8.0": "upstream-cuda-sm80",
  "8.6": "upstream-cuda-sm86",
  "8.9": "upstream-cuda-sm89",
  "9.0": "upstream-cuda-sm90",
  "default": "upstream-cuda"
}
```

#### 3. Publish as standalone script

The script should be:
- Self-contained (no dependencies beyond curl/bash)
- Available at a stable URL for `curl | bash` installs
- Documented in README

### Trade-offs

| Pros | Cons |
|------|------|
| #1 differentiator per issue | Requires manifest to be published |
| Simple, no binary needed | Shell script, not a proper CLI |
| Works with existing infrastructure | Limited error handling |

---

## Sequencing

1. **#64 first** — expand CUDA matrix so the CLI has binaries to distribute
2. **#58 second** — build the CLI that uses those binaries

### Milestones

| Milestone | What | Tests |
|-----------|------|-------|
| M1 | 4 new CUDA targets created | `python -m scripts.generate_manifest` produces 5 CUDA entries |
| M2 | Matrix workflow discovers all targets | CI runs 5 CUDA builds |
| M3 | `llamaup` script created | Manual test: `curl \| bash` on a CUDA machine |
| M4 | GPU auto-detection works | Test on sm_80, sm_86, sm_89, sm_90 |

---

## Success Criteria

- [ ] 5 CUDA builds in manifest (universal + 4 SM-specific)
- [ ] All 5 builds pass CI
- [ ] `llamaup` script installs correct binary for detected GPU
- [ ] SHA256 verification works
- [ ] Documentation updated

---

## Open Questions

None — design approved.

---

## References

- [llama.cpp CUDA build docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)
- [llama.cpp CMakeLists.txt CUDA architecture handling](https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-cuda/CMakeLists.txt)
- [Issue #64: Expand CUDA matrix](https://github.com/Heretek-AI/llama-builds/issues/64)
- [Issue #58: Binary distribution CLI](https://github.com/Heretek-AI/llama-builds/issues/58)
