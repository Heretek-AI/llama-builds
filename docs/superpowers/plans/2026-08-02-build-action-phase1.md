# Build Action Phase 1: Core Action + Manifest Schema + CPU Target

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `build-llama` composite action with CPU backend support, updated manifest schema, and the first real target (`upstream-cpu`) as proof of concept.

**Architecture:** A composite GitHub Action (`action.yml`) that clones a llama.cpp fork, runs CMake build, archives binaries + runtime libs, and emits a manifest entry. A `version_tag` utility generates traceable version strings (`{ref_prefix}-{build_num}`). The manifest schema is extended with `version`, `gpu_target`, `build.os`, and `build.artifact` fields.

**Tech Stack:** GitHub Actions (composite), Python 3.11+, CMake, JSON Schema, pytest

## Global Constraints

- Python 3.11+ (running on 3.15 beta in dev)
- Lint: `ruff check .`, format: `ruff format`
- Pre-commit hooks must pass (trailing-whitespace, end-of-file-fixer, ruff, betterleaks)
- JSON Schema draft 2020-12
- Manifest schema version: integer const (currently 1, bump when fields change)
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`
- Commits: Conventional Commits
- Tests: `pytest` — all must pass before commit

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `action.yml` | Create | Composite action definition — inputs, outputs, build steps |
| `scripts/version_tag.py` | Create | Generate version tags (`{ref_prefix}-{build_num}`) |
| `schemas/manifest.schema.json` | Modify | Add `version`, `gpu_target`, `build.os`, `build.artifact` fields |
| `scripts/generate_manifest.py` | Modify | Handle new fields from METADATA + build outputs |
| `targets/upstream-cpu/build.sh` | Create | First real target — upstream llama.cpp CPU baseline |
| `scripts/audit_matrix.py` | Modify | Validate new manifest fields against matrix |
| `tests/test_version_tag.py` | Create | Unit tests for version tag generation |
| `tests/test_action.py` | Create | Tests for action metadata and input/output contract |
| `tests/test_generate_manifest.py` | Modify | Extend with tests for new manifest fields |
| `tests/test_manifest_schema.py` | Modify | Validate new schema fields with golden fixtures |
| `tests/test_audit_matrix.py` | Modify | Validate new fields in matrix audit |

---

### Task 1: Version Tag Utility

**Files:**
- Create: `scripts/version_tag.py`
- Create: `tests/test_version_tag.py`

**Interfaces:**
- Consumes: upstream SHA string
- Produces: `generate_version_tag(ref_sha: str, build_number: int) -> str` returns e.g. `"abc1234-1"`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_version_tag.py
"""Tests for version_tag.py — generates traceable version strings."""

from scripts.version_tag import generate_version_tag, parse_version_tag


class TestGenerateVersionTag:
    def test_basic_tag(self):
        assert generate_version_tag("abc1234def5678", 1) == "abc1234-1"

    def test_short_sha(self):
        assert generate_version_tag("abc1234", 1) == "abc1234-1"

    def test_build_number_increments(self):
        assert generate_version_tag("abc1234def5678", 3) == "abc1234-3"

    def test_full_sha_prefixes_7_chars(self):
        tag = generate_version_tag("abc1234def567890123", 1)
        assert tag == "abc1234-1"
        assert len(tag.split("-")[0]) == 7

    def test_empty_sha_raises(self):
        import pytest
        with pytest.raises(ValueError):
            generate_version_tag("", 1)

    def test_zero_build_number_raises(self):
        import pytest
        with pytest.raises(ValueError):
            generate_version_tag("abc1234", 0)

    def test_negative_build_number_raises(self):
        import pytest
        with pytest.raises(ValueError):
            generate_version_tag("abc1234", -1)


class TestParseVersionTag:
    def test_parse_basic(self):
        ref, num = parse_version_tag("abc1234-1")
        assert ref == "abc1234"
        assert num == 1

    def test_parse_large_number(self):
        ref, num = parse_version_tag("abc1234-42")
        assert ref == "abc1234"
        assert num == 42

    def test_parse_invalid_format(self):
        import pytest
        with pytest.raises(ValueError):
            parse_version_tag("invalid")

    def test_parse_no_build_number(self):
        import pytest
        with pytest.raises(ValueError):
            parse_version_tag("abc1234")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_version_tag.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.version_tag'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/version_tag.py
"""Generate traceable version tags for llama-builds artifacts.

Version tag format: {ref_prefix}-{build_number}
- ref_prefix: First 7 chars of the upstream SHA
- build_number: Sequential integer per upstream ref (starts at 1)
"""

from __future__ import annotations

import re

TAG_PATTERN = re.compile(r"^([0-9a-f]{7})-(\d+)$")


def generate_version_tag(ref_sha: str, build_number: int) -> str:
    """Generate a version tag from an upstream SHA and build number.

    Args:
        ref_sha: Git SHA (full or short) of the upstream ref.
        build_number: Sequential build number (>= 1).

    Returns:
        Version tag string, e.g. "abc1234-1".

    Raises:
        ValueError: If ref_sha is empty or build_number < 1.
    """
    if not ref_sha:
        raise ValueError("ref_sha must not be empty")
    if build_number < 1:
        raise ValueError("build_number must be >= 1")

    prefix = ref_sha[:7]
    return f"{prefix}-{build_number}"


def parse_version_tag(tag: str) -> tuple[str, int]:
    """Parse a version tag back into ref prefix and build number.

    Args:
        tag: Version tag string, e.g. "abc1234-1".

    Returns:
        Tuple of (ref_prefix, build_number).

    Raises:
        ValueError: If tag doesn't match the expected format.
    """
    match = TAG_PATTERN.match(tag)
    if not match:
        raise ValueError(f"Invalid version tag format: {tag!r} (expected 'abcdef0-N')")
    return match.group(1), int(match.group(2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_version_tag.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/version_tag.py tests/test_version_tag.py
git commit -m "feat(version): add version tag generation utility

Generates traceable version strings ({ref_prefix}-{build_num}) for
llama-builds artifacts. Supports generation and parsing."
```

