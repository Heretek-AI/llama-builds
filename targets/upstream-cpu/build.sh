#!/usr/bin/env bash
# METADATA
# name=llama.cpp upstream CPU baseline
# repo=ggml-org/llama.cpp
# ref=5d3a7b0e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c
# backend=cpu
# arch=x86_64
# capabilities=chat,embed
set -euo pipefail

# Build llama.cpp CPU baseline from upstream.
# The actual build logic is in the composite action (action.yml).
# This script exists for:
#   1. Manifest generation (METADATA header)
#   2. Local development and testing

REPO="${REPO:-ggml-org/llama.cpp}"
REF="${REF:-main}"

echo "Building llama.cpp CPU baseline"
echo "  Repo: $REPO"
echo "  Ref:  $REF"
echo "  Backend: cpu"
echo "  Arch: x86_64"

# For local builds (not in CI), clone and build manually
if [[ -z "${GITHUB_ACTIONS:-}" ]]; then
  echo "Running outside GitHub Actions — building locally..."

  BUILD_DIR=$(mktemp -d)
  trap 'rm -rf "$BUILD_DIR"' EXIT

  git clone --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$BUILD_DIR/repo" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$REPO.git" "$BUILD_DIR/repo"

  cd "$BUILD_DIR/repo"
  mkdir -p build && cd build
  cmake .. -DCMAKE_BUILD_TYPE=Release -G Ninja
  cmake --build . -j$(nproc)

  echo "Build complete. Binaries in: $(pwd)"
  ls -la llama-server llama-cli 2>/dev/null || echo "Note: binary names may vary"
else
  echo "Running in GitHub Actions — use the build-llama composite action."
  echo "See: https://github.com/Heretek-AI/llama-builds/actions"
fi
