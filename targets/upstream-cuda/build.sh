#!/usr/bin/env bash
# METADATA
# name=llama.cpp upstream CUDA (sm_89/90a)
# repo=ggml-org/llama.cpp
# ref=5d3a7b0e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c
# backend=cuda
# arch=x86_64
# capabilities=chat,embed,flash-attn
set -euo pipefail

# Build llama.cpp CUDA (sm_89/90a) from upstream.
# The actual build logic is in the composite action (action.yml).
# This script exists for:
#   1. Manifest generation (METADATA header)
#   2. Local development and testing

REPO="${REPO:-ggml-org/llama.cpp}"
REF="${REF:-main}"

echo "Building llama.cpp CUDA (sm_89/90a)"
echo "  Repo: $REPO"
echo "  Ref:  $REF"
echo "  Backend: cuda"
echo "  Arch: x86_64"
echo "  CUDA Architectures: 89;90"

# For local builds (not in CI), clone and build manually
if [[ -z "${GITHUB_ACTIONS:-}" ]]; then
  echo "Running outside GitHub Actions — building locally..."

  BUILD_DIR=$(mktemp -d)
  trap 'rm -rf "$BUILD_DIR"' EXIT

  git clone --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$BUILD_DIR/repo" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$REPO.git" "$BUILD_DIR/repo"

  # Install CUDA toolkit if not present
  if ! command -v nvcc &> /dev/null; then
    echo "CUDA toolkit not found. Installing..."
    if [[ -f /etc/debian_version ]]; then
      sudo apt-get update && sudo apt-get install -y nvidia-cuda-toolkit ninja-build
    elif [[ -f /etc/redhat-release ]]; then
      sudo dnf install -y cuda-toolkit ninja-build
    else
      echo "ERROR: Cannot auto-install CUDA toolkit on this OS."
      echo "Please install CUDA toolkit and Ninja manually."
      exit 1
    fi
  else
    echo "CUDA toolkit found: $(nvcc --version | head -1)"
    # Still ensure ninja is available
    if ! command -v ninja &> /dev/null; then
      echo "Installing Ninja build system..."
      if [[ -f /etc/debian_version ]]; then
        sudo apt-get install -y ninja-build
      elif [[ -f /etc/redhat-release ]]; then
        sudo dnf install -y ninja-build
      fi
    fi
  fi

  cd "$BUILD_DIR/repo"
  mkdir -p build && cd build
  cmake .. -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="89;90" -DCMAKE_BUILD_TYPE=Release -G Ninja
  cmake --build . -j$(nproc)

  echo "Build complete. Binaries in: $(pwd)"
  ls -la llama-server llama-cli 2>/dev/null || echo "Note: binary names may vary"
else
  echo "Running in GitHub Actions — use the build-llama composite action."
  echo "See: https://github.com/Heretek-AI/llama-builds/actions"
fi