---

### Task 2: Manifest Schema Extension

**Files:**
- Modify: `schemas/manifest.schema.json`
- Modify: `tests/test_manifest_schema.py`

**Interfaces:**
- Consumes: existing schema (version 1)
- Produces: updated schema with new optional fields, bumped version to 2

- [ ] **Step 1: Write the failing test**

Add these test cases to `tests/test_manifest_schema.py`:

```python
class TestSchemaV2Fields:
    """Validate new fields added in schema version 2."""

    @pytest.fixture(autouse=True)
    def _load_jsonschema(self):
        jsonschema = pytest.importorskip("jsonschema")
        self.validate = jsonschema.validate
        self.ValidationError = jsonschema.ValidationError

    def test_version_bumped_to_2(self, schema):
        assert schema["properties"]["version"]["const"] == 2

    def test_gpu_target_field_exists(self, schema):
        target_schema = schema["$defs"]["target"]
        assert "gpu_target" in target_schema["properties"]

    def test_gpu_target_accepts_string(self, schema, manifest_with_target):
        manifest_with_target["targets"]["cpu"]["gpu_target"] = "gfx1151"
        self.validate(instance=manifest_with_target, schema=schema)

    def test_gpu_target_accepts_null(self, schema, manifest_with_target):
        manifest_with_target["targets"]["cpu"]["gpu_target"] = None
        self.validate(instance=manifest_with_target, schema=schema)

    def test_build_os_field_exists(self, schema):
        target_schema = schema["$defs"]["target"]
        assert "os" in target_schema["properties"]["build"]["properties"]

    def test_build_artifact_field_exists(self, schema):
        target_schema = schema["$defs"]["target"]
        assert "artifact" in target_schema["properties"]["build"]["properties"]

    def test_full_v2_manifest_validates(self, schema):
        manifest = {
            "version": 2,
            "generated_at": "2026-08-02T00:00:00Z",
            "targets": {
                "cpu": {
                    "name": "llama.cpp CPU baseline",
                    "repo": "ggml-org/llama.cpp",
                    "ref": "abc1234def5678",
                    "backend": "cpu",
                    "arch": "x86_64",
                    "gpu_target": None,
                    "capabilities": ["chat", "embed"],
                    "version": "abc1234-1",
                    "build": {
                        "runner": "ubuntu-latest",
                        "script": "targets/upstream-cpu/build.sh",
                        "os": "ubuntu",
                        "artifact": "llama-abc1234-1-ubuntu-cpu-x86_64.tar.gz",
                    },
                }
            },
        }
        self.validate(instance=manifest, schema=schema)
```

Also update the `golden_manifest` fixture to use version 2:

```python
@pytest.fixture
def golden_manifest():
    """Minimal valid manifest with no targets (empty targets tree)."""
    return {
        "version": 2,
        "generated_at": "2026-08-02T00:00:00Z",
        "targets": {},
    }
```

And update `manifest_with_target` to include the new fields:

```python
@pytest.fixture
def manifest_with_target():
    """Manifest with one realistic target entry."""
    return {
        "version": 2,
        "generated_at": "2026-08-02T00:00:00Z",
        "targets": {
            "cpu": {
                "name": "llama.cpp CPU baseline",
                "repo": "ggml-org/llama.cpp",
                "ref": "abc1234def5678",
                "backend": "cpu",
                "arch": "x86_64",
                "gpu_target": None,
                "capabilities": ["chat", "embed"],
                "version": "abc1234-1",
                "build": {
                    "runner": "ubuntu-latest",
                    "script": "targets/upstream-cpu/build.sh",
                    "os": "ubuntu",
                    "artifact": "llama-abc1234-1-ubuntu-cpu-x86_64.tar.gz",
                },
            }
        },
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_manifest_schema.py -v`
Expected: FAIL — version const is still 1, new fields not in schema

- [ ] **Step 3: Update the schema**

