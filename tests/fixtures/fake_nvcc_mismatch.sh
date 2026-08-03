#!/usr/bin/env bash
# Helper test fixture: fakes nvcc --version output, always reporting 12.9.x.
# Used by tests/test_cuda_pin.py::TestCudaVersionCheckScript::test_script_fails_on_mismatch
# to exercise the mismatch-detection branch without real CUDA.
set -euo pipefail
cat <<'EOF'
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2024 NVIDIA Corporation
Built on stub_fixture
Cuda compilation tools, release 12.9, V12.9.131
Build cuda_12.9.0/compiler.00000000_0
EOF
