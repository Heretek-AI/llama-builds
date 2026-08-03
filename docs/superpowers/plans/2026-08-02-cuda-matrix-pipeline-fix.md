# CUDA Matrix Pipeline Fix — Implementation Status

> **Status:** SUPERSEDED. 4 of 5 tasks already implemented in prior commits. This document now serves as the **delta plan** for the remaining work.

**Goal:** Make SM-specific CUDA targets (sm_80, sm_86, sm_89, sm_90) build with correct architecture flags in CI by fixing the matrix pipeline.

**Architecture:** Expose `gpu_target` and `extra_cmake_flags` through the Python metadata API, include them in matrix output, then replace the shell-based METADATA parsing in `matrix.yml` with a call to `generate_matrix.py`. The build job reads these fields and applies them to CMake, archive naming, and manifest entries.

## Status of original tasks

| Task | Status | Notes |
|------|--------|-------|
| **T1** Add `gpu_target`/`extra_cmake_flags` to `parse_metadata()` | ✅ Done | `scripts/metadata_parser.py:50-51` already exposes them. Test `test_parse_cuda_sm_target` passes. |
| **T2** Add fields to `generate_matrix()` else branch | ✅ Done | `scripts/metadata_parser.py:98-99` already emits them for CUDA/CPU/Vulkan entries. Tests pass. |
| **T3** Replace shell parsing in `matrix.yml` with Python | ✅ Done | `.github/workflows/matrix.yml:31` already calls `python scripts/generate_matrix.py`. CMake/manifest/archive wiring complete. |
| **T4** Add matrix entry tests | ✅ Done | `tests/test_cuda_targets.py::TestCudaMatrixEntries` added. 43 tests pass. |
| **T5** Verify and lint | ✅ Done | `ruff check` + `ruff format --check` clean. |

## Delta work (new tasks)

### Task A: Add `gpu_target`/`extra_cmake_flags` parity to ROCm branch

**File:** `scripts/metadata_parser.py:77-90` (ROCm branch in `generate_matrix()`)

**Reason:** The else branch (CUDA/CPU/Vulkan) already emits these fields. The ROCm branch did not. For schema consistency and downstream consumers (manifest, audit), both branches must emit the same shape.

**Change:** Add `gpu_target` and `extra_cmake_flags` to the ROCm entry dict.

- [x] **Step 1:** Edit ROCm branch to include `gpu_target: meta.get("gpu_target") or None` and `extra_cmake_flags: meta.get("extra_cmake_flags", "")`.
- [x] **Step 2:** Verify with `python -m scripts.generate_matrix` — ROCm entries now have both fields.
- [x] **Step 3:** All tests pass (`pytest tests/ -q` → 43 passed).

### Task B: Add CUDA matrix entry tests

**File:** `tests/test_cuda_targets.py`

**Reason:** `TestSmSpecificTargets` exercises `extract_metadata` per-target but never calls `generate_matrix()` against the real `targets/` directory. This catches integration regressions.

**Added:** `TestCudaMatrixEntries` class with 4 tests:
- `test_sm89_matrix_entry_has_gpu_target` — verifies SM89 entry has `gpu_target=sm_89`
- `test_sm89_matrix_entry_has_cmake_flags` — verifies `CMAKE_CUDA_ARCHITECTURES=89` in flags
- `test_universal_cuda_no_gpu_target` — universal CUDA has `gpu_target=None`
- `test_all_sm_targets_present_in_matrix` — all 4 SM targets in matrix output

## Verification

```bash
$ pytest tests/ -q
43 passed in 0.04s

$ ruff check scripts/metadata_parser.py tests/test_cuda_targets.py tests/test_metadata_parser.py
All checks passed!

$ ruff format --check scripts/metadata_parser.py tests/test_cuda_targets.py tests/test_metadata_parser.py
3 files already formatted

$ python -m scripts.generate_matrix
# Generated matrix.json with 24 entries; ROCm + CUDA + CPU + Vulkan all emit gpu_target/extra_cmake_flags
```

## Notes on plan accuracy

The original plan was written before several refactors landed. Key drift:
- Plan T3 referenced "shell-based METADATA parsing (lines 22-113)" and a "Read target METADATA" step (lines 125-163) — neither exists in current `matrix.yml`. The workflow was already Python-based.
- Plan T1 line numbers were off by 1 (target said line 49, actual was 50-51).
- Plan T3 Step 4 had two alternatives; the second (jq-based `if . == "" then null else . end`) is what was implemented.

## Reference

- Plan original: this file (superseded body)
- Manifest schema: `schemas/manifest.schema.json`
- Source of truth for METADATA parsing: `scripts/metadata_common.py`
- Public API: `scripts/metadata_parser.py`