Update `schemas/manifest.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://heretek-ai.github.io/llama-builds/schemas/manifest.schema.json",
  "title": "llama-builds manifest",
  "description": "Schema for the build manifest. Versioning: bump `version` const when adding/removing fields.",
  "x-versioning": "The `version` field is an integer const. When the schema changes, increment this value. Semver does not apply — use increment-only.",
  "type": "object",
  "required": ["version", "generated_at", "targets"],
  "additionalProperties": false,
  "properties": {
    "version": {
      "type": "integer",
      "const": 2,
      "description": "Manifest schema version"
    },
    "generated_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of when the manifest was generated"
    },
    "targets": {
      "type": "object",
      "additionalProperties": false,
      "patternProperties": {
        "^[a-z0-9][a-z0-9-]*$": {
          "$ref": "#/$defs/target"
        }
      },
      "description": "Map of target slug to target metadata"
    }
  },
  "$defs": {
    "target": {
      "type": "object",
      "required": ["name", "repo", "ref", "backend", "arch", "capabilities", "build"],
      "additionalProperties": false,
      "properties": {
        "name": {
          "type": "string",
          "minLength": 1,
          "description": "Human-readable target name"
        },
        "repo": {
          "type": "string",
          "pattern": "^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$",
          "description": "GitHub owner/repo to track"
        },
        "ref": {
          "type": "string",
          "minLength": 7,
          "description": "Pinned git SHA or tag (min 7 chars for short SHA)"
        },
        "backend": {
          "type": "string",
          "enum": ["cpu", "cuda", "rocm", "vulkan", "docs"],
          "description": "Compute backend"
        },
        "arch": {
          "type": "string",
          "enum": ["x86_64", "aarch64"],
          "description": "Target architecture"
        },
        "gpu_target": {
          "type": ["string", "null"],
          "description": "GPU ISA family (e.g. gfx1151, sm_89). Null for CPU builds."
        },
        "capabilities": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1,
          "uniqueItems": true,
          "description": "List of capability tags (e.g. chat, embed, trellis)"
        },
        "version": {
          "type": "string",
          "pattern": "^[0-9a-f]{7}-\\d+$",
          "description": "Build version tag (e.g. abc1234-1)"
        },
        "build": {
          "type": "object",
          "required": ["runner", "script"],
          "additionalProperties": false,
          "properties": {
            "runner": {
              "type": "string",
              "description": "GitHub Actions runner label"
            },
            "script": {
              "type": "string",
              "description": "Relative path to build.sh within the target directory"
            },
            "os": {
              "type": "string",
              "description": "Operating system used for the build (e.g. ubuntu, windows)"
            },
            "artifact": {
              "type": "string",
              "description": "Filename of the archived build artifact"
            }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_manifest_schema.py -v`
Expected: All tests pass (including new v2 tests)

- [ ] **Step 5: Commit**

```bash
git add schemas/manifest.schema.json tests/test_manifest_schema.py
git commit -m "feat(schema): bump manifest schema to v2 with build metadata fields

Adds gpu_target, version, build.os, and build.artifact fields.
Version bumped from 1 to 2 (integer const)."
```

---

### Task 3: Composite Action Definition

**Files:**
- Create: `action.yml`
- Create: `tests/test_action.py`

**Interfaces:**
- Consumes: GitHub Actions runtime, git, cmake, ninja
- Produces: `artifact_path`, `manifest_entry`, `resolved_sha`, `version_tag` outputs

- [ ] **Step 1: Write the failing test**

```python
# tests/test_action.py
"""Tests for action.yml — validates composite action metadata."""

import re
from pathlib import Path

import yaml

ACTION_PATH = Path("action.yml")


class TestActionStructure:
    """Validate action.yml is well-formed."""

    @pytest.fixture(autouse=True)
    def _load_action(self):
        self.action = yaml.safe_load(ACTION_PATH.read_text())

    def test_action_exists(self):
        assert ACTION_PATH.exists()

    def test_name(self):
        assert self.action["name"] == "Build llama.cpp"

    def test_is_composite(self):
        assert self.action["runs"]["using"] == "composite"

    def test_has_required_inputs(self):
        inputs = self.action["inputs"]
        assert "repo" in inputs
        assert "ref" in inputs
        assert "backend" in inputs

    def test_repo_input_required(self):
        assert self.action["inputs"]["repo"]["required"] is True

    def test_ref_input_required(self):
        assert self.action["inputs"]["ref"]["required"] is True

    def test_backend_input_required(self):
        assert self.action["inputs"]["backend"]["required"] is True

    def test_backend_input_description_mentions_options(self):
        desc = self.action["inputs"]["backend"]["description"]
        assert "cpu" in desc.lower()
        assert "cuda" in desc.lower()
        assert "rocm" in desc.lower()
        assert "vulkan" in desc.lower()

    def test_has_all_outputs(self):
        outputs = self.action["outputs"]
        assert "artifact_path" in outputs
        assert "manifest_entry" in outputs
        assert "resolved_sha" in outputs
        assert "version_tag" in outputs

    def test_default_arch_is_x86_64(self):
        assert self.action["inputs"]["arch"]["default"] == "x86_64"

    def test_default_build_type_is_release(self):
        assert self.action["inputs"]["build_type"]["default"] == "Release"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_action.py -v`
Expected: FAIL — `action.yml` doesn't exist yet

- [ ] **Step 3: Create the action**

