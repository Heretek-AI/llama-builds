"""Integration tests for build action and matrix workflow.

These tests validate that the real targets directory and manifest.json
are consistent and conform to the expected schema.
"""

import json
from pathlib import Path

from scripts.metadata_parser import parse_metadata

VALID_BACKENDS = {"cpu", "cuda", "rocm", "vulkan"}


def test_all_targets_have_required_metadata() -> None:
    """Verify all real targets have required METADATA fields."""
    targets_dir = Path("targets")
    if not targets_dir.exists():
        return  # Skip if not in repo root

    for build_sh in targets_dir.glob("*/build.sh"):
        if build_sh.parent.name.startswith("_"):
            continue
        meta = parse_metadata(build_sh)
        assert "name" in meta, f"{build_sh} missing name"
        assert "repo" in meta, f"{build_sh} missing repo"
        assert "ref" in meta, f"{build_sh} missing ref"
        assert "backend" in meta, f"{build_sh} missing backend"
        assert meta["backend"] in VALID_BACKENDS, (
            f"{build_sh} has invalid backend: {meta['backend']}"
        )


def test_manifest_entry_matches_schema() -> None:
    """Verify manifest entry structure matches schema requirements."""
    manifest_path = Path("manifest.json")
    if not manifest_path.exists():
        return  # Skip if manifest not generated

    with open(manifest_path) as f:
        manifest = json.load(f)

    assert manifest["version"] == 3
    for target_name, target in manifest["targets"].items():
        assert "name" in target, f"{target_name} missing name"
        assert "repo" in target, f"{target_name} missing repo"
        assert "ref" in target, f"{target_name} missing ref"
        assert "backend" in target, f"{target_name} missing backend"
        assert "version" in target, f"{target_name} missing version"
        assert "build" in target, f"{target_name} missing build"
        assert "artifact" in target["build"], f"{target_name} missing build.artifact"
