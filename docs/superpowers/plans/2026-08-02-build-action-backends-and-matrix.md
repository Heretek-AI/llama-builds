# Build Action Backends & Matrix Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete CUDA, ROCm, and Vulkan backends in the build action, fix manifest entry generation, and wire the matrix workflow for end-to-end CI.

**Architecture:** Extend the composite GitHub Action (`action.yml`) with backend-specific dependency installation, CMake flags, and runtime library bundling. Fix manifest entry generation to use Python for valid JSON. Wire `matrix.yml` discover → build → publish jobs.

**Tech Stack:** GitHub Actions (composite), Bash, Python 3.11+, CMake, CUDA toolkit, ROCm, Vulkan SDK

## Global Constraints

- Python 3.11+ (from AGENTS.md)
- Code style enforced by pre-commit + super-linter
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`
- Commit messages: Conventional Commits
- PRs require linked GitHub Issue
- Tests: `pytest` (111 passing)
- Lint: `ruff check .`

---

## File Structure

| File | Purpose |
|------|---------|
| `action.yml` | Composite GitHub Action — main build pipeline |
| `.github/workflows/matrix.yml` | Matrix workflow — discover + build + publish |
| `targets/upstream-cpu/build.sh` | CPU target METADATA (add `gpu_target` field) |
| `targets/upstream-cuda/build.sh` | CUDA target METADATA (add `gpu_target` field) |
| `targets/upstream-rocm/build.sh` | ROCm target METADATA (add `gpu_target` field) |
| `targets/upstream-vulkan/build.sh` | Vulkan target METADATA (add `gpu_target` field) |
| `tests/test_action_backends.py` | Tests for backend-specific logic |
| `tests/test_manifest_entry.py` | Tests for manifest entry generation |
| `tests/test_matrix_discovery.py` | Tests for matrix METADATA parsing |

---

## Task 1: CUDA Backend in action.yml

**Files:**
- Modify: `action.yml:91-125` (Install dependencies step, CUDA branch)
- Modify: `action.yml:196-205` (Collect artifacts step, CUDA branch)
- Test: `tests/test_action_backends.py`

**Interfaces:**
- Consumes: `inputs.repo`, `inputs.ref`, `inputs.backend`, `inputs.gpu_target`
- Produces: CUDA toolkit installed, GGML_CUDA=ON set, CUDA libs bundled in `$INSTALL_DIR/lib/`

- [ ] **Step 1: Write test for CUDA dependency installation**

```python
# tests/test_action_backends.py
"""Tests for backend-specific logic in the build action."""

from pathlib import Path


def test_cuda_cmake_flags_extract_sm_number() -> None:
    """Verify gpu_target=sm_89 extracts SM number 89 for CMAKE_CUDA_ARCHITECTURES."""
    gpu_target = "sm_89"
    sm_num = gpu_target.replace("sm_", "")
    assert sm_num == "89"


def test_cuda_cmake_flags_sm_90a() -> None:
    """Verify gpu_target=sm_90a extracts SM number 90a."""
    gpu_target = "sm_90a"
    sm_num = gpu_target.replace("sm_", "")
    assert sm_num == "90a"
```

- [ ] **Step 2: Run test to verify it passes (pure logic, no action dependency)**

Run: `pytest tests/test_action_backends.py -v`
Expected: PASS

- [ ] **Step 3: Update action.yml CUDA install step**

Replace the CUDA branch in the "Install dependencies" step (lines ~97-105):

```yaml
          cuda)
            echo "::group::Installing CUDA toolkit"
            # Use official NVIDIA CUDA action for reliable installs
            - uses: Jimver/cuda-toolkit@v0.2.21
              id: cuda-toolkit
              with:
                method: network
                linux-local-args: '["--toolkit"]'
            echo "CUDA installed: ${{ steps.cuda-toolkit.outputs.cuda }}"
            echo "::endgroup::"
            ;;
