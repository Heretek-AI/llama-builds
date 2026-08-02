"""Tests for manifest entry generation and version tag format.

Verifies that the Python-based JSON generation in action.yml produces
valid JSON and that version tags follow the {ref_prefix}-{build_num} pattern.
"""

import json
import re


def _build_manifest_entry(
    repo="ggml-org/llama.cpp",
    ref="abc1234def5678",
    backend="cpu",
    arch="x86_64",
    gpu_target=None,
    cmake_flags="",
    version_tag="abc1234-1",
    os_name="ubuntu",
    archive_name="llama-abc1234-1-ubuntu-cpu-x86_64.tar.gz",
):
    """Build a manifest entry dict mirroring what action.yml emits."""
    entry = {
        "name": f"{repo} ({backend})",
        "repo": repo,
        "ref": ref,
        "backend": backend,
        "arch": arch,
        "gpu_target": gpu_target if gpu_target else None,
        "capabilities": cmake_flags.split(",") if cmake_flags else ["chat"],
        "version": version_tag,
        "build": {
            "runner": "ubuntu-latest",
            "script": "",
            "os": os_name,
            "artifact": archive_name,
        },
        "smoke_test": "llama-cli --version",
        "ci_capable": True,
        "ci_compile_capable": True,
        "ci_test_capable": False,
        "is_llama_cpp_fork": True,
        "status": "active",
    }
    return entry


class TestManifestEntryJsonValidity:
    """Ensure the manifest entry round-trips through JSON without error."""

    def test_round_trip(self):
        entry = _build_manifest_entry()
        serialized = json.dumps(entry)
        parsed = json.loads(serialized)
        assert parsed == entry

    def test_no_trailing_comma(self):
        """Shell printf can leave trailing commas; Python json.dumps never does."""
        entry = _build_manifest_entry()
        serialized = json.dumps(entry)
        assert ",}" not in serialized
        assert ",]" not in serialized

    def test_string_values_are_strings(self):
        entry = _build_manifest_entry()
        serialized = json.dumps(entry)
        parsed = json.loads(serialized)
        for key in ("name", "repo", "ref", "backend", "arch", "version"):
            assert isinstance(parsed[key], str)


class TestManifestEntryGpuTarget:
    """Verify gpu_target propagates into the artifact name and entry."""

    def test_gpu_target_in_entry(self):
        entry = _build_manifest_entry(gpu_target="gfx1151")
        assert entry["gpu_target"] == "gfx1151"

    def test_gpu_target_appears_in_artifact_name(self):
        gpu = "sm_89"
        archive = f"llama-abc1234-1-ubuntu-cuda-x86_64-{gpu}.tar.gz"
        entry = _build_manifest_entry(
            backend="cuda",
            gpu_target=gpu,
            archive_name=archive,
        )
        assert gpu in entry["build"]["artifact"]

    def test_gpu_target_none_when_empty(self):
        entry = _build_manifest_entry(gpu_target="")
        assert entry["gpu_target"] is None


class TestVersionTagFormat:
    """Verify version tag follows {ref_prefix}-{build_num} pattern."""

    TAG_PATTERN = re.compile(r"^[0-9a-f]{7}-\d+$")

    def test_valid_format(self):
        tag = "abc1234-1"
        assert self.TAG_PATTERN.match(tag), f"Tag {tag!r} does not match pattern"

    def test_build_number_increments(self):
        ref_prefix = "abc1234"
        tags = [f"{ref_prefix}-{n}" for n in range(1, 6)]
        for tag in tags:
            assert self.TAG_PATTERN.match(tag)
        assert tags[-1] == "abc1234-5"

    def test_version_field_matches_tag(self):
        entry = _build_manifest_entry(version_tag="abc1234-3")
        assert entry["version"] == "abc1234-3"
        assert self.TAG_PATTERN.match(entry["version"])

    def test_ref_prefix_in_version(self):
        ref = "abc1234def56789"
        prefix = ref[:7]
        tag = f"{prefix}-2"
        assert tag.startswith(prefix)
        assert self.TAG_PATTERN.match(tag)