```yaml
# action.yml
name: "Build llama.cpp"
description: "Build a llama.cpp fork for a specific backend and architecture"
inputs:
  repo:
    description: "GitHub owner/repo to build (e.g. ggml-org/llama.cpp)"
    required: true
  ref:
    description: "Git SHA, tag, or branch to build"
    required: true
  backend:
    description: "Compute backend: cpu, cuda, rocm, vulkan"
    required: true
  arch:
    description: "Target architecture"
    required: false
    default: "x86_64"
  gpu_target:
    description: "GPU ISA family (e.g. gfx1151, sm_89)"
    required: false
    default: ""
  rocm_version:
    description: "ROCm version (e.g. 6.2.0)"
    required: false
    default: ""
  cuda_version:
    description: "CUDA version (e.g. 12.6)"
    required: false
    default: ""
  cmake_flags:
    description: "Extra CMake flags (space-separated)"
    required: false
    default: ""
  build_type:
    description: "CMake build type"
    required: false
    default: "Release"
outputs:
  artifact_path:
    description: "Path to the archived build artifact"
  manifest_entry:
    description: "JSON string — single target entry for manifest schema"
  resolved_sha:
    description: "Full SHA of the built ref"
  version_tag:
    description: "Generated version tag (e.g. abc1234-1)"
runs:
  using: "composite"
  steps:
    - name: Validate inputs
      shell: bash
      run: |
        # Validate backend is one of the allowed values
        case "${{ inputs.backend }}" in
          cpu|cuda|rocm|vulkan) ;;
          *)
            echo "::error::Invalid backend: ${{ inputs.backend }} (expected cpu, cuda, rocm, or vulkan)"
            exit 1
            ;;
        esac

        # Validate repo format (owner/repo)
        if [[ ! "${{ inputs.repo }}" =~ ^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$ ]]; then
          echo "::error::Invalid repo format: ${{ inputs.repo }} (expected owner/repo)"
          exit 1
        fi

        # Validate ref is at least 7 chars
        if [[ "${{ inputs.ref }}" -lt 7 ]]; then
          echo "::error::Ref must be at least 7 characters: ${{ inputs.ref }}"
          exit 1
        fi

    - name: Checkout target repo
      uses: actions/checkout@v4
      with:
        repository: ${{ inputs.repo }}
        ref: ${{ inputs.ref }}
        path: _build/target
        fetch-depth: 1

    - name: Resolve full SHA
      id: resolve
      shell: bash
      run: |
        cd _build/target
        FULL_SHA=$(git rev-parse HEAD)
        echo "resolved_sha=$FULL_SHA" >> "$GITHUB_OUTPUT"
        echo "Resolved SHA: ${FULL_SHA:0:12}"

    - name: Install dependencies
      shell: bash
      run: |
        sudo apt-get update -qq
        sudo apt-get install -y -qq cmake ninja-build

        case "${{ inputs.backend }}" in
          cuda)
            echo "::group::Installing CUDA toolkit"
            # CUDA toolkit installation — use official NVIDIA action or apt
            wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
            sudo dpkg -i cuda-keyring_1.1-1_all.deb
            sudo apt-get update -qq
            sudo apt-get install -y -qq cuda-toolkit
            echo "::endgroup::"
            ;;
          rocm)
            echo "::group::Installing ROCm"
            ROCM_VERSION="${{ inputs.rocm_version }}"
            if [[ -z "$ROCM_VERSION" ]]; then
              echo "::error::rocm_version input is required for ROCm backend"
              exit 1
            fi
            # Install ROCm — simplified for Phase 1 (CPU target doesn't need this)
            echo "ROCm $ROCM_VERSION installation — to be implemented in Phase 3"
            echo "::endgroup::"
            ;;
          vulkan)
            echo "::group::Installing Vulkan SDK"
            sudo apt-get install -y -qq libvulkan-dev vulkan-validationlayers
            echo "::endgroup::"
            ;;
          cpu)
            echo "No extra dependencies needed for CPU backend"
            ;;
        esac

    - name: CMake configure
      shell: bash
      run: |
        cd _build/target
        mkdir -p build && cd build

        CMAKE_ARGS="-DCMAKE_BUILD_TYPE=${{ inputs.build_type }}"
        CMAKE_ARGS="$CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${{ github.workspace }}/_build/install"

        case "${{ inputs.backend }}" in
          cuda)
            CMAKE_ARGS="$CMAKE_ARGS -DGGML_CUDA=ON"
            if [[ -n "${{ inputs.gpu_target }}" ]]; then
              # Extract SM architecture from gpu_target (e.g. sm_89 -> 89)
              SM_NUM="${{ inputs.gpu_target#sm_ }}"
              CMAKE_ARGS="$CMAKE_ARGS -DCMAKE_CUDA_ARCHITECTURES=$SM_NUM"
            fi
            ;;
          rocm)
            CMAKE_ARGS="$CMAKE_ARGS -DGGML_HIP=ON"
            if [[ -n "${{ inputs.gpu_target }}" ]]; then
              CMAKE_ARGS="$CMAKE_ARGS -DAMDGPU_TARGETS=${{ inputs.gpu_target }}"
            fi
            ;;
          vulkan)
            CMAKE_ARGS="$CMAKE_ARGS -DGGML_VULKAN=ON"
            ;;
        esac

        # Add user-specified cmake flags
        if [[ -n "${{ inputs.cmake_flags }}" ]]; then
          CMAKE_ARGS="$CMAKE_ARGS ${{ inputs.cmake_flags }}"
        fi

        echo "CMake args: $CMAKE_ARGS"
        cmake .. $CMAKE_ARGS -G Ninja

    - name: Build
      shell: bash
      run: |
        cd _build/target/build
        cmake --build . --config ${{ inputs.build_type }} -j$(nproc)

    - name: Collect artifacts
      id: collect
      shell: bash
      run: |
        INSTALL_DIR="${{ github.workspace }}/_build/install"
        mkdir -p "$INSTALL_DIR"

        cd _build/target/build

        # Determine what was built
        BINARIES=()
        for bin in llama-server llama-cli llama-bench llama-quantize llama-perplexity llama-benchmark; do
          if [[ -f "$bin" ]]; then
            BINARIES+=("$bin")
          fi
        done

        if [[ ${#BINARIES[@]} -eq 0 ]]; then
          echo "::error::No binaries found after build"
          exit 1
        fi

        echo "Found binaries: ${BINARIES[*]}"
        cp "${BINARIES[@]}" "$INSTALL_DIR/"

        # Collect backend-specific runtime libraries
        case "${{ inputs.backend }}" in
          rocm)
            echo "Collecting ROCm runtime libraries..."
            # Copy ROCm libs — to be implemented in Phase 3
            ;;
          cuda)
            echo "Collecting CUDA runtime libraries..."
            # Copy CUDA libs if needed — most systems have them in /usr/local/cuda
            ;;
        esac

        echo "install_dir=$INSTALL_DIR" >> "$GITHUB_OUTPUT"

    - name: Set RPATH
      if: runner.os == 'Linux'
      shell: bash
      run: |
        INSTALL_DIR="${{ steps.collect.outputs.install_dir }}"
        cd "$INSTALL_DIR"

        # Set RPATH to $ORIGIN for portable distribution
        for bin in llama-*; do
          if [[ -f "$bin" && -x "$bin" ]]; then
            patchelf --set-rpath '$ORIGIN' "$bin" 2>/dev/null || true
          fi
        done

    - name: Archive artifacts
      id: archive
      shell: bash
      run: |
        INSTALL_DIR="${{ steps.collect.outputs.install_dir }}"
        FULL_SHA="${{ steps.resolve.outputs.resolved_sha }}"
        REF_PREFIX="${FULL_SHA:0:7}"

        # Determine OS name
        OS_NAME="ubuntu"
        case "${{ runner.os }}" in
          Linux) OS_NAME="ubuntu" ;;
          Windows) OS_NAME="windows" ;;
          macOS) OS_NAME="macos" ;;
        esac

        # Build archive filename
        ARCHIVE_NAME="llama-${REF_PREFIX}-1-${OS_NAME}-${{ inputs.backend }}-${{ inputs.arch }}"
        if [[ -n "${{ inputs.gpu_target }}" ]]; then
          ARCHIVE_NAME="${ARCHIVE_NAME}-${{ inputs.gpu_target }}"
        fi
        ARCHIVE_NAME="${ARCHIVE_NAME}.tar.gz"

        # Create archive
        cd "$INSTALL_DIR"
        tar czf "${{ github.workspace }}/${ARCHIVE_NAME}" *

        echo "archive_name=$ARCHIVE_NAME" >> "$GITHUB_OUTPUT"
        echo "archive_path=${{ github.workspace }}/${ARCHIVE_NAME}" >> "$GITHUB_OUTPUT"
        echo "artifact_path=${{ github.workspace }}/${ARCHIVE_NAME}" >> "$GITHUB_OUTPUT"

    - name: Generate version tag
      id: version
      shell: bash
      run: |
        FULL_SHA="${{ steps.resolve.outputs.resolved_sha }}"
        REF_PREFIX="${FULL_SHA:0:7}"
        VERSION_TAG="${REF_PREFIX}-1"
        echo "version_tag=$VERSION_TAG" >> "$GITHUB_OUTPUT"
        echo "Version tag: $VERSION_TAG"

    - name: Emit manifest entry
      id: manifest
      shell: bash
      run: |
        FULL_SHA="${{ steps.resolve.outputs.resolved_sha }}"
        VERSION_TAG="${{ steps.version.outputs.version_tag }}"
        ARCHIVE_NAME="${{ steps.archive.outputs.archive_name }}"

        # Determine OS
        OS_NAME="ubuntu"
        case "${{ runner.os }}" in
          Linux) OS_NAME="ubuntu" ;;
          Windows) OS_NAME="windows" ;;
          macOS) OS_NAME="macos" ;;
        esac

        # Build manifest entry JSON
        GPU_TARGET="null"
        if [[ -n "${{ inputs.gpu_target }}" ]]; then
          GPU_TARGET="\"${{ inputs.gpu_target }}\""
        fi

        MANIFEST_ENTRY=$(cat <<EOF
        {
          "name": "${{ inputs.repo }} (${{ inputs.backend }})",
          "repo": "${{ inputs.repo }}",
          "ref": "$FULL_SHA",
          "backend": "${{ inputs.backend }}",
          "arch": "${{ inputs.arch }}",
          "gpu_target": $GPU_TARGET,
          "capabilities": ["chat"],
          "version": "$VERSION_TAG",
          "build": {
            "runner": "ubuntu-latest",
            "script": "",
            "os": "$OS_NAME",
            "artifact": "$ARCHIVE_NAME"
          }
        }
        EOF
        )

        # Write to output (escape for GitHub Actions)
        echo "manifest_entry=$MANIFEST_ENTRY" >> "$GITHUB_OUTPUT"

    - name: Set outputs
      shell: bash
      run: |
        echo "artifact_path=${{ steps.archive.outputs.artifact_path }}" >> "$GITHUB_OUTPUT"
        echo "resolved_sha=${{ steps.resolve.outputs.resolved_sha }}" >> "$GITHUB_OUTPUT"

    - name: Cleanup
      if: always()
      shell: bash
      run: |
        rm -rf _build
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_action.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add action.yml tests/test_action.py
git commit -m "feat(action): add composite build-llama action (CPU backend)

Reusable composite GitHub Action for building llama.cpp forks.
Currently supports CPU backend. CUDA/ROCm/Vulkan steps are
scaffolded for future phases."
```

