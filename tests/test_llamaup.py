"""Tests for llamaup binary distribution CLI (#58)."""

import json
from pathlib import Path


class TestGpuMap:
    """Validate GPU map configuration."""

    def test_gpu_map_exists(self):
        """configs/gpu_map.json should exist."""
        gpu_map_path = Path("configs/gpu_map.json")
        assert gpu_map_path.exists(), "configs/gpu_map.json must exist"

    def test_gpu_map_valid_json(self):
        """gpu_map.json should be valid JSON."""
        gpu_map_path = Path("configs/gpu_map.json")
        data = json.loads(gpu_map_path.read_text())
        assert isinstance(data, dict)

    def test_gpu_map_has_default(self):
        """gpu_map.json should have a default fallback."""
        gpu_map_path = Path("configs/gpu_map.json")
        data = json.loads(gpu_map_path.read_text())
        assert "default" in data, "gpu_map.json must have a 'default' key"

    def test_gpu_map_targets_exist(self):
        """All target slugs in gpu_map should exist in targets/."""
        gpu_map_path = Path("configs/gpu_map.json")
        data = json.loads(gpu_map_path.read_text())
        targets_dir = Path("targets")
        for key, slug in data.items():
            if key == "default":
                continue
            build_sh = targets_dir / slug / "build.sh"
            assert build_sh.exists(), f"Target {slug} referenced in gpu_map but not found"

    def test_gpu_map_compute_caps(self):
        """gpu_map should cover common compute capabilities."""
        gpu_map_path = Path("configs/gpu_map.json")
        data = json.loads(gpu_map_path.read_text())
        # Should have entries for 8.0, 8.6, 8.9, 9.0
        assert "8.0" in data, "Missing compute capability 8.0 (A100)"
        assert "8.6" in data, "Missing compute capability 8.6 (RTX 30xx)"
        assert "8.9" in data, "Missing compute capability 8.9 (RTX 40xx)"
        assert "9.0" in data, "Missing compute capability 9.0 (H100)"
