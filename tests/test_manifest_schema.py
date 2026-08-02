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
        "version": 3,
        "generated_at": "2026-08-02T00:00:00Z",
        "targets": {},
    }


@pytest.fixture
def manifest_with_target():
    """Manifest with one realistic target entry."""
    return {
        "version": 3,
        "generated_at": "2026-08-02T00:00:00Z",
        "targets": {
            "cpu": {
                "name": "llama.cpp CPU baseline",
                "repo": "ggml-org/llama.cpp",
                "ref": "abc1234def5678",
                "backend": "cpu",
                "arch": "x86_64",
                "gpu_target": None,
                "capabilities": ["chat", "embed"],
                "version": "abc1234-1",
                "build": {
                    "runner": "ubuntu-latest",
                    "script": "targets/upstream-cpu/build.sh",
                    "os": "ubuntu",
                    "artifact": "llama-abc1234-1-ubuntu-cpu-x86_64.tar.gz",
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
        golden_manifest["version"] = 1
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


class TestSchemaV2Fields:
    """Validate new fields added in schema version 2."""

    @pytest.fixture(autouse=True)
    def _load_jsonschema(self):
        jsonschema = pytest.importorskip("jsonschema")
        self.validate = jsonschema.validate
        self.ValidationError = jsonschema.ValidationError

    def test_version_bumped_to_3(self, schema):
        assert schema["properties"]["version"]["const"] == 3

    def test_gpu_target_field_exists(self, schema):
        target_schema = schema["$defs"]["target"]
        assert "gpu_target" in target_schema["properties"]

    def test_gpu_target_accepts_string(self, schema, manifest_with_target):
        manifest_with_target["targets"]["cpu"]["gpu_target"] = "gfx1151"
        self.validate(instance=manifest_with_target, schema=schema)

    def test_gpu_target_accepts_null(self, schema, manifest_with_target):
        manifest_with_target["targets"]["cpu"]["gpu_target"] = None
        self.validate(instance=manifest_with_target, schema=schema)

    def test_build_os_field_exists(self, schema):
        target_schema = schema["$defs"]["target"]
        assert "os" in target_schema["properties"]["build"]["properties"]

    def test_build_artifact_field_exists(self, schema):
        target_schema = schema["$defs"]["target"]
        assert "artifact" in target_schema["properties"]["build"]["properties"]

    def test_full_v2_manifest_validates(self, schema):
        manifest = {
            "version": 3,
            "generated_at": "2026-08-02T00:00:00Z",
            "targets": {
                "cpu": {
                    "name": "llama.cpp CPU baseline",
                    "repo": "ggml-org/llama.cpp",
                    "ref": "abc1234def5678",
                    "backend": "cpu",
                    "arch": "x86_64",
                    "gpu_target": None,
                    "capabilities": ["chat", "embed"],
                    "version": "abc1234-1",
                    "build": {
                        "runner": "ubuntu-latest",
                        "script": "targets/upstream-cpu/build.sh",
                        "os": "ubuntu",
                        "artifact": "llama-abc1234-1-ubuntu-cpu-x86_64.tar.gz",
                    },
                }
            },
        }
        self.validate(instance=manifest, schema=schema)