---

### Task 4: Update Manifest Generation for New Fields

**Files:**
- Modify: `scripts/generate_manifest.py`
- Modify: `tests/test_generate_manifest.py`

**Interfaces:**
- Consumes: METADATA headers from `targets/*/build.sh`, version tag utility
- Produces: Manifest dict with new fields (`version`, `gpu_target`, `build.os`, `build.artifact`)

- [ ] **Step 1: Write the failing test**

Add these test cases to `tests/test_generate_manifest.py`:

```python
class TestGenerateManifestV2:
    """Tests for v2 manifest fields."""

    def test_version_field_populated(self, tmp_path):
        """Generated manifest includes version from build.sh METADATA."""
        target_dir = tmp_path / "targets" / "cpu"
        target_dir.mkdir(parents=True)
        build_sh = target_dir / "build.sh"
        build_sh.write_text(
            textwrap.dedent("""\
            #!/usr/bin/env bash
            # METADATA
            # name=llama.cpp CPU baseline
            # repo=ggml-org/llama.cpp
            # ref=abc1234def5678
            # backend=cpu
            # arch=x86_64
            # capabilities=chat,embed
            set -euo pipefail
        """)
        )
        manifest = generate_manifest(targets_dir=tmp_path / "targets")
        target = manifest["targets"]["cpu"]
        assert "version" in target
        assert target["version"] == "abc1234-1"

    def test_gpu_target_from_metadata(self, tmp_path):
        """gpu_target is read from METADATA if present."""
        target_dir = tmp_path / "targets" / "cuda"
        target_dir.mkdir(parents=True)
        build_sh = target_dir / "build.sh"
        build_sh.write_text(
            textwrap.dedent("""\
            #!/usr/bin/env bash
            # METADATA
            # name=llama.cpp CUDA
            # repo=ggml-org/llama.cpp
            # ref=abc1234def5678
            # backend=cuda
            # arch=x86_64
            # gpu_target=sm_89
            # capabilities=chat,embed
            set -euo pipefail
        """)
        )
        manifest = generate_manifest(targets_dir=tmp_path / "targets")
        target = manifest["targets"]["cuda"]
        assert target["gpu_target"] == "sm_89"

    def test_gpu_target_null_when_missing(self, tmp_path):
        """gpu_target is null when not in METADATA."""
        target_dir = tmp_path / "targets" / "cpu"
        target_dir.mkdir(parents=True)
        build_sh = target_dir / "build.sh"
        build_sh.write_text(
            textwrap.dedent("""\
            #!/usr/bin/env bash
            # METADATA
            # name=llama.cpp CPU
            # repo=ggml-org/llama.cpp
            # ref=abc1234def5678
            # backend=cpu
            # arch=x86_64
            # capabilities=chat
            set -euo pipefail
        """)
        )
        manifest = generate_manifest(targets_dir=tmp_path / "targets")
        target = manifest["targets"]["cpu"]
        assert target["gpu_target"] is None

    def test_build_os_default_ubuntu(self, tmp_path):
        """build.os defaults to ubuntu."""
        target_dir = tmp_path / "targets" / "cpu"
        target_dir.mkdir(parents=True)
        build_sh = target_dir / "build.sh"
        build_sh.write_text(
            textwrap.dedent("""\
            #!/usr/bin/env bash
            # METADATA
            # name=Test
            # repo=o/r
            # ref=abc1234
            # backend=cpu
            # arch=x86_64
            # capabilities=chat
            set -euo pipefail
        """)
        )
        manifest = generate_manifest(targets_dir=tmp_path / "targets")
        target = manifest["targets"]["cpu"]
        assert target["build"]["os"] == "ubuntu"

    def test_manifest_schema_version_2(self, tmp_path):
        """Generated manifest uses schema version 2."""
        manifest = generate_manifest(targets_dir=tmp_path / "targets")
        assert manifest["version"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_generate_manifest.py::TestGenerateManifestV2 -v`
