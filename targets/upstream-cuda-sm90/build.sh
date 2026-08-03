#!/usr/bin/env bash
# METADATA
# name=llama.cpp upstream CUDA (sm_90)
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=cuda
# arch=x86_64
# gpu_target=sm_90
# capabilities=chat,embed,flash-attn
# extra_cmake_flags=-DCMAKE_CUDA_ARCHITECTURES=90
set -euo pipefail

# Build llama.cpp CUDA for sm_90 (H100, H200).

REPO="${REPO:-ggml-org/llama.cpp}"
REF="${REF:-main}"

echo "Building llama.cpp CUDA (sm_90)"
echo "  Repo: $REPO"
echo "  Ref:  $REF"
echo "  Backend: cuda"
echo "  Arch: x86_64"
echo "  CUDA Architectures: 90"

if [[ -z "${GITHUB_ACTIONS:-}" ]]; then
  echo "Running outside GitHub Actions — building locally..."

  BUILD_DIR=$(mktemp -d)
  trap 'rm -rf "$BUILD_DIR"' EXIT

  git clone --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$BUILD_DIR/repo" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$REPO.git" "$BUILD_DIR/repo"

  if ! command -v nvcc &> /dev/null; then
    echo "CUDA toolkit not found. Installing..."
    if [[ -f /etc/debian_version ]]; then
      sudo apt-get update && sudo apt-get install -y nvidia-cuda-toolkit ninja-build
    elif [[ -f /etc/redhat-release ]]; then
      sudo dnf install -y cuda-toolkit ninja-build
    else
      echo "ERROR: Cannot auto-install CUDA toolkit on this OS."
      exit 1
    fi
  fi

  cd "$BUILD_DIR/repo"
  mkdir -p build && cd build
  cmake .. -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=90 -DCMAKE_BUILD_TYPE=Release -G Ninja
  cmake --build . -j"$(nproc)"

  echo "Build complete. Binaries in: $(pwd)"
else
  echo "Running in GitHub Actions — use the build-llama composite action."
fi
