#!/usr/bin/env bash
# METADATA
# name=llama.cpp upstream ROCm baseline
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=rocm
# arch=x86_64
# gpu_targets=gfx110X,gfx1151,gfx1150,gfx120X,gfx103X,gfx90a,gfx908
# capabilities=chat,embed
# runtime_deps=librocblas,libhipblas,libamdhip64,librocsolver,libroctx64
# bundle_strategy=rocm-therock
set -euo pipefail

REPO="${REPO:-ggml-org/llama.cpp}"
REF="${REF:-main}"

echo "Building llama.cpp ROCm baseline"
echo "  Repo: $REPO"
echo "  Ref:  $REF"
echo "  Backend: rocm"
echo "  Arch: x86_64"

if [[ -z "${GITHUB_ACTIONS:-}" ]]; then
  echo "Running outside GitHub Actions — building locally..."

  BUILD_DIR=$(mktemp -d)
  trap 'rm -rf "$BUILD_DIR"' EXIT

  git clone --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$BUILD_DIR/repo" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$REPO.git" "$BUILD_DIR/repo"

  cd "$BUILD_DIR/repo"
  mkdir -p build && cd build
  cmake .. -DCMAKE_BUILD_TYPE=Release -DGGML_HIP=ON -G Ninja
  cmake --build . -j$(nproc)

  echo "Build complete. Binaries in: $(pwd)"
  ls -la llama-server llama-cli 2>/dev/null || echo "Note: binary names may vary"
else
  echo "Running in GitHub Actions — use the build-llama composite action."
fi
