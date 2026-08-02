"""Parse METADATA headers from target build.sh files."""

from __future__ import annotations

import re
from pathlib import Path


class MetadataParseError(Exception):
    """Raised when METADATA block is missing or malformed."""


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
    """
    in_metadata = False
    raw: dict[str, str] = {}

    for line in build_sh.read_text().splitlines():
        stripped = line.strip()
        if stripped == "# METADATA":
            in_metadata = True
            continue
        if in_metadata and stripped.startswith("# "):
            match = re.match(r"^#\s*([^=]+)=(.+)$", stripped)
            if match:
                raw[match.group(1).strip()] = match.group(2).strip()
        elif in_metadata and not stripped.startswith("#"):
            break

    if not raw:
        raise MetadataParseError(f"No METADATA block found in {build_sh}")

    # Build result with parsing
    result: dict = {}
    result["name"] = raw.get("name", "")
    result["repo"] = raw.get("repo", "")
    result["ref"] = raw.get("ref", "")
    result["backend"] = raw.get("backend", "")
    result["arch"] = raw.get("arch", DEFAULTS["arch"])

    # CSV fields
    for field in ("capabilities", "gpu_targets", "runtime_deps"):
        val = raw.get(field, "")
        result[field] = [v.strip() for v in val.split(",") if v.strip()] if val else DEFAULTS[field]

    result["bundle_strategy"] = raw.get("bundle_strategy", DEFAULTS["bundle_strategy"])
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
            for family in meta["gpu_targets"]:
                for isa in expand_gpu_family(family):
                    entries.append(
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
