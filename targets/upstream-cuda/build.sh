#!/usr/bin/env bash
# METADATA
# name=llama.cpp upstream CUDA (universal)
# description=Universal PTX build for any CUDA-capable GPU (rationale: docs/fork-rationale/upstream-cuda.md)
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=cuda
# arch=x86_64
# capabilities=chat,embed,flash-attn
set -euo pipefail

# Build llama.cpp CUDA (universal) from upstream.
# Uses llama.cpp's default CUDA architectures which builds for
# all supported architectures via PTX fallback.

REPO="${REPO:-ggml-org/llama.cpp}"
REF="${REF:-main}"

echo "Building llama.cpp CUDA (universal)"
echo "  Repo: $REPO"
echo "  Ref:  $REF"
echo "  Backend: cuda"
echo "  Arch: x86_64"
echo "  CUDA Architectures: all (llama.cpp defaults)"

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
  # Use llama.cpp's universal defaults for CUDA architectures
  cmake .. -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release -G Ninja
  cmake --build . -j"$(nproc)"

  echo "Build complete. Binaries in: $(pwd)"
  ls -la llama-server llama-cli 2>/dev/null || echo "Note: binary names may vary"
else
  echo "Running in GitHub Actions — use the build-llama composite action."
  echo "See: https://github.com/Heretek-AI/llama-builds/actions"
fi
