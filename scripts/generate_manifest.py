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

METADATA_HEADER = "# METADATA"
METADATA_PATTERN = re.compile(r"^#\s+(\w+)=(.+)$")
TARGETS_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def extract_metadata(build_sh: Path) -> dict | None:
    """Extract METADATA block from a build.sh file.

    Returns None if no METADATA header is found.
    """
    in_metadata = False
    metadata: dict[str, str] = {}

    for line in build_sh.read_text().splitlines():
        stripped = line.strip()
        if stripped == METADATA_HEADER:
            in_metadata = True
            continue
        if in_metadata:
            match = METADATA_PATTERN.match(stripped)
            if match:
                key, value = match.groups()
                metadata[key] = value.strip()
            elif stripped == "":
                continue  # Skip blank lines within metadata block
            elif not stripped.startswith("#"):
                break  # End of metadata block

    if not metadata or "name" not in metadata:
        return None

    # Parse capabilities from comma-separated string
    caps_raw = metadata.get("capabilities", "")
    metadata["capabilities"] = [c.strip() for c in caps_raw.split(",") if c.strip()]

    return metadata


def generate_manifest(targets_dir: Path, repo_root: Path | None = None) -> dict:
    """Walk targets_dir and build a manifest dict."""
    if repo_root is None:
        repo_root = targets_dir.parent

    targets: dict[str, dict] = {}

    if not targets_dir.is_dir():
        return {
            "version": 2,
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
        }

    return {
        "version": 2,
        "generated_at": datetime.now(UTC).isoformat(),
        "targets": targets,
    }


def _runner_for_backend(backend: str) -> str:
    """Map backend to a GitHub Actions runner label."""
    runners = {
        "cpu": "ubuntu-latest",
        "cuda": "self-hosted",
        "rocm": "self-hosted",
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
