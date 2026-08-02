"""Tests for audit_matrix.py — validates manifest vs targets/ + schema."""

import json
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.audit_matrix import audit_manifest, audit_targets_dir


@pytest.fixture
def schema():
    return json.loads(Path("schemas/manifest.schema.json").read_text())


@pytest.fixture
def valid_manifest():
    return {
        "version": 2,
        "generated_at": "2026-08-02T00:00:00Z",
        "targets": {
            "cpu": {
                "name": "llama.cpp CPU",
                "repo": "ggml-org/llama.cpp",
                "ref": "abc1234def5678",
                "backend": "cpu",
                "arch": "x86_64",
                "gpu_target": None,
                "capabilities": ["chat"],
                "version": "abc1234-1",
                "build": {
                    "runner": "ubuntu-latest",
                    "script": "targets/cpu/build.sh",
                    "os": "ubuntu",
                    "artifact": "llama-abc1234-1-ubuntu-cpu-x86_64.tar.gz",
                },
            }
        },
    }


METADATA_BLOCK = textwrap.dedent("""\
    #!/usr/bin/env bash
    # METADATA
    # name=Test target
    # repo=owner/repo
    # ref=abc1234def5678
    # backend=cpu
    # arch=x86_64
    # capabilities=chat
    set -euo pipefail
    echo "build"
""")


class TestAuditManifest:
    def test_valid_manifest_passes(self, valid_manifest, schema):
        errors = audit_manifest(valid_manifest, schema)
        assert errors == []

    def test_missing_version_fails(self, valid_manifest, schema):
        del valid_manifest["version"]
        errors = audit_manifest(valid_manifest, schema)
        assert any("version" in e for e in errors)

    def test_invalid_backend_fails(self, valid_manifest, schema):
        valid_manifest["targets"]["cpu"]["backend"] = "tpu"
        errors = audit_manifest(valid_manifest, schema)
        assert len(errors) > 0, "Expected schema validation error for invalid backend"


class TestAuditTargetsDir:
    def test_matching_target_and_build_sh(self, valid_manifest, tmp_path):
        targets_dir = tmp_path / "targets"
        target_dir = targets_dir / "cpu"
        target_dir.mkdir(parents=True)
        (target_dir / "build.sh").write_text(METADATA_BLOCK)

        errors = audit_targets_dir(targets_dir, valid_manifest)
        assert errors == []

    def test_manifest_target_missing_build_sh(self, valid_manifest, tmp_path):
        targets_dir = tmp_path / "targets"
        targets_dir.mkdir()

        errors = audit_targets_dir(targets_dir, valid_manifest)
        assert any("no build.sh" in e.lower() for e in errors)

    def test_build_sh_without_manifest_entry(self, tmp_path):
        targets_dir = tmp_path / "targets"
        target_dir = targets_dir / "orphan"
        target_dir.mkdir(parents=True)
        (target_dir / "build.sh").write_text(METADATA_BLOCK)

        manifest = {
            "version": 2,
            "generated_at": "2026-08-02T00:00:00Z",
            "targets": {},
        }
        errors = audit_targets_dir(targets_dir, manifest)
        assert any("no manifest entry" in e.lower() for e in errors)

    def test_empty_dirs_and_manifest_pass(self, tmp_path):
        targets_dir = tmp_path / "targets"
        targets_dir.mkdir()
        manifest = {
            "version": 2,
            "generated_at": "2026-08-02T00:00:00Z",
            "targets": {},
        }
        errors = audit_targets_dir(targets_dir, manifest)
        assert errors == []

    def test_build_sh_without_metadata_skipped(self, tmp_path):
        targets_dir = tmp_path / "targets"
        target_dir = targets_dir / "no-meta"
        target_dir.mkdir(parents=True)
        (target_dir / "build.sh").write_text("#!/usr/bin/env bash\necho 'no metadata'\n")

        manifest = {
            "version": 2,
            "generated_at": "2026-08-02T00:00:00Z",
            "targets": {
                "no-meta": {
                    "name": "test",
                    "repo": "o/r",
                    "ref": "abc12345",
                    "backend": "cpu",
                    "arch": "x86_64",
                    "gpu_target": None,
                    "capabilities": ["chat"],
                    "version": "abc1234-1",
                    "build": {
                        "runner": "ubuntu-latest",
                        "script": "targets/no-meta/build.sh",
                        "os": "ubuntu",
                        "artifact": "",
                    },
                }
            },
        }
        errors = audit_targets_dir(targets_dir, manifest)
        assert any("no build.sh with metadata" in e.lower() for e in errors)
