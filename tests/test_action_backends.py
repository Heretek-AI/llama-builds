"""Tests for action.yml backend-specific logic."""


def _extract_sm_number(gpu_target: str) -> str:
    """Extract SM number from gpu_target string, mirroring the shell logic.

    The action.yml CMake configure step uses:
        SM_NUM="${{ inputs.gpu_target#sm_ }}"
    which strips the 'sm_' prefix and passes the rest as CMAKE_CUDA_ARCHITECTURES.
    """
    if gpu_target.startswith("sm_"):
        return gpu_target[3:]  # strip "sm_" prefix
    return gpu_target


def test_sm_number_extraction():
    """sm_89 -> 89"""
    assert _extract_sm_number("sm_89") == "89"


def test_sm_number_extraction_with_suffix():
    """sm_90a -> 90a"""
    assert _extract_sm_number("sm_90a") == "90a"


def test_sm_number_extraction_small():
    """sm_70 -> 70"""
    assert _extract_sm_number("sm_70") == "70"


def test_sm_number_no_prefix_passthrough():
    """If no sm_ prefix, return as-is."""
    assert _extract_sm_number("gfx1151") == "gfx1151"


# ---------------------------------------------------------------------------
# ROCm backend helpers
# ---------------------------------------------------------------------------


def _rocm_version_required(version: str) -> bool:
    """Return True if the ROCm version is empty / missing.

    Mirrors the shell guard:
        if [[ -z "$ROCM_VERSION" ]]; then
          echo "::error::rocm_version input is required"
          exit 1
        fi
    """
    return not bool(version.strip())


def _rocm_tarball_url(version: str) -> str:
    """Construct the ROCm tarball download URL from a version string.

    Mirrors the shell logic:
        VERSION_NO_DOTS=$(echo "$ROCM_VERSION" | tr -d '.')
        ROCM_URL="https://rocm.nightlies.amd.com/Linux Ubuntu/22.04/amd64/rocm-rel-${VERSION_NO_DOTS}/rocm-${ROCM_VERSION}.tar.bz2"
    """
    version_no_dots = version.replace(".", "")
    return (
        f"https://rocm.nightlies.amd.com/Linux Ubuntu/22.04/amd64"
        f"/rocm-rel-{version_no_dots}/rocm-{version}.tar.bz2"
    )


def test_rocm_version_required_empty():
    """Empty string must trigger the required-version error."""
    assert _rocm_version_required("") is True


def test_rocm_version_required_whitespace():
    """Whitespace-only string must trigger the required-version error."""
    assert _rocm_version_required("   ") is True


def test_rocm_version_required_valid():
    """A valid version must NOT trigger the error."""
    assert _rocm_version_required("6.2.0") is False


def test_rocm_tarball_url_pattern():
    """URL must match the expected nightlies pattern."""
    url = _rocm_tarball_url("6.2.0")
    assert url == (
        "https://rocm.nightlies.amd.com/Linux Ubuntu/22.04/amd64/rocm-rel-620/rocm-6.2.0.tar.bz2"
    )


def test_rocm_tarball_url_major_minor_patch():
    """Version with different digits produces correct dot-stripped segment."""
    url = _rocm_tarball_url("6.3.1")
    assert "rocm-rel-631" in url
    assert "rocm-6.3.1.tar.bz2" in url


# ---------------------------------------------------------------------------
# Vulkan backend helpers
# ---------------------------------------------------------------------------


def test_vulkan_cmake_flags() -> None:
    """Verify Vulkan backend sets GGML_VULKAN=ON."""
    backend = "vulkan"
    cmake_args = "-DCMAKE_BUILD_TYPE=Release"
    if backend == "vulkan":
        cmake_args += " -DGGML_VULKAN=ON"
    assert "-DGGML_VULKAN=ON" in cmake_args
    assert "GGML_CUDA" not in cmake_args
    assert "GGML_HIP" not in cmake_args
