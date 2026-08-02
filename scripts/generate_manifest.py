"""Scrape targets/*/build.sh header comments and emit manifest.json.

Each target's build.sh must contain a METADATA block:

    # METADATA
    # name=Human-readable name
    # repo=owner/repo
    # ref=<pinned-sha-or-tag>
    # backend=cpu|cuda|rocm|vulkan|docs
    # arch=x86_64|aarch64
    # capabilities=cap1,cap2,...

The script walks targets/*/build.sh, extracts metadata, and emits a
JSON manifest conforming to schemas/manifest.schema.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from datetime import UTC, datetime
from pathlib import Path

from scripts.metadata_common import MetadataParseError, parse_metadata_raw

TARGETS_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def extract_metadata(build_sh: Path) -> dict | None:
    """Extract METADATA block from a build.sh file.

    Returns None if no METADATA header is found.

    This is a backward-compatible wrapper around parse_metadata_raw
    from metadata_common. Returns capabilities as a list (v2 shape).
    """
    try:
        raw = parse_metadata_raw(build_sh)
    except MetadataParseError:
        return None

    # Parse capabilities from comma-separated string
    caps_raw = raw.get("capabilities", "")
    capabilities = [c.strip() for c in caps_raw.split(",") if c.strip()]

    result = {k: v for k, v in raw.items() if k != "capabilities"}
    result["capabilities"] = capabilities
    return result


def _parse_new_fields(raw: dict[str, str]) -> dict:
    """Populate v3 fields from raw METADATA strings with defaults.

    Returns a dict of v3 fields with proper defaults applied.
    """
    return {
        "default_branch": raw.get("default_branch", "main"),
        "gpu_toolchain": raw.get("gpu_toolchain", "none"),
        "extra_cmake_flags": raw.get("extra_cmake_flags", ""),
        "build_system": raw.get("build_system", "cmake"),
        "binary_names": raw.get("binary_names", "llama-server,llama-cli"),
        "test_target": raw.get("test_target", ""),
        "layer": raw.get("layer", "base"),
        "parent": raw.get("parent") or None,
        "ci_capable": _parse_bool(raw.get("ci_capable", "true")),
        "ci_compile_capable": _parse_bool(raw.get("ci_compile_capable", "true")),
        "ci_test_capable": _parse_bool(raw.get("ci_test_capable", "false")),
        "is_llama_cpp_fork": _parse_bool(raw.get("is_llama_cpp_fork", "true")),
        "smoke_test": raw.get("smoke_test", ""),
        "upstream_ref": raw.get("upstream_ref") or None,
        "status": raw.get("status", "active"),
        "skip_reason": raw.get("skip_reason") or None,
        "repos": [r.strip() for r in raw.get("repos", "").split(",") if r.strip()],
    }


def _parse_bool(value: str) -> bool:
    """Coerce string to bool."""
    return value.lower() in ("true", "1", "yes")


def _validate_parent(targets_dir: Path, slug: str, parent: str | None) -> str | None:
    """Check that parent target exists. Returns error string or None."""
    if parent is None:
        return None
    parent_build_sh = targets_dir / parent / "build.sh"
    if not parent_build_sh.exists():
        return f"Target '{slug}' references parent '{parent}' but it does not exist"
    return None


def _detect_cycle(targets_dir: Path, slug: str) -> bool:
    """Check if a parent chain from slug would form a cycle."""
    visited: set[str] = {slug}
    current = slug

    while True:
        build_sh = targets_dir / current / "build.sh"
        if not build_sh.exists():
            return False
        try:
            raw = parse_metadata_raw(build_sh)
        except MetadataParseError:
            return False
        parent = raw.get("parent") or None
        if parent is None:
            return False
        if parent in visited:
            return True
        visited.add(parent)
        current = parent


def generate_manifest(targets_dir: Path, repo_root: Path | None = None) -> dict:
    """Walk targets_dir and build a manifest dict."""
    if repo_root is None:
        repo_root = targets_dir.parent

    targets: dict[str, dict] = {}

    if not targets_dir.is_dir():
        return {
            "version": 3,
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

        # Parse v3 fields
        new_fields = _parse_new_fields(meta)

        # Validate parent references
        parent_err = _validate_parent(targets_dir, slug, new_fields["parent"])
        if parent_err:
            warnings.warn(parent_err, stacklevel=2)

        if _detect_cycle(targets_dir, slug):
            warnings.warn(
                f"Target '{slug}' has a parent cycle — ignoring parent field",
                stacklevel=2,
            )
            new_fields["parent"] = None

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
            # v3 fields
            "default_branch": new_fields["default_branch"],
            "gpu_toolchain": new_fields["gpu_toolchain"],
            "extra_cmake_flags": new_fields["extra_cmake_flags"],
            "build_system": new_fields["build_system"],
            "binary_names": new_fields["binary_names"],
            "test_target": new_fields["test_target"],
            "layer": new_fields["layer"],
            "parent": new_fields["parent"],
            "ci_capable": new_fields["ci_capable"],
            "ci_compile_capable": new_fields["ci_compile_capable"],
            "ci_test_capable": new_fields["ci_test_capable"],
            "is_llama_cpp_fork": new_fields["is_llama_cpp_fork"],
            "smoke_test": new_fields["smoke_test"],
            "upstream_ref": new_fields["upstream_ref"],
            "status": new_fields["status"],
            "skip_reason": new_fields["skip_reason"],
            "repos": new_fields["repos"],
        }

    return {
        "version": 3,
        "generated_at": datetime.now(UTC).isoformat(),
        "targets": targets,
    }


def _runner_for_backend(backend: str) -> str:
    """Map backend to a GitHub Actions runner label."""
    runners = {
        "cpu": "ubuntu-latest",
        "cuda": "ubuntu-latest",
        "rocm": "ubuntu-latest",
        "vulkan": "ubuntu-latest",
        "docs": "ubuntu-latest",
    }
    return runners.get(backend, "ubuntu-latest")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate manifest.json from targets/*/build.sh metadata"
    )
    parser.add_argument(
        "--targets-dir",
        type=Path,
        default=Path("targets"),
        help="Path to targets directory (default: targets/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("manifest.json"),
        help="Output manifest path (default: manifest.json)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: auto-detect from targets dir parent)",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root or args.targets_dir.parent
    manifest = generate_manifest(targets_dir=args.targets_dir, repo_root=repo_root)

    args.output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Manifest written to {args.output} ({len(manifest['targets'])} targets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
