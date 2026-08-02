"""Tests for audit_matrix.py — validates manifest vs matrix.yml + schema."""

import json
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.audit_matrix import audit_manifest, audit_matrix


@pytest.fixture
def schema():
    return json.loads(Path("schemas/manifest.schema.json").read_text())


@pytest.fixture
def valid_manifest():
    return {
        "version": 1,
        "generated_at": "2026-08-02T00:00:00Z",
        "targets": {
            "cpu": {
                "name": "llama.cpp CPU",
                "repo": "ggml-org/llama.cpp",
                "ref": "abc1234def5678",
                "backend": "cpu",
                "arch": "x86_64",
                "capabilities": ["chat"],
                "build": {
                    "runner": "ubuntu-latest",
                    "script": "targets/cpu/build.sh",
                },
            }
        },
    }


@pytest.fixture
def matrix_yml_cpu_only():
    """matrix.yml with a single CPU entry."""
    return textwrap.dedent("""\
        name: Matrix Build
        on: [push]
        permissions:
          contents: read
        jobs:
          build:
            runs-on: ubuntu-latest
            strategy:
              matrix:
                include:
                  - target: cpu
                    backend: cpu
                    arch: x86_64
    """)


class TestAuditManifest:
    """Validate manifest against schema."""

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

    def test_orphan_manifest_target_warning(self, valid_manifest):
        """Manifest has a target not in matrix — should warn."""
        matrix_yml = textwrap.dedent("""\
            name: Matrix Build
            on: [push]
            permissions:
              contents: read
            jobs:
              build:
                runs-on: ubuntu-latest
                strategy:
                  matrix:
                    include: []
        """)
        errors = audit_matrix(matrix_yml, valid_manifest)
        assert any("not in matrix" in e.lower() or "missing entry" in e.lower() for e in errors)


class TestAuditMatrix:
    """Validate matrix.yml references real targets."""

    def test_matrix_with_valid_entry(self, valid_manifest, matrix_yml_cpu_only):
        errors = audit_matrix(matrix_yml_cpu_only, valid_manifest)
        assert errors == []

    def test_matrix_missing_manifest_target(self, valid_manifest):
        """Matrix doesn't list a target that's in the manifest."""
        matrix_yml = textwrap.dedent("""\
            name: Matrix Build
            on: [push]
            permissions:
              contents: read
            jobs:
              build:
                runs-on: ubuntu-latest
                strategy:
                  matrix:
                    include: []
        """)
        errors = audit_matrix(matrix_yml, valid_manifest)
        assert any("missing" in e.lower() or "not in matrix" in e.lower() for e in errors)

    def test_matrix_empty_passes(self):
        """Empty matrix + empty manifest = no errors."""
        matrix_yml = textwrap.dedent("""\
            name: Matrix Build
            on: [push]
            permissions:
              contents: read
            jobs:
              build:
                runs-on: ubuntu-latest
                strategy:
                  matrix:
                    include: []
        """)
        manifest = {
            "version": 1,
            "generated_at": "2026-08-02T00:00:00Z",
            "targets": {},
        }
        errors = audit_matrix(matrix_yml, manifest)
        assert errors == []
