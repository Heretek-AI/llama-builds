#!/usr/bin/env bash
# scripts/check_cuda_version.sh
# Fail loudly if the installed nvcc does not match the expected CUDA version.
# Usage: check_cuda_version.sh <expected_version> [nvcc_binary]
#
# Exit codes:
#   0  - version matches (or nvcc absent; warning only)
#   1  - version mismatch
#   2  - bad invocation
#
# Example:
#   bash scripts/check_cuda_version.sh 12.4.0
#   CUDA_VERSION=12.4.0 bash scripts/check_cuda_version.sh "$CUDA_VERSION" /usr/local/cuda/bin/nvcc

set -euo pipefail

EXPECTED="${1:-${CUDA_VERSION:-}}"
NVCC_BIN="${2:-${NVCC:-nvcc}}"

if [[ -z "$EXPECTED" ]]; then
  echo "Usage: $0 <expected_version> [nvcc_binary]" >&2
  echo "   or: CUDA_VERSION=<ver> $0" >&2
  exit 2
fi

if [[ ! -x "$NVCC_BIN" ]] && ! command -v "$NVCC_BIN" >/dev/null 2>&1; then
  echo "::warning::$NVCC_BIN not found; skipping CUDA version check" >&2
  exit 0
fi

# nvcc --version prints e.g.:
#   nvcc: NVIDIA (R) Cuda compiler driver
#   Copyright (c) 2005-2024 NVIDIA Corporation
#   Built on ___
#   Cuda compilation tools, release 12.4, V12.4.131
#   Build cuda_12.4.r12.4/compiler.34000000_0
# Extract the release version (X.Y) and compare against the expected X.Y[.Z].
RELEASE_LINE="$("$NVCC_BIN" --version | grep -E 'release [0-9]+(\.[0-9]+)+' || true)"
if [[ -z "$RELEASE_LINE" ]]; then
  echo "::warning::Could not parse CUDA version from nvcc output; skipping" >&2
  exit 0
fi

INSTALLED_FULL="$(echo "$RELEASE_LINE" | awk -F'release ' '/release/ {print $2; exit}' | awk -F',' '{print $1}')"
# Trim X.Y.Z down to X.Y for tolerant comparison; the test compares full strings.
INSTALLED_MAJOR_MINOR="$(echo "$INSTALLED_FULL" | awk -F. '{print $1"."$2}')"
EXPECTED_MAJOR_MINOR="$(echo "$EXPECTED" | awk -F. '{print $1"."$2}')"

if [[ "$INSTALLED_MAJOR_MINOR" != "$EXPECTED_MAJOR_MINOR" ]]; then
  echo "::error::CUDA version mismatch: expected $EXPECTED (major.minor $EXPECTED_MAJOR_MINOR), found $INSTALLED_FULL" >&2
  exit 1
fi

echo "CUDA version check OK: installed $INSTALLED_FULL, expected $EXPECTED"
exit 0
