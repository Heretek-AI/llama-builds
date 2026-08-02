"""Tests for the build target template."""

import re
from pathlib import Path

TEMPLATE_PATH = Path("targets/_template/build.sh")
METADATA_HEADER = "# METADATA"
METADATA_PATTERN = re.compile(r"^#\s+(\w+)=(.+)$")


def extract_metadata(build_sh: Path) -> dict | None:
    """Minimal METADATA extractor (mirrors scripts/generate_manifest.py)."""
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
            elif not stripped.startswith("#"):
                break
    if not metadata or "name" not in metadata:
        return None
    caps_raw = metadata.get("capabilities", "")
    metadata["capabilities"] = [c.strip() for c in caps_raw.split(",") if c.strip()]
    return metadata


class TestTemplate:
    """Validate the _template/build.sh contract."""

    def test_template_exists(self):
        assert TEMPLATE_PATH.exists()

    def test_template_has_metadata_block(self):
        meta = extract_metadata(TEMPLATE_PATH)
        assert meta is not None, "Template must have a METADATA block"

    def test_template_metadata_has_all_required_fields(self):
        meta = extract_metadata(TEMPLATE_PATH)
        assert meta is not None
        for field in ["name", "repo", "ref", "backend", "arch", "capabilities"]:
            assert field in meta, f"Template METADATA missing required field: {field}"

    def test_template_metadata_has_placeholder_values(self):
        """Template values should be obviously placeholder-ish."""
        meta = extract_metadata(TEMPLATE_PATH)
        assert meta is not None
        assert "TODO" in meta["name"] or meta["name"] == "Target name"
        assert "/" in meta["repo"]  # must be owner/repo format
