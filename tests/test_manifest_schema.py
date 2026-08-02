"""Tests for manifest.schema.json — validates the schema itself and golden fixtures."""

import json
from pathlib import Path

import pytest

SCHEMA_PATH = Path("schemas/manifest.schema.json")


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture
def golden_manifest():
    """Minimal valid manifest with no targets (empty targets tree)."""
    return {
        "version": 1,
        "generated_at": "2026-08-02T00:00:00Z",
        "targets": {},
    }


@pytest.fixture
def manifest_with_target():
    """Manifest with one realistic target entry."""
    return {
        "version": 1,
        "generated_at": "2026-08-02T00:00:00Z",
        "targets": {
            "cpu": {
                "name": "llama.cpp CPU baseline",
                "repo": "ggml-org/llama.cpp",
                "ref": "abc1234def5678",
                "backend": "cpu",
                "arch": "x86_64",
                "capabilities": ["chat", "embed"],
                "build": {
                    "runner": "ubuntu-latest",
                    "script": "targets/cpu/build.sh",
                },
            }
        },
    }


class TestSchemaStructure:
    """Validate the schema itself is well-formed."""

    def test_schema_is_valid_json(self, schema):
        assert isinstance(schema, dict)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_schema_requires_version(self, schema):
        assert "version" in schema["required"]

    def test_schema_requires_targets(self, schema):
        assert "targets" in schema["required"]

    def test_schema_requires_generated_at(self, schema):
        assert "generated_at" in schema["required"]

    def test_schema_additional_properties_false(self, schema):
        assert schema.get("additionalProperties") is False


class TestGoldenManifest:
    """Validate golden fixtures against the schema."""

    @pytest.fixture(autouse=True)
    def _load_jsonschema(self):
        jsonschema = pytest.importorskip("jsonschema")
        self.validate = jsonschema.validate
        self.ValidationError = jsonschema.ValidationError

    def test_empty_manifest_validates(self, schema, golden_manifest):
        self.validate(instance=golden_manifest, schema=schema)

    def test_manifest_with_target_validates(self, schema, manifest_with_target):
        self.validate(instance=manifest_with_target, schema=schema)

    def test_missing_version_rejects(self, schema, golden_manifest):
        del golden_manifest["version"]
        with pytest.raises(self.ValidationError):
            self.validate(instance=golden_manifest, schema=schema)

    def test_wrong_version_rejects(self, schema, golden_manifest):
        golden_manifest["version"] = 2
        with pytest.raises(self.ValidationError):
            self.validate(instance=golden_manifest, schema=schema)

    def test_extra_top_level_field_rejects(self, schema, golden_manifest):
        golden_manifest["unexpected"] = "nope"
        with pytest.raises(self.ValidationError):
            self.validate(instance=golden_manifest, schema=schema)

    def test_invalid_backend_rejects(self, schema, manifest_with_target):
        manifest_with_target["targets"]["cpu"]["backend"] = "tpu"
        with pytest.raises(self.ValidationError):
            self.validate(instance=manifest_with_target, schema=schema)

    def test_empty_capabilities_rejects(self, schema, manifest_with_target):
        manifest_with_target["targets"]["cpu"]["capabilities"] = []
        with pytest.raises(self.ValidationError):
            self.validate(instance=manifest_with_target, schema=schema)

    def test_invalid_target_name_rejects(self, schema, manifest_with_target):
        manifest_with_target["targets"]["UPPER_CASE"] = manifest_with_target["targets"].pop("cpu")
        with pytest.raises(self.ValidationError):
            self.validate(instance=manifest_with_target, schema=schema)