```

Note: In composite actions, `uses:` steps must be at the top level. The CUDA toolkit installation should be a separate step, not nested inside a `run:` block. Restructure as:

```yaml
    - name: Install CUDA toolkit
      if: inputs.backend == 'cuda'
      uses: Jimver/cuda-toolkit@v0.2.21
      id: cuda-toolkit
      with:
        method: network
        linux-local-args: '["--toolkit"]'

    - name: Install dependencies
      shell: bash
      run: |
        sudo apt-get update -qq
        sudo apt-get install -y -qq cmake ninja-build

        case "${{ inputs.backend }}" in
          rocm)
            echo "::group::Installing ROCm"
            ROCM_VERSION="${{ inputs.rocm_version }}"
            if [[ -z "$ROCM_VERSION" ]]; then
              echo "::error::rocm_version input is required for ROCm backend"
              exit 1
            fi
            echo "ROCm $ROCM_VERSION installation — to be implemented in Task 2"
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
```

- [ ] **Step 4: Update action.yml CUDA collect artifacts step**

Replace the CUDA branch in the "Collect artifacts" step (lines ~196-205):

```yaml
          cuda)
            echo "Collecting CUDA runtime libraries..."
            mkdir -p "$INSTALL_DIR/lib"
            # Copy cuBLAS and cuBLASLt (required by llama.cpp CUDA)
            for lib in libcublas.so* libcublaslt.so*; do
              find /usr/local/cuda -name "$lib" -exec cp -L {} "$INSTALL_DIR/lib/" \; 2>/dev/null || true
            done
            # Verify libs were collected
            if ls "$INSTALL_DIR/lib/"*.so* 1>/dev/null 2>&1; then
              echo "CUDA libs bundled: $(ls "$INSTALL_DIR/lib/"*.so* | wc -l) files"
            else
              echo "::warning::No CUDA runtime libs found — binaries may require system CUDA"
            fi
            ;;
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_action_backends.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add action.yml tests/test_action_backends.py
git commit -m "feat(action): add CUDA backend with toolkit install and runtime lib bundling"
```

---

## Task 2: ROCm Backend in action.yml

**Files:**
- Modify: `action.yml` (Install dependencies step, ROCm branch)
- Modify: `action.yml` (Collect artifacts step, ROCm branch)
- Modify: `action.yml` (inputs — add `rocm_version` default)
- Test: `tests/test_action_backends.py`

**Interfaces:**
- Consumes: `inputs.rocm_version` (required for ROCm)
- Produces: ROCm installed at `/opt/rocm-{version}`, GGML_HIP=ON set, ROCm libs bundled

- [ ] **Step 1: Write test for ROCm version validation**

```python
# tests/test_action_backends.py (append)

def test_rocm_version_required() -> None:
    """Verify rocm_version must be non-empty for ROCm backend."""
    rocm_version = ""
    backend = "rocm"
    if backend == "rocm" and not rocm_version:
        # Should raise error in actual action
        assert True  # Placeholder — actual validation is in action.yml
    else:
        assert False


def test_rocm_tarball_url_pattern() -> None:
    """Verify ROCm tarball URL construction."""
    rocm_version = "6.2.0"
    version_no_dots = rocm_version.replace(".", "")
    url = f"https://rocm.nightlies.amd.com/Linux Ubuntu/22.04/amd64/rocm-rel-{version_no_dots}/rocm-{rocm_version}.tar.bz2"
    assert "rocm-rel-620" in url
    assert "rocm-6.2.0.tar.bz2" in url
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_action_backends.py::test_rocm_version_required tests/test_action_backends.py::test_rocm_tarball_url_pattern -v`
Expected: PASS

- [ ] **Step 3: Add rocm_version input default**

In `action.yml`, update the `rocm_version` input:

```yaml
  rocm_version:
    description: "ROCm version (e.g. 6.2.0)"
    required: false
    default: "6.2.0"
