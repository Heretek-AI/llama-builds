"""Parse METADATA headers from target build.sh files.

This module provides the public parse_metadata() API (backward compatible)
and new validation helpers for v3 features. Internally it delegates to
metadata_common for the actual parsing.
"""

from __future__ import annotations

from pathlib import Path

from scripts.metadata_common import (
    MetadataParseError,
    parse_metadata_raw,
    parse_metadata_typed,
)

# Default values for fields that may be absent
DEFAULTS = {
    "arch": "x86_64",
    "capabilities": [],
    "gpu_targets": [],
    "runtime_deps": [],
    "bundle_strategy": "cpu-static",
}


def parse_metadata(build_sh: Path) -> dict:
    """Parse METADATA block from a target build.sh file.

    Returns dict with keys: name, repo, ref, backend, arch, capabilities,
    gpu_targets, runtime_deps, bundle_strategy.

    This is a backward-compatible wrapper around parse_metadata_typed
    from metadata_common.
    """
    typed = parse_metadata_typed(build_sh)

    # Build result matching the original return shape
    result: dict = {}
    result["name"] = typed["name"]
    result["repo"] = typed["repo"]
    result["ref"] = typed["ref"]
    result["backend"] = typed["backend"]
    result["arch"] = typed.get("arch", DEFAULTS["arch"])
    result["capabilities"] = typed.get("capabilities", DEFAULTS["capabilities"])
    result["gpu_targets"] = typed.get("gpu_targets", DEFAULTS["gpu_targets"])
    result["runtime_deps"] = typed.get("runtime_deps", DEFAULTS["runtime_deps"])
    result["bundle_strategy"] = typed.get("bundle_strategy", DEFAULTS["bundle_strategy"])
    return result


# GPU family → individual ISA target mapping
GPU_FAMILIES = {
    "gfx110X": ["gfx1100", "gfx1101", "gfx1102", "gfx1103"],
    "gfx103X": ["gfx1030", "gfx1031", "gfx1032", "gfx1034"],
    "gfx120X": ["gfx1200", "gfx1201"],
}


def expand_gpu_family(family: str) -> list[str]:
    """Expand a GPU family target (e.g. gfx110X) to individual ISA targets."""
    return GPU_FAMILIES.get(family, [family])


def generate_matrix(targets_dir: Path) -> dict:
    """Read all targets/*/build.sh and emit GitHub Actions matrix JSON structure."""
    entries = []
    for build_sh in sorted(targets_dir.glob("*/build.sh")):
        target_name = build_sh.parent.name
        if target_name.startswith("_"):
            continue
        meta = parse_metadata(build_sh)
        if meta["backend"] == "rocm" and meta["gpu_targets"]:
            entries.extend(
                {
                    "target": target_name,
                    "backend": meta["backend"],
                    "arch": meta["arch"],
                    "gfx_target": isa,
                    "repo": meta["repo"],
                    "ref": meta["ref"],
                    "bundle_strategy": meta["bundle_strategy"],
                    "capabilities": meta["capabilities"],
                }
                for family in meta["gpu_targets"]
                for isa in expand_gpu_family(family)
            )
        else:
            entries.append(
                {
                    "target": target_name,
                    "backend": meta["backend"],
                    "arch": meta["arch"],
                    "gfx_target": None,
                    "repo": meta["repo"],
                    "ref": meta["ref"],
                    "bundle_strategy": meta["bundle_strategy"],
                    "capabilities": meta["capabilities"],
                }
            )
    return {"include": entries}


def validate_fork_gate(meta: dict) -> bool:
    """Check if a target qualifies as a llama.cpp fork or derivative.

    Returns True if is_llama_cpp_fork is True OR if the repo name
    contains 'llama'. Returns False otherwise (target is not a fork).
    """
    if meta.get("is_llama_cpp_fork", True):
        return True
    repo = meta.get("repo", "")
    return "llama" in repo.lower()


def validate_parent_chain(
    targets_dir: Path,
    slug: str,
    parent: str | None,
) -> list[str]:
    """Validate the parent reference chain for a target.

    Follows the parent chain from slug upward. Returns a list of error
    strings for:
    - Cycle detection (chain returns to self)
    - Missing parent target (parent has no build.sh)
    - Empty loop (parent points to another parent that loops back)
    """
    errors: list[str] = []
    if parent is None:
        return errors

    visited: set[str] = set()
    current = parent

    while current is not None:
        if current == slug:
            errors.append(f"Target '{slug}' has a parent cycle: parent chain loops back to self")
            break

        if current in visited:
            errors.append(f"Target '{slug}' parent chain has a cycle through '{current}'")
            break

        visited.add(current)

        parent_build_sh = targets_dir / current / "build.sh"
        if not parent_build_sh.exists():
            errors.append(
                f"Target '{slug}' references parent '{current}' "
                f"but targets/{current}/build.sh does not exist"
            )
            break

        # Parse parent to find its parent
        try:
            raw = parse_metadata_raw(parent_build_sh)
            current = raw.get("parent") or None
        except MetadataParseError:
            errors.append(f"Parent target '{current}' has no valid METADATA block")
            break

    return errors
