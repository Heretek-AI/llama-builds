"""Validate manifest.json against targets/ directory and the JSON schema.

Checks:
1. Manifest conforms to schemas/manifest.schema.json
2. Every manifest target has a corresponding targets/<slug>/build.sh
3. Every targets/<slug>/build.sh with METADATA has a manifest entry
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMA_PATH = Path("schemas/manifest.schema.json")


def audit_manifest(manifest: dict, schema: dict) -> list[str]:
    """Validate manifest against JSON schema."""
    errors: list[str] = []

    # Schema validation
    try:
        import jsonschema

        jsonschema.validate(instance=manifest, schema=schema)
    except ImportError:
        errors.append("jsonschema not installed — skipping schema validation")
    except jsonschema.ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")

    return errors


def audit_targets_dir(targets_dir: Path, manifest: dict) -> list[str]:
    """Validate targets/ directory against manifest.

    Checks that every manifest target has a build.sh and vice versa.
    """
    import re

    errors: list[str] = []
    manifest_targets = set(manifest.get("targets", {}).keys())

    # Discover targets from filesystem
    fs_targets: set[str] = set()
    if targets_dir.is_dir():
        for entry in targets_dir.iterdir():
            if not entry.is_dir():
                continue
            slug = entry.name
            if not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
                continue
            build_sh = entry / "build.sh"
            if build_sh.exists():
                # Check if build.sh has METADATA
                content = build_sh.read_text()
                if "# METADATA" in content:
                    fs_targets.add(slug)

    for target in manifest_targets - fs_targets:
        errors.append(f"Manifest target '{target}' has no build.sh with METADATA in targets/")

    for target in fs_targets - manifest_targets:
        errors.append(
            f"Target '{target}' has build.sh but no manifest entry (run generate_manifest)"
        )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate manifest.json against targets/ and schema"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("manifest.json"),
        help="Path to manifest.json",
    )
    parser.add_argument(
        "--targets-dir",
        type=Path,
        default=Path("targets"),
        help="Path to targets directory",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=SCHEMA_PATH,
        help="Path to manifest.schema.json",
    )
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text())
    schema = json.loads(args.schema.read_text())

    errors: list[str] = []
    errors.extend(audit_manifest(manifest, schema))
    errors.extend(audit_targets_dir(args.targets_dir, manifest))

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print("Audit passed: manifest and targets/ are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
