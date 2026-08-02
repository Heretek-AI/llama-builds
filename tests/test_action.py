"""Tests for action.yml — validates composite action metadata."""

from pathlib import Path

import pytest
import yaml

ACTION_PATH = Path("action.yml")


class TestActionStructure:
    """Validate action.yml is well-formed."""

    @pytest.fixture(autouse=True)
    def _load_action(self):
        self.action = yaml.safe_load(ACTION_PATH.read_text())

    def test_action_exists(self):
        assert ACTION_PATH.exists()

    def test_name(self):
        assert self.action["name"] == "Build llama.cpp"

    def test_is_composite(self):
        assert self.action["runs"]["using"] == "composite"

    def test_has_required_inputs(self):
        inputs = self.action["inputs"]
        assert "repo" in inputs
        assert "ref" in inputs
        assert "backend" in inputs

    def test_repo_input_required(self):
        assert self.action["inputs"]["repo"]["required"] is True

    def test_ref_input_required(self):
        assert self.action["inputs"]["ref"]["required"] is True

    def test_backend_input_required(self):
        assert self.action["inputs"]["backend"]["required"] is True

    def test_backend_input_description_mentions_options(self):
        desc = self.action["inputs"]["backend"]["description"]
        assert "cpu" in desc.lower()
        assert "cuda" in desc.lower()
        assert "rocm" in desc.lower()
        assert "vulkan" in desc.lower()

    def test_has_all_outputs(self):
        outputs = self.action["outputs"]
        assert "artifact_path" in outputs
        assert "manifest_entry" in outputs
        assert "resolved_sha" in outputs
        assert "version_tag" in outputs

    def test_default_arch_is_x86_64(self):
        assert self.action["inputs"]["arch"]["default"] == "x86_64"

    def test_default_build_type_is_release(self):
        assert self.action["inputs"]["build_type"]["default"] == "Release"
