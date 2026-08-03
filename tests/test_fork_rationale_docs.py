"""Tests for the fork rationale docs wired into METADATA description (lb-0097).

Validates the lb-0097 acceptance criteria:
  - Each Tier-1 fork target has docs/fork-rationale/<target>.md (>=20 lines).
  - manifest.json entry description ends with (rationale: docs/fork-rationale/<target>.md).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGETS_DIR = REPO_ROOT / "targets"
RATIONALE_DIR = REPO_ROOT / "docs" / "fork-rationale"
MANIFEST_PATH = REPO_ROOT / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "manifest.schema.json"

# Tier-1 fork targets = every targets/<slug>/build.sh with
# is_llama_cpp_fork=true AND not _template. Computed from the on-disk state.
TIER_1_TARGETS = sorted(
    d.name
    for d in TARGETS_DIR.iterdir()
    if d.is_dir() and d.name != "_template" and (d / "build.sh").exists()
)


def _read(p: Path) -> str:
    return p.read_text()


def _extract_description(build_sh: Path) -> str:
    """Pull the `# description=...` line from a METADATA block."""
    text = _read(build_sh)
    in_meta = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "# METADATA":
            in_meta = True
            continue
        if in_meta:
            m = re.match(r"^#\s+description=(.*)$", stripped)
            if m:
                return m.group(1).strip()
            elif stripped and not stripped.startswith("#"):
                break
    return ""


class TestSchemaAcceptsDescription:
    def test_schema_has_description_field(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        target_props = schema["$defs"]["target"]["properties"]
        assert "description" in target_props, (
            "manifest.schema.json target definition must allow optional 'description' field"
        )
        desc = target_props["description"]
        assert desc.get("type") == "string", (
            f"description field must be type=string, got {desc.get('type')!r}"
        )


class TestRationaleDocsExist:
    def test_rationale_dir_exists(self):
        assert RATIONALE_DIR.is_dir()

    def test_readme_index_exists(self):
        assert (RATIONALE_DIR / "README.md").exists(), "Missing docs/fork-rationale/README.md"

    def test_each_tier1_target_has_rationale_doc(self):
        for slug in TIER_1_TARGETS:
            doc = RATIONALE_DIR / f"{slug}.md"
            assert doc.exists(), f"Missing rationale doc for {slug}: expected {doc}"

    def test_each_rationale_doc_minimum_size(self):
        for slug in TIER_1_TARGETS:
            doc = RATIONALE_DIR / f"{slug}.md"
            assert doc.exists(), f"{doc} missing"
            line_count = len(doc.read_text().splitlines())
            assert line_count >= 20, (
                f"{doc} has only {line_count} lines; acceptance criterion requires >=20"
            )


class TestMetadataDescriptionLinksRationale:
    def test_each_target_description_ends_with_rationale_link(self):
        for slug in TIER_1_TARGETS:
            build_sh = TARGETS_DIR / slug / "build.sh"
            desc = _extract_description(build_sh)
            expected_suffix = f"(rationale: docs/fork-rationale/{slug}.md)"
            assert desc.endswith(expected_suffix), (
                f"{slug} description must end with {expected_suffix!r}, got: {desc!r}"
            )

    def test_each_target_description_non_empty(self):
        """description must have substantive content before the rationale suffix."""
        for slug in TIER_1_TARGETS:
            build_sh = TARGETS_DIR / slug / "build.sh"
            desc = _extract_description(build_sh)
            tail = f"(rationale: docs/fork-rationale/{slug}.md)"
            assert desc.endswith(tail), f"{slug} desc must end with suffix: {desc!r}"
            prefix = desc[: -len(tail)].strip()
            assert len(prefix) >= 5, (
                f"{slug} description must include substantive rationale prefix, got: {desc!r}"
            )


class TestManifestRegeneratesDescription:
    def test_manifest_loads(self):
        assert MANIFEST_PATH.exists()
        manifest = json.loads(MANIFEST_PATH.read_text())
        assert "targets" in manifest

    def test_each_target_has_description_in_manifest(self):
        manifest = json.loads(MANIFEST_PATH.read_text())
        for slug in TIER_1_TARGETS:
            target = manifest["targets"].get(slug)
            assert target is not None, f"{slug} missing from manifest"
            assert "description" in target, (
                f"manifest.targets.{slug} must include 'description' field"
            )
            desc = target["description"]
            assert desc.endswith(f"(rationale: docs/fork-rationale/{slug}.md)"), (
                f"manifest.targets.{slug}.description must end with rationale link, got: {desc!r}"
            )
