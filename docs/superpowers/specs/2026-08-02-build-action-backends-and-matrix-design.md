# Build Action Backends & Matrix Wiring Design

**Date:** 2026-08-02
**Status:** Approved — ready for implementation planning
**Supersedes:** N/A (extends `2026-08-02-build-action-design.md`)

## Problem Statement

The build action (`action.yml`) has a working skeleton for CPU builds but CUDA, ROCm, and Vulkan backends are stubs. The matrix workflow (`matrix.yml`) discovers targets but doesn't wire to the action. We need to:

1. Complete all three GPU backends in the action
2. Fix manifest entry generation (JSON quoting, missing fields)
3. Wire the matrix workflow end-to-end: discover → build → publish

## Goals

1. **Working CUDA backend** — Install toolkit, set GGML_CUDA flags, bundle runtime libs
2. **Working ROCm backend** — Install ROCm tarball, set GGML_HIP flags, bundle runtime libs
3. **Working Vulkan backend** — Install Vulkan SDK, set GGML_VULKAN flags
4. **Valid manifest entries** — Python-based JSON generation, proper field coverage
5. **End-to-end matrix CI** — Discover targets → build → collect artifacts → publish manifest

## Non-Goals

- Lemonade adapter (separate spec)
- Python/OCI/WASM adapters (separate specs)
- Self-hosted GPU runners (org infra decision)
- Smoke test execution (separate job, not part of build action)

---

## CUDA Backend

### Changes to `action.yml`

**Install dependencies (CUDA branch):**
```yaml
cuda)
  echo "::group::Installing CUDA toolkit"
  - uses: Jimver/cuda-toolkit@v0.2.21
    id: cuda-toolkit
    with:
      method: network
      linux-local-args: '["--toolkit"]'
  echo "CUDA installed: ${{ steps.cuda-toolkit.outputs.cuda }}"
  echo "::endgroup::"
  ;;
```

**CMake configure (CUDA branch) — unchanged:**
```yaml
cuda)
  CMAKE_ARGS="$CMAKE_ARGS -DGGML_CUDA=ON"
  if [[ -n "${{ inputs.gpu_target }}" ]]; then
    SM_NUM="${{ inputs.gpu_target#sm_ }}"
    CMAKE_ARGS="$CMAKE_ARGS -DCMAKE_CUDA_ARCHITECTURES=$SM_NUM"
  fi
  ;;
```

**Collect artifacts (CUDA branch):**
```yaml
cuda)
  echo "Collecting CUDA runtime libraries..."
  mkdir -p "$INSTALL_DIR/lib"
  for lib in libcublas.so* libcublaslt.so*; do
    find /usr/local/cuda -name "$lib" -exec cp -L {} "$INSTALL_DIR/lib/" \; 2>/dev/null || true
  done
  ;;
```

### Changes to `targets/upstream-cuda/build.sh`

Update METADATA header to include all fields:
```bash
# METADATA
# name=llama.cpp upstream CUDA (sm_89/90a)
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=cuda
# arch=x86_64
# capabilities=chat,embed,flash-attn
# gpu_target=sm_89
# build_system=cmake
# smoke_test=llama-cli --version
```

### Testing

1. Run locally with `act` against pinned SHA
2. Verify `llama-cli --version` smoke test passes
3. Check CUDA libs are bundled in archive
4. Validate manifest entry against schema

---

## ROCm Backend

### Changes to `action.yml`

**Install dependencies (ROCm branch):**
```yaml
rocm)
  echo "::group::Installing ROCm"
  ROCM_VERSION="${{ inputs.rocm_version }}"
  if [[ -z "$ROCM_VERSION" ]]; then
    echo "::error::rocm_version input is required for ROCm backend"
    exit 1
  fi
  wget -q "https://rocm.nightlies.amd.com/Linux Ubuntu/22.04/amd64/rocm-rel-$(echo $ROCM_VERSION | tr -d .)/rocm-$ROCM_VERSION.tar.bz2"
  tar -xjf "rocm-$ROCM_VERSION.tar.bz2" -C /opt/
  export PATH="/opt/rocm-$ROCM_VERSION/bin:$PATH"
  echo "ROCm $ROCM_VERSION installed"
  echo "::endgroup::"
  ;;
```

**CMake configure (ROCm branch) — unchanged:**
```yaml
rocm)
  CMAKE_ARGS="$CMAKE_ARGS -DGGML_HIP=ON"
  if [[ -n "${{ inputs.gpu_target }}" ]]; then
    CMAKE_ARGS="$CMAKE_ARGS -DAMDGPU_TARGETS=${{ inputs.gpu_target }}"
  fi
  ;;
```

