"""Validate manifest.json against matrix.yml and the JSON schema.

Checks:
1. Manifest conforms to schemas/manifest.schema.json
2. Every manifest target appears in matrix.yml include entries
3. Every matrix entry has a corresponding manifest target (warns on orphans)
4. No matrix entries reference non-existent targets
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

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


def audit_matrix(matrix_yml: str, manifest: dict) -> list[str]:
    """Validate matrix.yml against manifest."""
    errors: list[str] = []
    matrix_targets = _parse_matrix_targets(matrix_yml)
    manifest_targets = set(manifest.get("targets", {}).keys())

    for target in matrix_targets - manifest_targets:
        errors.append(f"Matrix entry '{target}' has no corresponding manifest target")

    for target in manifest_targets - matrix_targets:
        errors.append(f"Manifest target '{target}' not found in matrix.yml (missing entry)")

    return errors


def _parse_matrix_targets(matrix_yml: str) -> set[str]:
    """Extract target slugs from matrix.yml include entries.

    Skips entries with ``disabled: true`` (placeholder GPU entries).
    Handles YAML files with GitHub Actions expressions that may not parse cleanly.
    """
    # Preprocess: remove lines with GH Actions expressions (${{ ... }})
    # that break YAML parsing, but keep the rest of the structure intact.

    cleaned_lines = []
    for line in matrix_yml.splitlines():
        # Skip lines containing ${{ ... }} expressions
        if "${{" in line:
            continue
        cleaned_lines.append(line)
    cleaned_yml = "\n".join(cleaned_lines)

    try:
        data = yaml.safe_load(cleaned_yml)
    except yaml.YAMLError:
        # Still can't parse — return empty set
        return set()

    if data is None:
        return set()

    targets = set()

    jobs = data.get("jobs", {})
    for _job_name, job_def in jobs.items():
        strategy = job_def.get("strategy", {})
        matrix = strategy.get("matrix", {})
        includes = matrix.get("include", [])
        for entry in includes:
            if isinstance(entry, dict) and "target" in entry:
                if entry.get("disabled", False):
                    continue
                targets.add(entry["target"])

    return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate manifest.json against matrix.yml and schema"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("manifest.json"),
        help="Path to manifest.json",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        default=Path(".github/workflows/matrix.yml"),
        help="Path to matrix.yml",
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
    matrix_yml = args.matrix.read_text()

    errors: list[str] = []
    errors.extend(audit_manifest(manifest, schema))
    errors.extend(audit_matrix(matrix_yml, manifest))

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print("Audit passed: manifest and matrix are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
