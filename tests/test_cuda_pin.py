"""Tests for the CUDA toolkit version pin on ik_llama.cpp CUDA build.

Validates the lb-0095 acceptance criteria:
  - targets/ik-llama-cpp-cuda/build.sh exports CUDA_VERSION=12.4.0
  - .github/workflows/build.yml and matrix.yml install cuda-12-4 ONLY for ik-llama-cpp-cuda
  - scripts/check_cuda_version.sh exists, parses versions, exits non-zero on mismatch
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_CUDA_VERSION = "12.4.0"
IK_CUDA_SLUG = "ik-llama-cpp-cuda"
CUDA_BUILD_SH = REPO_ROOT / "targets" / "ik-llama-cpp-cuda" / "build.sh"
BUILD_YML = REPO_ROOT / ".github" / "workflows" / "build.yml"
MATRIX_YML = REPO_ROOT / ".github" / "workflows" / "matrix.yml"
CHECK_SH = REPO_ROOT / "scripts" / "check_cuda_version.sh"
FAKE_NVCC_MATCH = REPO_ROOT / "tests" / "fixtures" / "fake_nvcc.sh"
FAKE_NVCC_MISMATCH = REPO_ROOT / "tests" / "fixtures" / "fake_nvcc_mismatch.sh"

CUDA_VERSION_RE = re.compile(
    r"CUDA_VERSION=\"?\$\{?CUDA_VERSION(?::-(?P<pin>[0-9]+\.[0-9]+(?:\.[0-9]+)?))?\}?\"?"
    r"|CUDA_VERSION=(?P<direct>[0-9]+\.[0-9]+(?:\.[0-9]+)?)"
)


def _extract_pinned_version(text: str) -> str | None:
    match = CUDA_VERSION_RE.search(text)
    if not match:
        return None
    return match.group("pin") or match.group("direct")


def _read(p: Path) -> str:
    return p.read_text()


def _cuda_block(text: str) -> str:
    match = re.search(r"\bcuda\)\s*\n((?:\s{6,}.*\n|\s*;;\s*\n)+)", text)
    if not match:
        return ""
    return match.group(1)


class TestCudaPinInBuildScript:
    def test_build_sh_exists(self):
        assert CUDA_BUILD_SH.exists()

    def test_build_sh_exports_cuda_version(self):
        text = _read(CUDA_BUILD_SH)
        pinned = _extract_pinned_version(text)
        assert pinned, f"build.sh must export CUDA_VERSION=<X.Y.Z>, got:\n{text}"

    def test_build_sh_pins_to_12_4_0(self):
        text = _read(CUDA_BUILD_SH)
        pinned = _extract_pinned_version(text)
        assert pinned == EXPECTED_CUDA_VERSION, (
            f"Expected CUDA_VERSION={EXPECTED_CUDA_VERSION}, got {pinned!r}"
        )

    def test_build_sh_runtime_asserts_nvcc_version(self):
        text = _read(CUDA_BUILD_SH)
        assert "nvcc" in text
        assert "INSTALLED_CUDA" in text
        assert "mismatch" in text.lower()


class TestCudaPinInWorkflows:
    def test_build_yml_conditional_pin(self):
        text = _read(BUILD_YML)
        cuda_block = _cuda_block(text)
        assert cuda_block, "build.yml must have a cuda) case block"
        assert f'"{IK_CUDA_SLUG}"' in cuda_block or f"'{IK_CUDA_SLUG}'" in cuda_block, (
            "build.yml cuda) block must check for the ik-llama-cpp-cuda target slug"
        )
        assert "cuda-12-4" in cuda_block, (
            "build.yml cuda) block must install cuda-12-4 for ik-llama-cpp-cuda"
        )
        assert "cuda-toolkit" in cuda_block, (
            "build.yml cuda) block must still allow cuda-toolkit for non-pinned targets"
        )

    def test_matrix_yml_conditional_pin(self):
        text = _read(MATRIX_YML)
        cuda_block = _cuda_block(text)
        assert cuda_block, "matrix.yml must have a cuda) case block"
        assert f'"{IK_CUDA_SLUG}"' in cuda_block or f"'{IK_CUDA_SLUG}'" in cuda_block, (
            "matrix.yml cuda) block must check for the ik-llama-cpp-cuda target slug"
        )
        assert "cuda-12-4" in cuda_block, (
            "matrix.yml cuda) block must install cuda-12-4 for ik-llama-cpp-cuda"
        )
        assert "cuda-toolkit" in cuda_block, (
            "matrix.yml cuda) block must still allow cuda-toolkit for non-pinned targets"
        )

    def test_workflows_invoke_cuda_version_check_for_pinned_target(self):
        for label, path in (("build.yml", BUILD_YML), ("matrix.yml", MATRIX_YML)):
            text = _read(path)
            cuda_block = _cuda_block(text)
            assert "check_cuda_version.sh" in cuda_block, (
                f"{label} cuda) block must invoke scripts/check_cuda_version.sh"
            )


class TestCudaVersionCheckScript:
    def test_script_exists(self):
        assert CHECK_SH.exists()

    def test_script_is_executable(self):
        mode = CHECK_SH.stat().st_mode
        assert mode & 0o111

    def test_fake_nvcc_match_exists_and_is_executable(self):
        assert FAKE_NVCC_MATCH.exists()
        assert FAKE_NVCC_MATCH.stat().st_mode & 0o111

    def test_fake_nvcc_mismatch_exists_and_is_executable(self):
        assert FAKE_NVCC_MISMATCH.exists()
        assert FAKE_NVCC_MISMATCH.stat().st_mode & 0o111

    def test_script_succeeds_on_match(self):
        result = subprocess.run(
            ["bash", str(CHECK_SH), EXPECTED_CUDA_VERSION, str(FAKE_NVCC_MATCH)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"Expected exit 0; got {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_script_fails_on_mismatch(self):
        result = subprocess.run(
            ["bash", str(CHECK_SH), EXPECTED_CUDA_VERSION, str(FAKE_NVCC_MISMATCH)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0, (
            f"Expected non-zero exit; got {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        combined = (result.stdout + result.stderr).lower()
        assert "mismatch" in combined

    def test_script_fails_on_missing_argument(self):
        result = subprocess.run(
            ["bash", str(CHECK_SH)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
