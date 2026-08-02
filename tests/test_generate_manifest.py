"""Tests for generate_manifest.py — scrapes targets/*/build.sh for metadata."""

import json
import textwrap
from pathlib import Path

import pytest

# Import the module under test
from scripts.generate_manifest import (
    extract_metadata,
    generate_manifest,
)

SCHEMA_PATH = Path("schemas/manifest.schema.json")
TARGETS_DIR = Path("targets")


class TestExtractMetadata:
    """Unit tests for header-comment extraction from build.sh files."""

    def _write_build_sh(self, tmp_path: Path, content: str) -> Path:
        build_sh = tmp_path / "build.sh"
        build_sh.write_text(content)
        return build_sh

    def test_extracts_full_metadata(self, tmp_path):
        content = textwrap.dedent("""\
            #!/usr/bin/env bash
            # METADATA
            # name=llama.cpp CPU baseline
            # repo=ggml-org/llama.cpp
            # ref=abc1234def5678
            # backend=cpu
            # arch=x86_64
            # capabilities=chat,embed
            set -euo pipefail
        """)
        build_sh = self._write_build_sh(tmp_path, content)
        meta = extract_metadata(build_sh)
        assert meta["name"] == "llama.cpp CPU baseline"
        assert meta["repo"] == "ggml-org/llama.cpp"
        assert meta["ref"] == "abc1234def5678"
        assert meta["backend"] == "cpu"
        assert meta["arch"] == "x86_64"
        assert meta["capabilities"] == ["chat", "embed"]

    def test_missing_metadata_header_returns_none(self, tmp_path):
        content = "#!/usr/bin/env bash\nset -euo pipefail\n"
        build_sh = self._write_build_sh(tmp_path, content)
        assert extract_metadata(build_sh) is None

    def test_partial_metadata_still_extracted(self, tmp_path):
        content = textwrap.dedent("""\
            #!/usr/bin/env bash
            # METADATA
            # name=Test Target
            # repo=owner/repo
            # ref=abc1234
            # backend=cuda
            # arch=x86_64
            # capabilities=
        """)
        build_sh = self._write_build_sh(tmp_path, content)
        meta = extract_metadata(build_sh)
        assert meta["name"] == "Test Target"
        assert meta["capabilities"] == []

    def test_capabilities_comma_separated(self, tmp_path):
        content = textwrap.dedent("""\
            #!/usr/bin/env bash
            # METADATA
            # name=Test
            # repo=o/r
            # ref=abc1234
            # backend=cpu
            # arch=x86_64
            # capabilities=chat,embed,trellis,flashmla
        """)
        build_sh = self._write_build_sh(tmp_path, content)
        meta = extract_metadata(build_sh)
        assert meta["capabilities"] == ["chat", "embed", "trellis", "flashmla"]


class TestGenerateManifest:
    """Integration tests for full manifest generation from targets/ tree."""

    def test_empty_targets_tree(self, tmp_path):
        """No targets → valid manifest with empty targets map."""
        targets = tmp_path / "targets"
        targets.mkdir()
        manifest = generate_manifest(targets_dir=targets)
        assert manifest["version"] == 1
        assert manifest["targets"] == {}

    def test_single_target(self, tmp_path):
        """One target with valid metadata → manifest entry created."""
        target_dir = tmp_path / "targets" / "cpu"
        target_dir.mkdir(parents=True)
        build_sh = target_dir / "build.sh"
        build_sh.write_text(
            textwrap.dedent("""\
            #!/usr/bin/env bash
            # METADATA
            # name=llama.cpp CPU baseline
            # repo=ggml-org/llama.cpp
            # ref=abc1234def5678
            # backend=cpu
            # arch=x86_64
            # capabilities=chat,embed
            set -euo pipefail
        """)
        )
        manifest = generate_manifest(targets_dir=tmp_path / "targets")
        assert "cpu" in manifest["targets"]
        assert manifest["targets"]["cpu"]["name"] == "llama.cpp CPU baseline"
        assert manifest["targets"]["cpu"]["build"]["script"] == "targets/cpu/build.sh"

    def test_target_without_metadata_skipped(self, tmp_path):
        """Target with no METADATA block → skipped in manifest."""
        target_dir = tmp_path / "targets" / "empty"
        target_dir.mkdir(parents=True)
        build_sh = target_dir / "build.sh"
        build_sh.write_text("#!/usr/bin/env bash\nset -euo pipefail\n")
        manifest = generate_manifest(targets_dir=tmp_path / "targets")
        assert manifest["targets"] == {}

    def test_multiple_targets(self, tmp_path):
        """Multiple targets → all appear in manifest."""
        for name, backend in [("cpu", "cpu"), ("cuda", "cuda")]:
            target_dir = tmp_path / "targets" / name
            target_dir.mkdir(parents=True)
            build_sh = target_dir / "build.sh"
            build_sh.write_text(
                textwrap.dedent(f"""\
                #!/usr/bin/env bash
                # METADATA
                # name={name} target
                # repo=owner/{name}
                # ref=abc1234
                # backend={backend}
                # arch=x86_64
                # capabilities=chat
                set -euo pipefail
            """)
            )
        manifest = generate_manifest(targets_dir=tmp_path / "targets")
        assert len(manifest["targets"]) == 2
        assert "cpu" in manifest["targets"]
        assert "cuda" in manifest["targets"]

    def test_manifest_validates_against_schema(self, tmp_path):
        """Generated manifest passes JSON Schema validation."""
        jsonschema = pytest.importorskip("jsonschema")
        schema = json.loads(SCHEMA_PATH.read_text())
        manifest = generate_manifest(targets_dir=tmp_path / "targets")
        jsonschema.validate(instance=manifest, schema=schema)
