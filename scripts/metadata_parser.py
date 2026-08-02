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
