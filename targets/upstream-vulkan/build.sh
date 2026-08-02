#!/usr/bin/env bash
# METADATA
# name=llama.cpp upstream Vulkan
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=vulkan
# arch=x86_64
# capabilities=chat,embed
set -euo pipefail

# Build llama.cpp with Vulkan backend from upstream.
# The actual build logic is in the composite action (action.yml).
# This script exists for:
#   1. Manifest generation (METADATA header)
#   2. Local development and testing

REPO="${REPO:-ggml-org/llama.cpp}"
REF="${REF:-main}"

echo "Building llama.cpp with Vulkan backend"
echo "  Repo: $REPO"
echo "  Ref:  $REF"
echo "  Backend: vulkan"
echo "  Arch: x86_64"

# For local builds (not in CI), clone and build manually
if [[ -z "${GITHUB_ACTIONS:-}" ]]; then
  echo "Running outside GitHub Actions — building locally..."

  BUILD_DIR=$(mktemp -d)
  trap 'rm -rf "$BUILD_DIR"' EXIT

  # Install Vulkan SDK dependencies
  echo "Installing Vulkan SDK dependencies..."
  sudo apt-get update -qq
  sudo apt-get install -y libvulkan-dev vulkan-validationlayers

  git clone --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$BUILD_DIR/repo" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$REPO.git" "$BUILD_DIR/repo"

  cd "$BUILD_DIR/repo"
  mkdir -p build && cd build
  cmake .. -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON -G Ninja
  cmake --build . -j$(nproc)

  echo "Build complete. Binaries in: $(pwd)"
  ls -la llama-server llama-cli 2>/dev/null || echo "Note: binary names may vary"
else
  echo "Running in GitHub Actions — use the build-llama composite action."
  echo "See: https://github.com/Heretek-AI/llama-builds/actions"
fi
