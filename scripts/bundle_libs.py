"""Bundle runtime libraries into build artifact directories."""

from __future__ import annotations

import fnmatch
import shutil
import subprocess
from pathlib import Path

BUNDLE_STRATEGIES: dict[str, dict] = {
    "cpu-static": {
        "patterns": [],
        "rpath": "$ORIGIN",
    },
    "rocm-therock": {
        "patterns": [
            "librocblas.so*",
            "libhipblas.so*",
            "libamdhip64.so*",
            "librocsolver.so*",
            "libroctx64.so*",
            "libhipblaslt.so*",
            "librocprofiler-register.so*",
            "libamd_comgr.so*",
            "libhsa-runtime64.so*",
            "librocroller.so*",
            "liborigami.so*",
            "librocm_kpack.so*",
            "libLLVM.so*",
            "libclang-cpp.so*",
        ],
        "rpath": "$ORIGIN",
        "extra_dirs": ["rocblas/library", "hipblaslt/library"],
    },
    "cuda-redist": {
        "patterns": [
            "libcublas.so*",
            "libcublasLt.so*",
            "libcudart.so*",
            "libcufft.so*",
            "libcusparse.so*",
            "libcusolver.so*",
            "libnvrtc.so*",
            "libnvJitLink.so*",
        ],
        "rpath": "$ORIGIN",
    },
    "vulkan-sdk": {
        "patterns": [
            "libvulkan.so*",
            "libSPIRV*.so*",
        ],
        "rpath": "$ORIGIN",
    },
}


def _matches_any(filename: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(filename, p) for p in patterns)


def _copy_matching_files(source_dir: Path, dest_dir: Path, patterns: list[str]) -> int:
    """Copy files matching any pattern from source to dest. Returns count copied."""
    count = 0
    if not source_dir.exists():
        return count
    for file in source_dir.iterdir():
        if file.is_file() and _matches_any(file.name, patterns):
            shutil.copy2(file, dest_dir / file.name)
            count += 1
    return count


def _set_rpath(bin_dir: Path) -> None:
    """Set RPATH to $ORIGIN for all ELF binaries in directory."""
    for file in bin_dir.iterdir():
        if file.is_file() and not file.is_symlink():
            try:
                subprocess.run(
                    ["patchelf", "--set-rpath", "$ORIGIN", str(file)],
                    check=True,
                    capture_output=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass  # Not an ELF binary or patchelf not installed


def bundle_libs(artifact_dir: Path, strategy_name: str) -> None:
    """Bundle runtime libraries into artifact_dir using the named strategy."""
    strategy = BUNDLE_STRATEGIES.get(strategy_name)
    if not strategy or not strategy["patterns"]:
        return

    for pattern in strategy["patterns"]:
        # Search common library locations
        for lib_base in [Path("/usr/lib"), Path("/usr/lib64"), Path("/usr/local/lib")]:
            _copy_matching_files(lib_base, artifact_dir, [pattern])

    # Copy extra directories (e.g. ROCm tuning libraries)
    for extra in strategy.get("extra_dirs", []):
        for lib_base in [Path("/opt/rocm/lib"), Path("/opt/cuda/lib64")]:
            extra_src = lib_base / extra
            if extra_src.exists():
                dest = artifact_dir / extra
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copytree(extra_src, dest, dirs_exist_ok=True)

    _set_rpath(artifact_dir)


def bundle_libs_custom(artifact_dir: Path, source_dir: Path, patterns: list[str]) -> None:
    """Copy files matching patterns from source_dir into artifact_dir."""
    _copy_matching_files(source_dir, artifact_dir, patterns)
