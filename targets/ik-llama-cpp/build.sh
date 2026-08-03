#!/usr/bin/env bash
# METADATA
# name=ik_llama.cpp (SOTA IQ*K quants)
# repo=ikawrakow/ik_llama.cpp
# ref=cb9147fd0d9c08a9a84eee5ac405a73f4e10e3e1
# backend=cpu
# arch=x86_64
# capabilities=chat,embed,iq_k,trellis
# build_system=cmake
# default_branch=master
# gpu_toolchain=none
# extra_cmake_flags=
# binary_names=llama-server,llama-cli,llama-quantize,llama-bench
# test_target=
# smoke_test=llama-cli --model tests/fixtures/iqk-test-model.iq4.gguf --prompt test --n-predict 1
# layer=base
# parent=
# ci_capable=true
# ci_compile_capable=true
# ci_test_capable=true
# is_llama_cpp_fork=true
# upstream_ref=ggml-org/llama.cpp
# status=active
# skip_reason=
# drift_risk=high
# drift_risk_note=Last upstream sync Aug 2024
set -euo pipefail

# Build ik_llama.cpp CPU baseline.
# SOTA custom quantization types (IQ*K, Trellis IQ*KT, IQ*KL).
# All additions are compile-time via standard GGML options.

REPO="${REPO:-ikawrakow/ik_llama.cpp}"
REF="${REF:-master}"
BACKEND="${BACKEND:-cpu}"

echo "Building ik_llama.cpp CPU baseline"
echo "  Repo: $REPO"
echo "  Ref:  $REF"
echo "  Backend: $BACKEND"

if [[ -z "${GITHUB_ACTIONS:-}" ]]; then
  echo "Running outside GitHub Actions — building locally..."

  BUILD_DIR=$(mktemp -d)
  trap 'rm -rf "$BUILD_DIR"' EXIT

  git clone --depth 1 "https://github.com/$REPO.git" "$BUILD_DIR/repo" 2>/dev/null \
    || git clone --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$BUILD_DIR/repo"

  cd "$BUILD_DIR/repo"
  cmake -B build -DGGML_NATIVE=ON -DCMAKE_BUILD_TYPE=Release
  cmake --build build -j"$(nproc)"

  echo "Build complete. Binaries in: $(pwd)/build"
  ls -la build/llama-server build/llama-cli 2>/dev/null || echo "Note: binary names may vary"
else
  echo "Running in GitHub Actions — use the build-llama composite action."
fi