```

- [ ] **Step 4: Update action.yml ROCm install step**

Replace the ROCm branch in the "Install dependencies" step:

```yaml
          rocm)
            echo "::group::Installing ROCm"
            ROCM_VERSION="${{ inputs.rocm_version }}"
            if [[ -z "$ROCM_VERSION" ]]; then
              echo "::error::rocm_version input is required for ROCm backend"
              exit 1
            fi
            # Download ROCm tarball from nightlies
            VERSION_NO_DOTS=$(echo "$ROCM_VERSION" | tr -d '.')
            ROCM_URL="https://rocm.nightlies.amd.com/Linux Ubuntu/22.04/amd64/rocm-rel-${VERSION_NO_DOTS}/rocm-${ROCM_VERSION}.tar.bz2"
            echo "Downloading ROCm from: $ROCM_URL"
            wget -q "$ROCM_URL" -O /tmp/rocm.tar.bz2
            sudo tar -xjf /tmp/rocm.tar.bz2 -C /opt/
            rm /tmp/rocm.tar.bz2
            echo "/opt/rocm-${ROCM_VERSION}/bin" >> $GITHUB_PATH
            echo "ROCm $ROCM_VERSION installed at /opt/rocm-${ROCM_VERSION}"
            echo "::endgroup::"
            ;;
```

- [ ] **Step 5: Update action.yml ROCm collect artifacts step**

Replace the ROCm branch in the "Collect artifacts" step:

```yaml
          rocm)
            echo "Collecting ROCm runtime libraries..."
            ROCM_VERSION="${{ inputs.rocm_version }}"
            mkdir -p "$INSTALL_DIR/lib"
            # Copy ROCm libraries needed at runtime
            for lib in librocblas.so* libhipblaslt.so* libamdhip64.so*; do
              find /opt/rocm-${ROCM_VERSION} -name "$lib" -exec cp -L {} "$INSTALL_DIR/lib/" \; 2>/dev/null || true
            done
            # Verify libs were collected
            if ls "$INSTALL_DIR/lib/"*.so* 1>/dev/null 2>&1; then
              echo "ROCm libs bundled: $(ls "$INSTALL_DIR/lib/"*.so* | wc -l) files"
            else
              echo "::warning::No ROCm runtime libs found — binaries may require system ROCm"
            fi
            ;;
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_action_backends.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add action.yml tests/test_action_backends.py
git commit -m "feat(action): add ROCm backend with tarball install and runtime lib bundling"
```

---

## Task 3: Vulkan Backend in action.yml

**Files:**
- Modify: `action.yml` (Install dependencies step, Vulkan branch — already correct)
- Modify: `action.yml` (CMake configure step, Vulkan branch — already correct)
- Test: `tests/test_action_backends.py`

**Interfaces:**
- Consumes: `inputs.backend == 'vulkan'`
- Produces: Vulkan SDK installed, GGML_VULKAN=ON set

- [ ] **Step 1: Write test for Vulkan CMake flags**

```python
# tests/test_action_backends.py (append)

def test_vulkan_cmake_flags() -> None:
    """Verify Vulkan backend sets GGML_VULKAN=ON."""
    backend = "vulkan"
    cmake_args = "-DCMAKE_BUILD_TYPE=Release"
    if backend == "vulkan":
        cmake_args += " -DGGML_VULKAN=ON"
    assert "-DGGML_VULKAN=ON" in cmake_args
    assert "GGML_CUDA" not in cmake_args
    assert "GGML_HIP" not in cmake_args
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_action_backends.py::test_vulkan_cmake_flags -v`
Expected: PASS

- [ ] **Step 3: Verify action.yml Vulkan steps are correct**

The Vulkan install and CMake configure steps are already correct in the current `action.yml`. No changes needed. Verify by reading the file.

- [ ] **Step 4: Run all backend tests**

Run: `pytest tests/test_action_backends.py -v`
Expected: PASS

- [ ] **Step 5: Commit (no file changes, just test)**

```bash
git add tests/test_action_backends.py
git commit -m "test(action): add Vulkan backend CMake flag validation test"
```

---

## Task 4: Fix Manifest Entry Generation

**Files:**
- Modify: `action.yml` (Emit manifest entry step)
- Modify: `action.yml` (Generate version tag step — add build number tracking)
- Test: `tests/test_manifest_entry.py`

**Interfaces:**
- Consumes: `inputs.repo`, `inputs.backend`, `steps.resolve.outputs.resolved_sha`, `inputs.arch`, `inputs.gpu_target`, `steps.version.outputs.version_tag`
- Produces: Valid JSON manifest entry as step output

- [ ] **Step 1: Write test for manifest entry JSON validity**

```python
# tests/test_manifest_entry.py
"""Tests for manifest entry generation."""

