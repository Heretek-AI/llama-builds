#!/usr/bin/env bash
# METADATA
# name=ik_llama.cpp CUDA
# description=ik_llama.cpp CUDA backend, CUDA 12.4.0 pinned (rationale: docs/fork-rationale/ik-llama-cpp-cuda.md)
# repo=ikawrakow/ik_llama.cpp
# ref=cb9147fd0d9c08a9a84eee5ac405a73f4e10e3e1
# backend=cuda
# arch=x86_64
# capabilities=chat,embed,iq_k,trellis
# build_system=cmake
# default_branch=master
# gpu_toolchain=cuda
# extra_cmake_flags=-DCMAKE_CUDA_ARCHITECTURES=89
# binary_names=llama-server,llama-cli,llama-quantize,llama-bench
# test_target=
# smoke_test=llama-cli --version
# layer=backend
# parent=ik-llama-cpp
# ci_capable=true
# ci_compile_capable=true
# ci_test_capable=false
# is_llama_cpp_fork=true
# upstream_ref=ggml-org/llama.cpp
# status=active
# skip_reason=
set -euo pipefail

# Build ik_llama.cpp with CUDA backend.
# Cross-compiles for NVIDIA GPUs — no physical GPU needed on runner.

REPO="${REPO:-ikawrakow/ik_llama.cpp}"
REF="${REF:-master}"
BACKEND="${BACKEND:-cuda}"
CUDA_ARCH="${CUDA_ARCH:-89}"

echo "Building ik_llama.cpp CUDA"
echo "  Repo: $REPO"
echo "  Ref:  $REF"
echo "  Backend: $BACKEND"
echo "  CUDA_ARCH: $CUDA_ARCH"

if [[ -z "${GITHUB_ACTIONS:-}" ]]; then
  echo "Running outside GitHub Actions — building locally..."

  BUILD_DIR=$(mktemp -d)
  trap 'rm -rf "$BUILD_DIR"' EXIT

  git clone --depth 1 "https://github.com/$REPO.git" "$BUILD_DIR/repo" 2>/dev/null \
    || git clone --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$BUILD_DIR/repo"

  cd "$BUILD_DIR/repo"
  cmake -B build \
    -DGGML_NATIVE=OFF \
    -DGGML_CUDA=ON \
    -DCMAKE_CUDA_ARCHITECTURES="$CUDA_ARCH" \
    -DCMAKE_BUILD_TYPE=Release
  cmake --build build -j"$(nproc)"

  echo "Build complete. Binaries in: $(pwd)/build"
  ls -la build/llama-server build/llama-cli 2>/dev/null || echo "Note: binary names may vary"
else
  echo "Running in GitHub Actions — use the build-llama composite action."
fi
