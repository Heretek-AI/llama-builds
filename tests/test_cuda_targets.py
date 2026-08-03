"""Tests for CUDA target expansion (#64)."""

from pathlib import Path

from scripts.generate_manifest import extract_metadata


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