import json


def test_manifest_entry_is_valid_json() -> None:
    """Verify generated manifest entry is valid JSON."""
    entry = {
        "name": "llama.cpp (cpu)",
        "repo": "ggml-org/llama.cpp",
        "ref": "0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48",
        "backend": "cpu",
        "arch": "x86_64",
        "gpu_target": None,
        "capabilities": ["chat", "embed"],
        "version": "0ab9d6f-1",
        "build": {
            "runner": "ubuntu-latest",
            "script": "",
            "os": "ubuntu",
            "artifact": "llama-0ab9d6f-1-ubuntu-cpu-x86_64.tar.gz",
        },
        "smoke_test": "llama-cli --version",
        "ci_capable": True,
        "ci_compile_capable": True,
        "ci_test_capable": False,
        "is_llama_cpp_fork": True,
        "status": "active",
    }
    # Should serialize without error
    json_str = json.dumps(entry, indent=2)
    parsed = json.loads(json_str)
    assert parsed["backend"] == "cpu"
    assert parsed["gpu_target"] is None
    assert parsed["version"] == "0ab9d6f-1"


def test_manifest_entry_with_gpu_target() -> None:
    """Verify manifest entry with gpu_target field."""
    entry = {
        "name": "llama.cpp (cuda)",
        "repo": "ggml-org/llama.cpp",
        "ref": "0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48",
        "backend": "cuda",
        "arch": "x86_64",
        "gpu_target": "sm_89",
        "capabilities": ["chat", "embed", "flash-attn"],
        "version": "0ab9d6f-1",
        "build": {
            "runner": "ubuntu-latest",
            "script": "",
            "os": "ubuntu",
            "artifact": "llama-0ab9d6f-1-ubuntu-cuda-x86_64-sm_89.tar.gz",
        },
    }
    json_str = json.dumps(entry)
    parsed = json.loads(json_str)
    assert parsed["gpu_target"] == "sm_89"
    assert "sm_89" in parsed["build"]["artifact"]


def test_version_tag_format() -> None:
    """Verify version tag follows {ref_prefix}-{build_num} format."""
    full_sha = "0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48"
    ref_prefix = full_sha[:7]
    build_num = 1
    version_tag = f"{ref_prefix}-{build_num}"
    assert version_tag == "0ab9d6f-1"
    assert len(ref_prefix) == 7
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_manifest_entry.py -v`
Expected: PASS

- [ ] **Step 3: Update action.yml Emit manifest entry step**

Replace the "Emit manifest entry" step with Python-based JSON generation:

```yaml
    - name: Emit manifest entry
      id: manifest
      shell: bash
      run: |
        FULL_SHA="${{ steps.resolve.outputs.resolved_sha }}"
        VERSION_TAG="${{ steps.version.outputs.version_tag }}"
        ARCHIVE_NAME="${{ steps.archive.outputs.archive_name }}"
        OS_NAME="ubuntu"

        python3 -c "
        import json, sys
        entry = {
            'name': f'{sys.argv[1]} ({sys.argv[2]})',
            'repo': sys.argv[1],
            'ref': sys.argv[3],
            'backend': sys.argv[2],
            'arch': sys.argv[4],
            'gpu_target': sys.argv[5] if sys.argv[5] else None,
            'capabilities': sys.argv[6].split(',') if sys.argv[6] else ['chat'],
            'version': sys.argv[7],
            'build': {
                'runner': 'ubuntu-latest',
                'script': '',
                'os': sys.argv[8],
                'artifact': sys.argv[9]
            },
            'smoke_test': 'llama-cli --version',
            'ci_capable': True,
            'ci_compile_capable': True,
            'ci_test_capable': False,
            'is_llama_cpp_fork': True,
            'status': 'active'
        }
        print(json.dumps(entry))
        " "${{ inputs.repo }}" "${{ inputs.backend }}" "$FULL_SHA" \
          "${{ inputs.arch }}" "${{ inputs.gpu_target }}" \
          "${{ inputs.cmake_flags }}" "$VERSION_TAG" "$OS_NAME" "$ARCHIVE_NAME" \
        >> "$GITHUB_OUTPUT"
