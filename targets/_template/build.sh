#!/usr/bin/env bash
# METADATA
# name=Target name
# repo=owner/repo
# ref=<pinned-sha-or-tag>
# backend=cpu|cuda|rocm|vulkan|docs
# arch=x86_64|aarch64
# gpu_target=<gpu-isa-or-empty>
# capabilities=chat,embed
# --- v3 fields (all optional, shown with defaults) ---
# default_branch=main|master
# gpu_toolchain=cuda|hip|metal|vulkan|none
# extra_cmake_flags=
# build_system=cmake|make|cibuildwheel|cython|go|dotnet|colcon|dfx|oci|docs
# binary_names=llama-server,llama-cli
# test_target=
# layer=base|backend|variant|docs
# parent=
# ci_capable=true
# ci_compile_capable=true
# ci_test_capable=false
# is_llama_cpp_fork=true
# smoke_test=
# upstream_ref=
# status=active|skipped|deprecated|archived
# skip_reason=
# repos=
set -euo pipefail

# Template build script for llama-builds targets.
# Copy this directory and fill in the METADATA block above.
#
# The METADATA header is scraped by scripts/generate_manifest.py
# to produce manifest.json. Required fields:
#   name     - Human-readable target name
#   repo     - GitHub owner/repo to track
#   ref      - Pinned git SHA or tag (min 7 chars)
#   backend  - One of: cpu, cuda, rocm, vulkan, docs
#   arch     - One of: x86_64, aarch64
#   capabilities - Comma-separated capability tags
#
# Optional v3 fields (with defaults):
#   default_branch  - main or master (default: main)
#   gpu_toolchain   - GPU toolchain (default: none)
#   extra_cmake_flags - Extra CMake flags (default: empty)
#   build_system    - Build system type (default: cmake)
#   binary_names    - Comma-separated binary names (default: llama-server,llama-cli)
#   test_target     - Test target name (default: empty)
#   layer           - Build layer (default: base)
#   parent          - Parent target slug (default: none)
#   ci_capable      - Can run in CI (default: true)
#   ci_compile_capable - Can compile in CI (default: true)
#   ci_test_capable - Can run tests in CI (default: false)
#   is_llama_cpp_fork - Is llama.cpp fork (default: true)
#   smoke_test      - Smoke test command (default: empty)
#   upstream_ref    - Upstream ref SHA (default: none)
#   status          - Lifecycle status (default: active)
#   skip_reason     - Reason for skipping (default: none)
#   repos           - Additional repos (default: empty)
#
# Build steps go below this comment.

echo "TODO: Implement build for this target"
exit 1