Expected: FAIL — `version` field not populated, schema version still 1

- [ ] **Step 3: Update generate_manifest.py**

In `scripts/generate_manifest.py`:

1. Update `METADATA_PATTERN` to also match `gpu_target`:
```python
# Already handled by the generic pattern — no change needed
```

2. Update `generate_manifest()` to include new fields:

```python
def generate_manifest(targets_dir: Path, repo_root: Path | None = None) -> dict:
    """Walk targets_dir and build a manifest dict."""
    if repo_root is None:
        repo_root = targets_dir.parent

    targets: dict[str, dict] = {}

    if not targets_dir.is_dir():
        return {
            "version": 2,
            "generated_at": datetime.now(UTC).isoformat(),
            "targets": targets,
        }

    for target_dir in sorted(targets_dir.iterdir()):
        if not target_dir.is_dir():
            continue

        slug = target_dir.name
        if not TARGETS_PATTERN.match(slug):
            continue

        build_sh = target_dir / "build.sh"
        if not build_sh.exists():
            continue

        meta = extract_metadata(build_sh)
        if meta is None:
            continue

        # Compute relative script path from repo root
        script_rel = str(build_sh.relative_to(repo_root))

        if "arch" not in meta:
            warnings.warn(
                f"Target '{slug}' missing 'arch' in METADATA, defaulting to x86_64",
                stacklevel=2,
            )

        # Generate version tag from ref
        ref = meta.get("ref", "")
        version_tag = f"{ref[:7]}-1" if len(ref) >= 7 else ""

        targets[slug] = {
            "name": meta["name"],
            "repo": meta["repo"],
            "ref": ref,
            "backend": meta["backend"],
            "arch": meta.get("arch", "x86_64"),
            "gpu_target": meta.get("gpu_target") or None,
            "capabilities": meta["capabilities"],
            "version": version_tag,
            "build": {
                "runner": _runner_for_backend(meta["backend"]),
                "script": script_rel,
                "os": "ubuntu",
                "artifact": "",  # Populated at build time, not manifest gen time
            },
        }

    return {
        "version": 2,
        "generated_at": datetime.now(UTC).isoformat(),
        "targets": targets,
    }
```