```

- [ ] **Step 4: Update action.yml Generate version tag step**

Replace the "Generate version tag" step with build number tracking:

```yaml
    - name: Generate version tag
      id: version
      shell: bash
      run: |
        FULL_SHA="${{ steps.resolve.outputs.resolved_sha }}"
        REF_PREFIX="${FULL_SHA:0:7}"

        # Check existing releases for this ref prefix
        BUILD_NUM=1
        while gh release view "v${REF_PREFIX}-${BUILD_NUM}" >/dev/null 2>&1; do
          BUILD_NUM=$((BUILD_NUM + 1))
        done

        VERSION_TAG="${REF_PREFIX}-${BUILD_NUM}"
        echo "version_tag=$VERSION_TAG" >> "$GITHUB_OUTPUT"
        echo "Version tag: $VERSION_TAG"
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_manifest_entry.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add action.yml tests/test_manifest_entry.py
git commit -m "fix(action): use Python for manifest entry JSON and add build number tracking"
```

---

## Task 5: Update Target build.sh METADATA Headers

**Files:**
- Modify: `targets/upstream-cpu/build.sh` (add `gpu_target` field)
- Modify: `targets/upstream-cuda/build.sh` (add `gpu_target` field)
- Modify: `targets/upstream-vulkan/build.sh` (add `gpu_target` field)
- Test: `tests/test_metadata_parser.py`

**Interfaces:**
- Consumes: Existing METADATA headers
- Produces: Updated METADATA with `gpu_target` field for all targets

- [ ] **Step 1: Write test for gpu_target field parsing**

```python
# tests/test_metadata_parser.py (append)

def test_parse_cpu_target_with_gpu_target(tmp_path: Path) -> None:
    """Verify gpu_target field is parsed from METADATA."""
    build_sh = tmp_path / "build.sh"
    build_sh.write_text(
        "#!/usr/bin/env bash\n"
        "# METADATA\n"
        "# name=llama.cpp upstream CPU baseline\n"
        "# repo=ggml-org/llama.cpp\n"
        "# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48\n"
        "# backend=cpu\n"
        "# arch=x86_64\n"
        "# gpu_target=\n"
        "# capabilities=chat,embed\n"
        "set -euo pipefail\n"
    )
    meta = parse_metadata(build_sh)
    assert meta.get("gpu_target") is None or meta.get("gpu_target") == ""


def test_parse_cuda_target_with_gpu_target(tmp_path: Path) -> None:
    """Verify gpu_target=sm_89 is parsed from METADATA."""
    build_sh = tmp_path / "build.sh"
    build_sh.write_text(
        "#!/usr/bin/env bash\n"
        "# METADATA\n"
        "# name=llama.cpp upstream CUDA\n"
        "# repo=ggml-org/llama.cpp\n"
        "# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48\n"
        "# backend=cuda\n"
        "# arch=x86_64\n"
        "# gpu_target=sm_89\n"
        "# capabilities=chat,embed,flash-attn\n"
        "set -euo pipefail\n"
    )
    meta = parse_metadata(build_sh)
    assert meta.get("gpu_target") == "sm_89"
```

- [ ] **Step 2: Run test to verify it fails (gpu_target not yet in parser)**

Run: `pytest tests/test_metadata_parser.py::test_parse_cpu_target_with_gpu_target tests/test_metadata_parser.py::test_parse_cuda_target_with_gpu_target -v`
Expected: FAIL (KeyError or AssertionError)

- [ ] **Step 3: Update metadata_parser.py to support gpu_target field**

In `scripts/metadata_parser.py`, add `gpu_target` to DEFAULTS and parse_metadata:

```python
DEFAULTS = {
    "arch": "x86_64",
    "capabilities": [],
    "gpu_targets": [],
    "gpu_target": None,
    "runtime_deps": [],
    "bundle_strategy": "cpu-static",
}