**Collect artifacts (ROCm branch):**
```yaml
rocm)
  echo "Collecting ROCm runtime libraries..."
  mkdir -p "$INSTALL_DIR/lib/rocblas" "$INSTALL_DIR/lib/hipblaslt"
  for lib in librocblas.so* libhipblaslt.so*; do
    find /opt/rocm-$ROCM_VERSION -name "$lib" -exec cp -L {} "$INSTALL_DIR/lib/" \; 2>/dev/null || true
  done
  cp -r /opt/rocm-$ROCM_VERSION/lib/rocblas "$INSTALL_DIR/lib/" 2>/dev/null || true
  cp -r /opt/rocm-$ROCM_VERSION/lib/hipblaslt "$INSTALL_DIR/lib/" 2>/dev/null || true
  ;;
```

### Changes to `targets/upstream-rocm/build.sh`

Update METADATA header:
```bash
# METADATA
# name=llama.cpp upstream ROCm baseline
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=rocm
# arch=x86_64
# capabilities=chat,embed
# build_system=cmake
# smoke_test=llama-cli --version
```

### ROCm Version Pinning

The action requires `rocm_version` input. Default to `6.2.0` (stable) but allow override. The tarball URL pattern:
```
https://rocm.nightlies.amd.com/Linux Ubuntu/22.04/amd64/rocm-rel-620/rocm-6.2.0.tar.bz2
```

### Testing

1. Test with pinned ROCm version on Ubuntu 22.04
2. Verify `llama-cli --version` smoke test
3. Check ROCm libs are bundled
4. Validate manifest entry

---

## Vulkan Backend

### Changes to `action.yml`

**Install dependencies (Vulkan branch) — unchanged:**
```yaml
vulkan)
  echo "::group::Installing Vulkan SDK"
  sudo apt-get install -y -qq libvulkan-dev vulkan-validationlayers
  echo "::endgroup::"
  ;;
```

**CMake configure (Vulkan branch) — unchanged:**
```yaml
vulkan)
  CMAKE_ARGS="$CMAKE_ARGS -DGGML_VULKAN=ON"
  ;;
```

**No runtime lib collection needed** — Vulkan binaries link against system Vulkan drivers.

### Changes to `targets/upstream-vulkan/build.sh`

Update METADATA header:
```bash
# METADATA
# name=llama.cpp upstream Vulkan
# repo=ggml-org/llama.cpp
# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48
# backend=vulkan
# arch=x86_64
# capabilities=chat,embed
# build_system=cmake
# smoke_test=llama-cli --version
```

### Testing

1. Test on Ubuntu with Vulkan SDK installed
2. Verify `llama-cli --version` smoke test
3. Validate manifest entry

---

## Manifest Entry Fixes

### Problem

The current `Emit manifest entry` step uses `printf` with shell escaping issues. JSON is malformed for entries with special characters.

### Solution

Replace with Python-based JSON generation:

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
        'capabilities': sys.argv[6].split(','),
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

### Build Number Tracking

For the matrix workflow, `version_tag` should check existing GitHub Releases:

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

---

## Matrix Workflow Wiring

### Job 1: `discover` — Parse METADATA Headers

```yaml
discover:
  runs-on: ubuntu-latest
  outputs:
    matrix: ${{ steps.set-matrix.outputs.matrix }}
  steps:
    - uses: actions/checkout@v4

    - id: set-matrix
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
```

### Job 2: `build` — Wire to Action

```yaml
build:
  needs: discover
  runs-on: ubuntu-latest
  if: fromJson(needs.discover.outputs.matrix).include[0]
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
```

### Job 3: `publish` — Collect Manifest

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

    - name: Collect manifest entries
      run: |
        python3 scripts/generate_manifest.py --from-artifacts _artifacts
```

### End-to-End Flow

```
PR opened
  → matrix.yml triggers
    → discover: parse targets/*/build.sh METADATA
    → build: matrix expansion → build-llama action per target
    → publish: merge manifest entries → validate → upload
```

---

## Testing Strategy

1. **Unit tests** — Test metadata extraction from build.sh headers
2. **Integration tests** — Test each backend with pinned SHA
3. **Matrix validation** — Verify matrix expands correctly
4. **Manifest validation** — Verify generated entries pass schema validation

## Migration Path

1. **Phase 1**: CUDA backend + manifest fixes
2. **Phase 2**: ROCm backend
3. **Phase 3**: Vulkan backend
4. **Phase 4**: Matrix workflow wiring
5. **Phase 5**: End-to-end testing
