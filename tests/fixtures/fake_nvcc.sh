#!/usr/bin/env bash
# Helper test fixture: fakes nvcc --version output.
# Used by tests/test_cuda_pin.py to exercise scripts/check_cuda_version.sh
# without requiring an actual CUDA installation.
# Usage: fake_nvcc.sh [--version] [<X.Y[.Z]>]
# Matches real nvcc format: "release 12.4, V12.4.131".
set -euo pipefail
REPORT="12.4"
for arg in "$@"; do
  case "$arg" in
    --version|-V) ;;
    [0-9]*.[0-9]*) REPORT="$arg" ;;
  esac
done
MAJOR_MINOR="$(echo "$REPORT" | awk -F. '{print $1"."$2}')"
cat <<EOF
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2024 NVIDIA Corporation
Built on stub_fixture
Cuda compilation tools, release ${MAJOR_MINOR}, V${REPORT}.131
Build cuda_${REPORT}/compiler.00000000_0
EOF