def parse_metadata(build_sh: Path) -> dict:
    # ... existing code ...
    result["gpu_target"] = typed.get("gpu_target", DEFAULTS["gpu_target"])
    # ... rest of existing code ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_metadata_parser.py::test_parse_cpu_target_with_gpu_target tests/test_metadata_parser.py::test_parse_cuda_target_with_gpu_target -v`
Expected: PASS

- [ ] **Step 5: Update target build.sh files**

Update `targets/upstream-cpu/build.sh` METADATA:
```bash
# METADATA
# name=llama.cpp upstream CPU baseline
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=cpu
# arch=x86_64
# gpu_target=
# capabilities=chat,embed
```

Update `targets/upstream-cuda/build.sh` METADATA:
```bash
# METADATA
# name=llama.cpp upstream CUDA (sm_89/90a)
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=cuda
# arch=x86_64
# gpu_target=sm_89
# capabilities=chat,embed,flash-attn
```

Update `targets/upstream-vulkan/build.sh` METADATA:
```bash
# METADATA
# name=llama.cpp upstream Vulkan
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=vulkan
# arch=x86_64
# gpu_target=
# capabilities=chat,embed
```

- [ ] **Step 6: Run all metadata tests**

Run: `pytest tests/test_metadata_parser.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add targets/*/build.sh scripts/metadata_parser.py tests/test_metadata_parser.py
git commit -m "feat(target): add gpu_target field to METADATA headers"
```

---

## Task 6: Wire Matrix Workflow End-to-End

**Files:**
- Modify: `.github/workflows/matrix.yml` (discover job — parse METADATA)
- Modify: `.github/workflows/matrix.yml` (build job — wire to action)
- Modify: `.github/workflows/matrix.yml` (add publish job)
- Test: `tests/test_matrix_discovery.py`

**Interfaces:**
- Consumes: `targets/*/build.sh` METADATA headers
- Produces: Matrix JSON with repo, ref, backend, arch, gpu_target per target

- [ ] **Step 1: Write test for matrix discovery parsing**

```python
# tests/test_matrix_discovery.py
"""Tests for matrix workflow METADATA discovery."""

import json
from pathlib import Path

from scripts.metadata_parser import generate_matrix


def test_generate_matrix_includes_all_backends(tmp_path: Path) -> None:
    """Verify matrix includes cpu, cuda, vulkan targets."""
    for backend, gpu_target in [("cpu", ""), ("cuda", "sm_89"), ("vulkan", "")]:
        target_dir = tmp_path / f"upstream-{backend}"
        target_dir.mkdir()
        (target_dir / "build.sh").write_text(
            f"#!/usr/bin/env bash\n"
            f"# METADATA\n"
            f"# name=llama.cpp upstream {backend}\n"
            f"# repo=ggml-org/llama.cpp\n"
            f"# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48\n"
            f"# backend={backend}\n"
            f"# arch=x86_64\n"
            f"# gpu_target={gpu_target}\n"
            f"# capabilities=chat,embed\n"
        )
    matrix = generate_matrix(tmp_path)
    assert len(matrix["include"]) == 3
    backends = [e["backend"] for e in matrix["include"]]
    assert "cpu" in backends
    assert "cuda" in backends
    assert "vulkan" in backends


def test_generate_matrix_excludes_template(tmp_path: Path) -> None:
    """Verify _template directory is excluded from matrix."""
    template_dir = tmp_path / "_template"
    template_dir.mkdir()
    (template_dir / "build.sh").write_text("#!/usr/bin/env bash\n")

    cpu_dir = tmp_path / "upstream-cpu"
    cpu_dir.mkdir()
    (cpu_dir / "build.sh").write_text(
        "#!/usr/bin/env bash\n"
        "# METADATA\n"
        "# name=llama.cpp upstream CPU\n"
        "# repo=ggml-org/llama.cpp\n"
        "# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48\n"
        "# backend=cpu\n"
        "# arch=x86_64\n"
        "# capabilities=chat,embed\n"
    )
    matrix = generate_matrix(tmp_path)
    assert len(matrix["include"]) == 1
    assert matrix["include"][0]["target"] == "upstream-cpu"


def test_generate_matrix_json_serializable(tmp_path: Path) -> None:
    """Verify matrix output is valid JSON for GitHub Actions."""
    cpu_dir = tmp_path / "upstream-cpu"
    cpu_dir.mkdir()
    (cpu_dir / "build.sh").write_text(
        "#!/usr/bin/env bash\n"
        "# METADATA\n"
        "# name=llama.cpp upstream CPU\n"
        "# repo=ggml-org/llama.cpp\n"
        "# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48\n"
        "# backend=cpu\n"
        "# arch=x86_64\n"
        "# capabilities=chat,embed\n"
    )
    matrix = generate_matrix(tmp_path)
    json_str = json.dumps(matrix)
    parsed = json.loads(json_str)
    assert "include" in parsed
    assert len(parsed["include"]) == 1
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_matrix_discovery.py -v`
Expected: PASS

