#!/usr/bin/env bash
# METADATA
# name=llama.cpp DGX Spark (deprecated)
# repo=croll83/llama.cpp-dgx
# ref=9131f2e6ec8f34a733fe9b141a2c5b07c16b7645
# backend=cuda
# arch=x86_64
# capabilities=chat,embed,dgx-spark
# build_system=cmake
# default_branch=main
# gpu_toolchain=cuda
# extra_cmake_flags=-DCMAKE_CUDA_ARCHITECTURES=90
# binary_names=llama-server,llama-cli,llama-quantize,llama-dflash,llama-dflash-server
# test_target=
# smoke_test=llama-cli --version
# layer=base
# parent=
# ci_capable=false
# ci_compile_capable=false
# ci_test_capable=false
# is_llama_cpp_fork=true
# upstream_ref=ggml-org/llama.cpp
# status=deprecated
# skip_reason=Deprecated upstream (2026-05-25), one-off verify only
set -euo pipefail

# Build llama.cpp-dgx (DFlash MTP, TurboQuant KV, NVFP4).
# DEPRECATED by maintainer — upstream now has MTP + NVFP4 natively.
# Only unique value: TurboQuant KV types (TQ3_0, TURBO2_0/3_0/4_0).

REPO="${REPO:-croll83/llama.cpp-dgx}"
REF="${REF:-main}"
BACKEND="${BACKEND:-cuda}"
CUDA_ARCH="${CUDA_ARCH:-90}"

echo "Building llama.cpp-dgx (DEPRECATED)"
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
    -DCMAKE_CUDA_ARCHITECTURES="$CUDA_ARCH-real" \
    -DCMAKE_BUILD_TYPE=Release
  cmake --build build --target llama-server llama-cli llama-quantize llama-dflash llama-dflash-server -j"$(nproc)"

  echo "Build complete. Binaries in: $(pwd)/build"
  ls -la build/llama-server build/llama-cli 2>/dev/null || echo "Note: binary names may vary"
else
  echo "Running in GitHub Actions — use the build-llama composite action."
fi
