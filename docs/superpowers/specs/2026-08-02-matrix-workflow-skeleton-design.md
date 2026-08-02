# Matrix Workflow Skeleton

**Issue**: [#1](https://github.com/Heretek-AI/llama-builds/issues/1)
**Date**: 2026-08-02
**Status**: Draft

## Goal

Create `.github/workflows/matrix.yml` — the skeleton for llama-builds'
cross-OS / cross-arch build matrix. The skeleton demonstrates that
`pull_request` and `workflow_dispatch` triggers fire and that the job
graph dynamically discovers and expands per-target from
`targets/*/build.sh`.

## Design

### Two-job workflow

The workflow uses a **discover → build** two-job pattern, following
the same pattern proven in
[lemonade-sdk/llamacpp-rocm](https://github.com/lemonade-sdk/llamacpp-rocm/blob/main/.github/workflows/build-llamacpp-rocm.yml).

**Job 1: `discover`**

- Runs on `ubuntu-latest`.
- Globs `targets/*/build.sh` using a shell script.
- Derives matrix entries from directory names: target = dirname,
  backend = dirname, arch = `x86_64` (hardcoded default).
  Full metadata extraction from build.sh headers belongs to
  issue #3.
- Emits a JSON matrix array as a job output using the format
  `{"include": [{"target": "cuda", "backend": "cuda", ...}]}`.
- If `targets/` is empty or has no `build.sh` files, outputs
  `{"include": []}`.

**Job 2: `build`**

- Depends on `discover` via `needs: discover`.
- Consumes the matrix output from `discover` using
  `fromJson()`.
- Guard: `if: fromJson(needs.discover.outputs.matrix).include[0]`
  — only runs when the matrix is non-empty. Empty matrix → job
  skipped cleanly, no false failures.
- `fail-fast: false` in the strategy — one target failure must
  not cancel others.
- Each matrix entry runs on `ubuntu-latest` (placeholder runner;
  issue #2 will add real runner labels).
- Placeholder step echoes the matrix parameters and prints a
  "skeleton only — no build yet" message.

### Edge case handling

Borrowed from lemonade's approach to empty / conditional matrices:

- **Empty matrix**: `discover` outputs `{"include": []}`. The
  build job's `if:` guard evaluates to false. Job is skipped —
  not failed, not pending. Clean state.
- **Single target**: Works identically; `fromJson()` handles
  single-element arrays.
- **Future OS split**: When cross-OS builds land, each OS gets
  its own build job with its own `if:` guard (e.g.,
  `if: needs.discover.outputs.should_build_ubuntu == 'true'`),
  matching lemonade's windows/ubuntu split pattern.

### Triggers

```yaml
on:
  pull_request:
  workflow_dispatch:
```

No branch filter — fires on all PRs and manual dispatches.

### File location

`.github/workflows/matrix.yml`

## Acceptance criteria

- [x] `.github/workflows/matrix.yml` is committed and parses cleanly.
- [x] Triggers on `pull_request` and `workflow_dispatch`.
- [x] A placeholder job runs on `ubuntu-latest` and prints the
      target list (or skips cleanly if empty).
- [x] Dynamic discovery from `targets/*/build.sh` — no hardcoded
      matrix entries.

## Out of scope

- Real CUDA / ROCm / Vulkan matrix entries (issue #2).
- Manifest scraping (issue #3).
- Actual build steps.

## Migration path

When issue #2 adds `targets/cuda/build.sh`, `targets/rocm/build.sh`,
etc., the `discover` job will automatically pick them up. The
`build` job matrix will expand with no workflow changes.