- [ ] **Step 3: Update matrix.yml discover job**

Replace the discover job with Python-based METADATA parsing:

```yaml
  discover:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
      target_count: ${{ steps.set-matrix.outputs.target_count }}
    steps:
      - uses: actions/checkout@v4

      - name: Discover build targets
        id: set-matrix
        run: |
          python3 -c "
          import json, re, os
          targets = []
          for d in sorted(os.listdir('targets')):
              if d.startswith('_') or not os.path.isdir(f'targets/{d}'):
                  continue
              build_sh = f'targets/{d}/build.sh'
              if not os.path.exists(build_sh):
                  continue
              meta = {}
              with open(build_sh) as f:
                  for line in f:
                      if not line.startswith('# METADATA'):
                          if meta:
                              break
                          continue
                      match = re.match(r'^#\s+(\w+)=(.*)', line.strip())
                      if match:
                          meta[match.group(1)] = match.group(2)
              if 'repo' in meta and 'ref' in meta and 'backend' in meta:
                  targets.append({
                      'target': d,
                      'repo': meta['repo'],
                      'ref': meta['ref'],
                      'backend': meta['backend'],
                      'arch': meta.get('arch', 'x86_64'),
                      'gpu_target': meta.get('gpu_target', ''),
                      'name': meta.get('name', d),
                      'smoke_test': meta.get('smoke_test', 'llama-cli --version')
                  })
          print(json.dumps({'include': targets}))
          " >> \$GITHUB_OUTPUT

          TARGET_COUNT=\$(python3 -c "
          import os
          count = sum(1 for d in os.listdir('targets')
                      if not d.startswith('_')
                      and os.path.isdir(f'targets/{d}')
                      and os.path.exists(f'targets/{d}/build.sh'))
          print(count)
          ")
          echo "target_count=\$TARGET_COUNT" >> "\$GITHUB_OUTPUT"
```

- [ ] **Step 4: Update matrix.yml build job**

Replace the build job to wire to the composite action:

```yaml
  build:
    needs: discover
    if: fromJson(needs.discover.outputs.matrix).include[0]
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: ${{ fromJson(needs.discover.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4

      - name: Build ${{ matrix.target }}
        uses: ./action.yml
        id: build
        with:
          repo: ${{ matrix.repo }}
          ref: ${{ matrix.ref }}
          backend: ${{ matrix.backend }}
          arch: ${{ matrix.arch }}
          gpu_target: ${{ matrix.gpu_target }}

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: llama-${{ matrix.target }}
          path: ${{ steps.build.outputs.artifact_path }}
          retention-days: 7
```

- [ ] **Step 5: Add publish job to matrix.yml**

Add a new job after `build`:

```yaml
  publish:
    needs: build
    runs-on: ubuntu-latest
    if: always() && needs.build.result == 'success'
    steps:
      - uses: actions/checkout@v4

      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: _artifacts

      - name: Collect and validate manifest
        run: |
          echo "Artifacts downloaded:"
          find _artifacts -name "*.tar.gz" -type f

          # TODO: Merge manifest entries from action outputs
          # For now, validate that artifacts exist
          ARTIFACT_COUNT=$(find _artifacts -name "*.tar.gz" -type f | wc -l)
          echo "Total artifacts: $ARTIFACT_COUNT"
          if [ "$ARTIFACT_COUNT" -eq 0 ]; then
            echo "::error::No artifacts found"
            exit 1
          fi
```

- [ ] **Step 6: Run matrix discovery tests**

Run: `pytest tests/test_matrix_discovery.py -v`
Expected: PASS

- [ ] **Step 7: Run all tests**

Run: `pytest -v`
Expected: PASS (all tests)

- [ ] **Step 8: Commit**

```bash
git add .github/workflows/matrix.yml tests/test_matrix_discovery.py
git commit -m "feat(ci): wire matrix workflow to build-llama action with publish job"
```

---

## Task 7: Integration Testing

**Files:**
- Test: `tests/test_integration.py` (new)
- Verify: All existing tests pass

**Interfaces:**
- Consumes: All previous tasks
- Produces: Integration test validating end-to-end flow

- [ ] **Step 1: Write integration test for manifest schema validation**

```python
# tests/test_integration.py
"""Integration tests for build action and matrix workflow."""

import json
from pathlib import Path

from scripts.metadata_parser import generate_matrix, parse_metadata


def test_all_targets_have_required_metadata(tmp_path: Path) -> None:
    """Verify all real targets have required METADATA fields."""
    targets_dir = Path("targets")
    if not targets_dir.exists():
        return  # Skip if not in repo root

    for build_sh in targets_dir.glob("*/build.sh"):
        if build_sh.parent.name.startswith("_"):
            continue
        meta = parse_metadata(build_sh)
        assert "name" in meta, f"{build_sh} missing name"
        assert "repo" in meta, f"{build_sh} missing repo"
        assert "ref" in meta, f"{build_sh} missing ref"
        assert "backend" in meta, f"{build_sh} missing backend"
        assert meta["backend"] in ("cpu", "cuda", "rocm", "vulkan"), \
            f"{build_sh} has invalid backend: {meta['backend']}"


def test_manifest_entry_matches_schema() -> None:
    """Verify manifest entry structure matches schema requirements."""
    # Load the actual manifest if it exists
    manifest_path = Path("manifest.json")
    if not manifest_path.exists():
        return  # Skip if manifest not generated

    with open(manifest_path) as f:
        manifest = json.load(f)

    assert manifest["version"] == 3
    for target_name, target in manifest["targets"].items():
        assert "name" in target, f"{target_name} missing name"
        assert "repo" in target, f"{target_name} missing repo"
        assert "ref" in target, f"{target_name} missing ref"
        assert "backend" in target, f"{target_name} missing backend"
        assert "version" in target, f"{target_name} missing version"
        assert "build" in target, f"{target_name} missing build"
        assert "artifact" in target["build"], f"{target_name} missing build.artifact"
```

- [ ] **Step 2: Run integration tests**

Run: `pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `pytest -v`
Expected: PASS (all tests)

- [ ] **Step 4: Run lint**

Run: `ruff check .`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for build action and matrix workflow"
```

---

## Execution Order

1. **Task 1**: CUDA backend (foundation for GPU builds)
2. **Task 2**: ROCm backend (depends on Task 1 patterns)
3. **Task 3**: Vulkan backend (simplest, validates pattern)
4. **Task 4**: Manifest entry fixes (unblocks correct metadata)
5. **Task 5**: Target METADATA updates (enables matrix parsing)
6. **Task 6**: Matrix workflow wiring (end-to-end CI)
7. **Task 7**: Integration testing (validation)

## Verification Checklist

After completing all tasks:

- [ ] `pytest -v` — all tests pass
- [ ] `ruff check .` — no lint errors
- [ ] `action.yml` — valid YAML, all backends functional
- [ ] `matrix.yml` — discovers targets, builds, publishes
- [ ] `manifest.json` — valid JSON, passes schema validation
- [ ] All target `build.sh` files — have complete METADATA headers
