"""Tests for CUDA target expansion (#64)."""

from pathlib import Path

import pytest

from scripts.generate_manifest import extract_metadata, generate_manifest


class TestUpstreamCudaUniversal:
    """Validate upstream-cuda is now a universal build."""

    def test_upstream_cuda_name_updated(self):
        """upstream-cuda should be named 'universal' not 'sm_89/90a'."""
        build_sh = Path("targets/upstream-cuda/build.sh")
        meta = extract_metadata(build_sh)
        assert meta is not None
        assert "universal" in meta["name"].lower()

    def test_upstream_cuda_no_explicit_architectures(self):
        """upstream-cuda build.sh should not hardcode CMAKE_CUDA_ARCHITECTURES."""
        build_sh = Path("targets/upstream-cuda/build.sh")
        content = build_sh.read_text()
        # The build script should NOT contain explicit architecture specification
        # in the cmake command (it should use llama.cpp's defaults)
        assert (
            "CMAKE_CUDA_ARCHITECTURES" not in content
            or content.count("CMAKE_CUDA_ARCHITECTURES") == 0
        )

    def test_upstream_cuda_metadata_fields(self):
        """upstream-cuda should have correct METADATA fields."""
        build_sh = Path("targets/upstream-cuda/build.sh")
        meta = extract_metadata(build_sh)
        assert meta is not None
        assert meta["backend"] == "cuda"
        assert meta["arch"] == "x86_64"
        assert "chat" in meta["capabilities"]
        assert "embed" in meta["capabilities"]


class TestSmSpecificTargets:
    """Validate SM-specific CUDA targets exist with correct metadata."""

    SM_TARGETS = {
        "upstream-cuda-sm80": {"sm": "80", "name_part": "sm_80"},
        "upstream-cuda-sm86": {"sm": "86", "name_part": "sm_86"},
        "upstream-cuda-sm89": {"sm": "89", "name_part": "sm_89"},
        "upstream-cuda-sm90": {"sm": "90", "name_part": "sm_90"},
    }

    @pytest.mark.parametrize("slug,info", SM_TARGETS.items())
    def test_target_build_sh_exists(self, slug, info):
        """Each SM target should have a build.sh file."""
        build_sh = Path(f"targets/{slug}/build.sh")
        assert build_sh.exists(), f"{slug}/build.sh must exist"

    @pytest.mark.parametrize("slug,info", SM_TARGETS.items())
    def test_metadata_name_contains_sm(self, slug, info):
        """METADATA name should reference the SM version."""
        build_sh = Path(f"targets/{slug}/build.sh")
        meta = extract_metadata(build_sh)
        assert meta is not None
        assert info["name_part"] in meta["name"]

    @pytest.mark.parametrize("slug,info", SM_TARGETS.items())
    def test_metadata_backend_cuda(self, slug, info):
        """All SM targets should be cuda backend."""
        build_sh = Path(f"targets/{slug}/build.sh")
        meta = extract_metadata(build_sh)
        assert meta["backend"] == "cuda"

    @pytest.mark.parametrize("slug,info", SM_TARGETS.items())
    def test_extra_cmake_flags_set(self, slug, info):
        """extra_cmake_flags should specify the SM architecture."""
        build_sh = Path(f"targets/{slug}/build.sh")
        meta = extract_metadata(build_sh)
        assert meta is not None
        assert f"CMAKE_CUDA_ARCHITECTURES={info['sm']}" in meta["extra_cmake_flags"]

    @pytest.mark.parametrize("slug,info", SM_TARGETS.items())
    def test_target_appears_in_manifest(self, slug, info):
        """Each SM target should appear in the generated manifest."""
        manifest = generate_manifest(targets_dir=Path("targets"))
        assert slug in manifest["targets"], f"{slug} missing from manifest"

    @pytest.mark.parametrize("slug,info", SM_TARGETS.items())
    def test_manifest_gpu_target_set(self, slug, info):
        """Manifest entry should have gpu_target set to sm_XX."""
        manifest = generate_manifest(targets_dir=Path("targets"))
        target = manifest["targets"][slug]
        assert target["gpu_target"] == f"sm_{info['sm']}"