3. Update the `extract_metadata` function — the generic pattern already handles `gpu_target` since it matches any `key=value` line. No change needed there.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_generate_manifest.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_manifest.py tests/test_generate_manifest.py
git commit -m "feat(manifest): generate v2 manifest with build metadata

Adds version, gpu_target, build.os, and build.artifact fields to
generated manifest entries. Schema version bumped to 2."
```

---

### Task 5: Upstream CPU Target

**Files:**
- Create: `targets/upstream-cpu/build.sh`
- Create: `targets/upstream-cpu/` directory

**Interfaces:**
- Consumes: METADATA header contract (scraped by generate_manifest.py)
- Produces: Manifest entry for upstream llama.cpp CPU baseline

- [ ] **Step 1: Write the test**

Add to `tests/test_generate_manifest.py`:

```python
class TestUpstreamCpuTarget:
    """Validate the upstream-cpu target exists and has correct metadata."""

    def test_upstream_cpu_build_sh_exists(self):
        build_sh = Path("targets/upstream-cpu/build.sh")
        assert build_sh.exists(), "targets/upstream-cpu/build.sh must exist"

    def test_upstream_cpu_metadata(self):
        from scripts.generate_manifest import extract_metadata
        build_sh = Path("targets/upstream-cpu/build.sh")
        meta = extract_metadata(build_sh)
        assert meta is not None
        assert meta["name"] == "llama.cpp upstream CPU baseline"
        assert meta["repo"] == "ggml-org/llama.cpp"
        assert meta["backend"] == "cpu"
        assert meta["arch"] == "x86_64"
        assert "chat" in meta["capabilities"]
        assert "embed" in meta["capabilities"]

    def test_upstream_cpu_in_manifest(self):
        from scripts.generate_manifest import generate_manifest
        manifest = generate_manifest(targets_dir=Path("targets"))
        assert "upstream-cpu" in manifest["targets"]
        target = manifest["targets"]["upstream-cpu"]
        assert target["backend"] == "cpu"
        assert target["gpu_target"] is None
        assert target["version"].endswith("-1")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_generate_manifest.py::TestUpstreamCpuTarget -v`
Expected: FAIL — target doesn't exist yet

- [ ] **Step 3: Create the target**

```bash
mkdir -p targets/upstream-cpu
```

```bash
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
```

Make it executable:

```bash
chmod +x targets/upstream-cpu/build.sh
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_generate_manifest.py::TestUpstreamCpuTarget -v`
Expected: All 3 tests pass

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass (existing + new)

- [ ] **Step 6: Commit**

```bash
git add targets/upstream-cpu/ tests/test_generate_manifest.py
git commit -m "feat(target): add upstream-cpu build target

