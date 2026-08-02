#!/usr/bin/env bash
# METADATA
# name=Target name
# repo=owner/repo
# ref=<pinned-sha-or-tag>
# backend=cpu|cuda|rocm|vulkan|docs
# arch=x86_64|aarch64
# capabilities=chat,embed
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
# Build steps go below this comment.

echo "TODO: Implement build for this target"
exit 1
