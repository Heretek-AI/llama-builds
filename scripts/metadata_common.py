"""Shared METADATA parsing utilities for llama-builds targets.

Single source of truth for reading and parsing METADATA header blocks
from target build.sh files. Both metadata_parser.py and
generate_manifest.py import from this module.
"""

from __future__ import annotations

import re
from pathlib import Path

METADATA_HEADER = "# METADATA"
METADATA_PATTERN = re.compile(r"^#\s+(\w+)=(.+)$")

# v2 core fields (always present in METADATA)
CORE_FIELDS: dict[str, str] = {
    "name": "",
    "repo": "",
    "ref": "",
    "backend": "",
    "arch": "x86_64",
    "gpu_target": "",
    "capabilities": "",
    "bundle_strategy": "cpu-static",
}

# v3 new fields with defaults
NEW_FIELDS: dict[str, str | bool | int | list[str] | None] = {
    "default_branch": "main",
    "gpu_toolchain": "none",
    "extra_cmake_flags": "",
    "build_system": "cmake",
    "binary_names": "llama-server,llama-cli",
    "test_target": "",
    "layer": "base",
    "parent": None,
    "ci_capable": True,
    "ci_compile_capable": True,
    "ci_test_capable": False,
    "is_llama_cpp_fork": True,
    "smoke_test": "",
    "upstream_ref": None,
    "status": "active",
    "skip_reason": None,
    "repos": [],
}

# Valid enum values for v3 fields
VALID_BUILD_SYSTEMS = frozenset({
    "cmake", "make", "cibuildwheel", "cython", "go", "dotnet",
    "colcon", "dfx", "oci", "docs",
})
VALID_LAYERS = frozenset({"base", "backend", "variant", "docs"})
VALID_STATUSES = frozenset({"active", "skipped", "deprecated", "archived"})
VALID_GPU_TOOLCHAINS = frozenset({"cuda", "hip", "metal", "vulkan", "none"})
VALID_DEFAULT_BRANCHES = frozenset({"main", "master"})


class MetadataParseError(Exception):
    """Raised when METADATA block is missing or malformed."""


def parse_metadata_raw(build_sh: Path) -> dict[str, str]:
    """Read raw key=value strings from a METADATA block in a build.sh file.

    Returns a dict of string values for all keys found in the METADATA
    header. Raises MetadataParseError if no METADATA block or no keys found.

    This is the low-level parser that returns everything as strings.
    Use parse_metadata_typed() for coerced values.
    """
    in_metadata = False
    raw: dict[str, str] = {}

    for line in build_sh.read_text().splitlines():
        stripped = line.strip()
        if stripped == METADATA_HEADER:
            in_metadata = True
            continue
        if in_metadata:
            match = METADATA_PATTERN.match(stripped)
            if match:
                key, value = match.groups()
                raw[key] = value.strip()
            elif stripped == "":
                continue  # Skip blank lines within metadata block
            elif not stripped.startswith("#"):
                break  # End of metadata block

    if not raw or "name" not in raw:
        raise MetadataParseError(f"No METADATA block found in {build_sh}")

    return raw


def _coerce_bool(value: str) -> bool:
    """Coerce a string to bool. Accepts 'true'/'false' (case-insensitive)."""
    return value.lower() in ("true", "1", "yes")


def _coerce_csv(value: str) -> list[str]:
    """Coerce a comma-separated string to a list of stripped strings."""
    return [v.strip() for v in value.split(",") if v.strip()]


def _coerce_nullable_string(value: str) -> str | None:
    """Return None for empty strings, otherwise the string."""
    return value if value else None


def _coerce_nullable_csv(value: str) -> list[str] | None:
    """Return None for empty strings, otherwise a list from CSV."""
    return _coerce_csv(value) if value else None


def _coerce_repos(value: str) -> list[str]:
    """Coerce a comma-separated string to a list of repo strings."""
    return _coerce_csv(value)


def parse_metadata_typed(build_sh: Path) -> dict:
    """Parse METADATA block with type coercion for v2 + v3 fields.

    Returns a dict where:
    - Core v2 fields are always present (with defaults)
    - v3 fields are always present (with defaults)
    - CSV fields become lists
    - Boolean fields become bool
    - Nullable fields become str | None
    """
    raw = parse_metadata_raw(build_sh)

    result: dict = {}

    # Core v2 fields
    result["name"] = raw.get("name", CORE_FIELDS["name"])
    result["repo"] = raw.get("repo", CORE_FIELDS["repo"])
    result["ref"] = raw.get("ref", CORE_FIELDS["ref"])
    result["backend"] = raw.get("backend", CORE_FIELDS["backend"])
    result["arch"] = raw.get("arch", CORE_FIELDS["arch"])
    result["gpu_target"] = _coerce_nullable_string(
        raw.get("gpu_target", CORE_FIELDS["gpu_target"])
    )

    # CSV fields
    caps_raw = raw.get("capabilities", "")
    result["capabilities"] = _coerce_csv(caps_raw) if caps_raw else []

    gpu_raw = raw.get("gpu_targets", "")
    result["gpu_targets"] = _coerce_csv(gpu_raw) if gpu_raw else []

    runtime_raw = raw.get("runtime_deps", "")
    result["runtime_deps"] = _coerce_csv(runtime_raw) if runtime_raw else []

    result["bundle_strategy"] = raw.get("bundle_strategy", CORE_FIELDS["bundle_strategy"])

    # v3 new fields — always populated with defaults
    result["default_branch"] = raw.get("default_branch", "main")
    result["gpu_toolchain"] = raw.get("gpu_toolchain", "none")
    result["extra_cmake_flags"] = raw.get("extra_cmake_flags", "")
    result["build_system"] = raw.get("build_system", "cmake")
    result["binary_names"] = raw.get("binary_names", "llama-server,llama-cli")
    result["test_target"] = raw.get("test_target", "")
    result["layer"] = raw.get("layer", "base")
    result["smoke_test"] = raw.get("smoke_test", "")
    result["status"] = raw.get("status", "active")

    # Nullable strings
    result["parent"] = _coerce_nullable_string(raw.get("parent", ""))
    result["upstream_ref"] = _coerce_nullable_string(raw.get("upstream_ref", ""))
    result["skip_reason"] = _coerce_nullable_string(raw.get("skip_reason", ""))

    # Booleans
    result["ci_capable"] = _coerce_bool(raw.get("ci_capable", "true"))
    result["ci_compile_capable"] = _coerce_bool(raw.get("ci_compile_capable", "true"))
    result["ci_test_capable"] = _coerce_bool(raw.get("ci_test_capable", "false"))
    result["is_llama_cpp_fork"] = _coerce_bool(raw.get("is_llama_cpp_fork", "true"))

    # Repos (CSV)
    result["repos"] = _coerce_repos(raw.get("repos", ""))

    return result
