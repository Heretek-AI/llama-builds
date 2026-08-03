# Design: Fix CUDA Matrix Pipeline

**Date:** 2026-08-02
**Issue:** #64 — CUDA matrix only covers sm_89/90a
**Status:** Draft

## Problem

SM-specific CUDA targets (sm_80, sm_86, sm_89, sm_90) exist in `targets/` but CI doesn't use them correctly:

1. `matrix.yml` parses METADATA in shell but ignores `gpu_target` and `extra_cmake_flags`
2. `generate_matrix.py` handles ROCm GPU family expansion but not CUDA — CUDA targets are emitted without their `gpu_target` field
3. `metadata_parser.py`'s `parse_metadata()` doesn't return `gpu_target` or `extra_cmake_flags`
4. CMake configure in `matrix.yml` doesn't apply `extra_cmake_flags`
5. Archive naming and manifest entries omit `gpu_target`

Result: SM-specific targets build in CI without their architecture flags, producing universal binaries instead of optimized ones.

## Design

### 1. `scripts/metadata_parser.py` — expose missing fields

Add `gpu_target` and `extra_cmake_flags` to `parse_metadata()` return dict:

```python
result["gpu_target"] = typed.get("gpu_target", "")
result["extra_cmake_flags"] = typed.get("extra_cmake_flags", "")
```

These are already parsed by `metadata_common.py` (lines 152, 169) but not surfaced through the public API.

### 2. `scripts/metadata_parser.py` — add CUDA handling in `generate_matrix()`

Current logic only handles ROCm expansion. Add CUDA passthrough:

```python
else:
    entries.append(
        {
            "target": target_name,
            "backend": meta["backend"],
            "arch": meta["arch"],
            "gpu_target": meta.get("gpu_target"),         # NEW
            "extra_cmake_flags": meta.get("extra_cmake_flags", ""),  # NEW
            "repo": meta["repo"],
            "ref": meta["ref"],
            "bundle_strategy": meta["bundle_strategy"],
            "capabilities": meta["capabilities"],
        }
    )
```

No family expansion needed — each SM target already has its own `build.sh` with explicit `gpu_target` and `extra_cmake_flags`.

### 3. `.github/workflows/matrix.yml` — replace shell parsing with Python

Replace the 50+ line shell METADATA parsing block in the `discover` job with:

```yaml
- name: Discover build targets
  id: set-matrix
  run: python scripts/generate_matrix.py
```

Remove the inline shell parsing and the `Read target METADATA` step. The Python script writes `matrix.json` which the workflow already consumes.

### 4. `.github/workflows/matrix.yml` — pass through new fields in build job

**CMake configure step** — apply `extra_cmake_flags`:

```yaml
- name: CMake configure
  run: |
    CMAKE_ARGS="-DCMAKE_BUILD_TYPE=Release"
    CMAKE_ARGS="$CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=..."
    # ... existing backend flags ...
    if [[ -n "${{ matrix.extra_cmake_flags }}" ]]; then
      CMAKE_ARGS="$CMAKE_ARGS ${{ matrix.extra_cmake_flags }}"
    fi
```

**Archive naming** — include `gpu_target`:

```yaml
ARCHIVE_NAME="llama-${REF_PREFIX}-1-${OS}-${{ matrix.backend }}-${{ matrix.arch }}"
if [[ -n "${{ matrix.gpu_target }}" ]]; then
  ARCHIVE_NAME="${ARCHIVE_NAME}-${{ matrix.gpu_target }}"
fi
```

**Manifest entry** — include `gpu_target`:

```yaml
gpu_target: ${{ matrix.gpu_target || 'null' }}
```

### 5. `tests/test_metadata_parser.py` — add tests

- Test that `parse_metadata()` returns `gpu_target` for SM-specific targets
- Test that `parse_metadata()` returns `extra_cmake_flags` for SM-specific targets
- Test that `generate_matrix()` includes `gpu_target` and `extra_cmake_flags` in entries

### 6. `tests/test_cuda_targets.py` — update tests

- Verify matrix entries for SM targets include correct `gpu_target`
- Verify matrix entries for SM targets include correct `extra_cmake_flags`
- Verify the universal `upstream-cuda` target has `gpu_target=None`

## Files touched

| File | Change |
|------|--------|
| `scripts/metadata_parser.py` | Add `gpu_target`, `extra_cmake_flags` to `parse_metadata()` and `generate_matrix()` |
| `.github/workflows/matrix.yml` | Replace shell parsing with Python script, add field passthrough |
| `tests/test_metadata_parser.py` | Add tests for new matrix fields |
| `tests/test_cuda_targets.py` | Update/add tests for CUDA matrix entries |

## What stays the same

- `metadata_common.py` — already parses both fields correctly
- `generate_manifest.py` — already handles these fields via `metadata_common`
- `action.yml` — already handles `gpu_target` input
- `gpu_map.json` — no changes needed (llamaup already maps correctly)
- `targets/*/build.sh` — no changes needed (all SM targets already have correct METADATA)

## Verification

1. Run `python scripts/generate_matrix.py` — confirm output includes `gpu_target` and `extra_cmake_flags` for SM targets
2. Run `pytest tests/` — all tests pass
3. Run `python scripts/audit_matrix.py` — manifest audit passes
4. Inspect `matrix.json` — SM targets have correct fields