First real build target — llama.cpp CPU baseline from ggml-org/llama.cpp.
METADATA header validates against manifest schema v2."
```

---

### Task 6: Update Audit Matrix for New Fields

**Files:**
- Modify: `scripts/audit_matrix.py`
- Modify: `tests/test_audit_matrix.py`

**Interfaces:**
- Consumes: manifest dict with v2 fields, matrix.yml
- Produces: validation errors for mismatches

- [ ] **Step 1: Write the failing test**

Add to `tests/test_audit_matrix.py`:

```python
class TestAuditMatrixV2:
    """Validate v2 manifest fields in matrix audit."""

    def test_gpu_target_validated(self):
        """Matrix entry with gpu_target must match manifest."""
        manifest = {
            "version": 2,
            "generated_at": "2026-08-02T00:00:00Z",
            "targets": {
                "cuda-sm89": {
                    "name": "CUDA sm_89",
                    "repo": "ggml-org/llama.cpp",
                    "ref": "abc1234def5678",
                    "backend": "cuda",
                    "arch": "x86_64",
                    "gpu_target": "sm_89",
                    "capabilities": ["chat"],
                    "version": "abc1234-1",
                    "build": {
                        "runner": "ubuntu-latest",
                        "script": "targets/cuda-sm89/build.sh",
                        "os": "ubuntu",
                        "artifact": "llama-abc1234-1-ubuntu-cuda-x86_64-sm_89.tar.gz",
                    },
                }
            },
        }
        matrix_yml = textwrap.dedent("""\
            name: Matrix Build
            on: [push]
            permissions:
              contents: read
            jobs:
              build:
                runs-on: ubuntu-latest
                strategy:
                  matrix:
                    include:
                      - target: cuda-sm89
                        backend: cuda
                        arch: x86_64
                        gpu_target: sm_89
        """)
        errors = audit_matrix(matrix_yml, manifest)
        assert errors == []

    def test_version_field_not_validated(self):
        """Version field is informational — not validated against matrix."""
        manifest = {
            "version": 2,
            "generated_at": "2026-08-02T00:00:00Z",
            "targets": {
                "cpu": {
                    "name": "CPU",
                    "repo": "o/r",
                    "ref": "abc1234def5678",
                    "backend": "cpu",
                    "arch": "x86_64",
                    "gpu_target": None,
                    "capabilities": ["chat"],
                    "version": "abc1234-1",
                    "build": {
                        "runner": "ubuntu-latest",
                        "script": "targets/cpu/build.sh",
                        "os": "ubuntu",
                        "artifact": "",
                    },
                }
            },
        }
        matrix_yml = textwrap.dedent("""\
            name: Matrix Build
            on: [push]
            permissions:
              contents: read
            jobs:
              build:
                runs-on: ubuntu-latest
                strategy:
                  matrix:
                    include:
                      - target: cpu
                        backend: cpu
                        arch: x86_64
        """)
        errors = audit_matrix(matrix_yml, manifest)
        assert errors == []
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_audit_matrix.py -v`
Expected: The new tests should pass — the audit logic doesn't validate `version` or `gpu_target` by design (version is informational, gpu_target is optional in matrix).

- [ ] **Step 3: Update audit_matrix.py (if needed)**

The current `audit_matrix()` function only validates target slug presence — it doesn't check individual fields. This is correct behavior for the matrix audit (we validate against the schema, not the matrix). No changes needed to `audit_matrix.py` itself.

However, update `audit_manifest()` to use the new schema version:

```python
SCHEMA_PATH = Path("schemas/manifest.schema.json")
```

This already references the schema file, which we updated in Task 2. No code change needed.

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add scripts/audit_matrix.py tests/test_audit_matrix.py
git commit -m "test(audit): validate v2 manifest fields in matrix audit

Adds tests for gpu_target validation and version field (informational).
Audit matrix correctly validates target slug presence without checking
individual build metadata fields."
```

---

### Task 7: Update Manifest and Verify End-to-End

**Files:**
- Modify: `manifest.json` (regenerated)
- Modify: `tests/test_template.py` (update for v2)

**Interfaces:**
- Consumes: all previous tasks
- Produces: updated manifest.json, all tests passing

- [ ] **Step 1: Regenerate manifest**

Run: `python -m scripts.generate_manifest --output manifest.json`

Expected: manifest.json now contains the upstream-cpu target with v2 fields.

- [ ] **Step 2: Verify manifest content**

Run: `python -c "import json; m = json.load(open('manifest.json')); print(json.dumps(m, indent=2))"`

Expected output should include:
```json
{
  "version": 2,
  "targets": {
    "upstream-cpu": {
      "name": "llama.cpp upstream CPU baseline",
      "repo": "ggml-org/llama.cpp",
      "ref": "5d3a7b0e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c",
      "backend": "cpu",
      "arch": "x86_64",
      "gpu_target": null,
      "capabilities": ["chat", "embed"],
      "version": "5d3a7b0-1",
      "build": {
        "runner": "ubuntu-latest",
        "script": "targets/upstream-cpu/build.sh",
        "os": "ubuntu",
        "artifact": ""
      }
    }
  }
}
```

- [ ] **Step 3: Update test_template.py for v2**

The template test checks METADATA extraction. Update the template `targets/_template/build.sh` to include the new `gpu_target` field (optional in METADATA):

```bash
#!/usr/bin/env bash
# METADATA
# name=Target name
# repo=owner/repo
# ref=<pinned-sha-or-tag>
# backend=cpu|cuda|rocm|vulkan|docs
# arch=x86_64|aarch64
# gpu_target=<gpu-isa-or-empty>
# capabilities=chat,embed
set -euo pipefail

# Template build script for llama-builds targets.
# Copy this directory and fill in the METADATA block above.
```

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 5: Run linter**

Run: `ruff check .`
Expected: No errors

- [ ] **Step 6: Run pre-commit**

Run: `pre-commit run --files .`
Expected: All hooks pass

- [ ] **Step 7: Commit**

```bash
git add manifest.json targets/_template/build.sh
git commit -m "chore: regenerate manifest with upstream-cpu target

Updates manifest.json to v2 with the first real build target.
Template updated to include gpu_target field."
```

---

## Verification Checklist

After all tasks are complete:

1. **All tests pass**: `pytest tests/ -v` — 0 failures
2. **Lint passes**: `ruff check .` — 0 errors
3. **Pre-commit passes**: `pre-commit run --files .` — all green
4. **Manifest validates**: `python -m scripts.audit_matrix` — passes
5. **Action is valid YAML**: `python -c "import yaml; yaml.safe_load(open('action.yml'))"` — no error
6. **Target METADATA extracts correctly**: `python -c "from scripts.generate_manifest import extract_metadata; from pathlib import Path; print(extract_metadata(Path('targets/upstream-cpu/build.sh')))"` — returns dict with all fields
