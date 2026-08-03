"""Tests for llamaup binary distribution CLI (#58)."""

import json
import subprocess
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


class TestLlamaup:
    """Validate llamaup script."""

    def test_llamaup_exists(self):
        """scripts/llamaup should exist."""
        llamaup = Path("scripts/llamaup")
        assert llamaup.exists(), "scripts/llamaup must exist"

    def test_llamaup_executable(self):
        """scripts/llamaup should be executable."""
        llamaup = Path("scripts/llamaup")
        assert llamaup.stat().st_mode & 0o111, "scripts/llamaup must be executable"

    def test_llamaup_has_shebang(self):
        """scripts/llamaup should have a shebang line."""
        llamaup = Path("scripts/llamaup")
        first_line = llamaup.read_text().splitlines()[0]
        assert first_line.startswith("#!/"), "scripts/llamaup must start with shebang"

    def test_llamaup_help_flag(self):
        """scripts/llamaup --help should print usage."""
        llamaup = Path("scripts/llamaup")
        content = llamaup.read_text()
        assert "--help" in content or "-h" in content, "llamaup should support --help"

    def test_llamaup_list_flag(self):
        """scripts/llamaup should support --list flag."""
        llamaup = Path("scripts/llamaup")
        content = llamaup.read_text()
        assert "--list" in content, "llamaup should support --list"

    def test_llamaup_dry_run_flag(self):
        """scripts/llamaup should support --dry-run flag."""
        llamaup = Path("scripts/llamaup")
        content = llamaup.read_text()
        assert "--dry-run" in content, "llamaup should support --dry-run"


class TestLlamaupBehavior:
    """Behavioral tests that execute the llamaup script."""

    SCRIPT = Path("scripts/llamaup")

    def _run(self, *args, env_overrides=None, check=False):
        """Run llamaup with optional env overrides, return CompletedProcess."""
        env = {**dict(__import__("os").environ), "LLAMAUP_MANIFEST_URL": "about:blank"}
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            ["bash", str(self.SCRIPT), *args],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )

    def test_help_exits_zero(self):
        """llamaup --help should exit 0 and print usage."""
        result = self._run("--help")
        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    def test_version_missing_argument(self):
        """llamaup --version (no value) should error, not crash with unbound variable."""
        result = self._run("--version")
        assert result.returncode != 0, "Should fail when --version has no argument"
        assert "$2" not in (result.stderr + result.stdout), (
            "Should not expose unbound variable $2 to user"
        )

    def test_version_next_flag_not_consumed(self):
        """llamaup --version --list should error (not consume --list as version)."""
        result = self._run("--version", "--list")
        assert result.returncode != 0

    def test_unknown_option_exits_nonzero(self):
        """llamaup --bogus should exit non-zero."""
        result = self._run("--bogus")
        assert result.returncode != 0

    def test_list_builds_jq_syntax(self):
        """llamaup --list should not produce jq parse errors."""
        manifest_path = Path("manifest.json")
        if not manifest_path.exists():
            import pytest

            pytest.skip("manifest.json not found locally")
        result = self._run(
            "--list",
            env_overrides={"LLAMAUP_MANIFEST_URL": str(manifest_path.resolve())},
        )
        # jq errors go to stderr; a syntax error would show "parse error"
        assert "parse error" not in result.stderr.lower(), (
            f"jq parse error in --list output: {result.stderr}"
        )

    def test_no_exit_trap_in_download_artifact(self):
        """download_artifact must not register an EXIT trap (was deleting the file)."""
        content = self.SCRIPT.read_text()
        # Find the download_artifact function body
        in_func = False
        func_lines = []
        for line in content.splitlines():
            if line.startswith("download_artifact()"):
                in_func = True
            if in_func:
                func_lines.append(line)
                if line.strip() == "}" and len(func_lines) > 1:
                    break
        func_body = "\n".join(func_lines)
        assert "trap" not in func_body, (
            "download_artifact() must not use trap — cleanup happens in main()"
        )

    def test_sha256_verify_function_exists(self):
        """verify_sha256 function must be defined in the script."""
        content = self.SCRIPT.read_text()
        assert "verify_sha256()" in content, "verify_sha256 function must exist"

    def test_amd_targets_rocm(self):
        """AMD GPU fallback should target upstream-rocm, not upstream-cuda."""
        content = self.SCRIPT.read_text()
        assert "upstream-rocm" in content, "AMD path must reference upstream-rocm"
        # Ensure the AMD branch does not still say upstream-cuda
        in_amd_block = False
        for line in content.splitlines():
            if "detect_amd_gpu" in line and "elif" in line:
                in_amd_block = True
            if in_amd_block and "target_slug=" in line:
                assert "upstream-rocm" in line, (
                    f"AMD fallback should be upstream-rocm, got: {line.strip()}"
                )
                break

    def test_no_gpu_targets_cpu(self):
        """No-GPU fallback should target upstream-cpu, not upstream-cuda."""
        content = self.SCRIPT.read_text()
        in_nogpu_block = False
        for line in content.splitlines():
            if "No GPU detected" in line:
                in_nogpu_block = True
            if in_nogpu_block and "target_slug=" in line:
                assert "upstream-cpu" in line, (
                    f"No-GPU fallback should be upstream-cpu, got: {line.strip()}"
                )
                break
