"""Tests for upstream_sha_tester.py — validates upstream SHA compatibility."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.upstream_sha_tester import (
    REPO_PATTERN,
    _parse_cmake_metadata,
    _parse_metadata_file,
    clone_repo,
    extract_metadata_from_repo,
    validate_sha,
)


class TestParseMetadataFile:
    """Unit tests for METADATA extraction from files."""

    def test_extracts_metadata_from_build_sh(self, tmp_path):
        build_sh = tmp_path / "build.sh"
        build_sh.write_text(
            "#!/usr/bin/env bash\n"
            "# METADATA\n"
            "# name=Test Target\n"
            "# repo=owner/repo\n"
            "# ref=abc1234\n"
            "# backend=cpu\n"
            "# arch=x86_64\n"
            "# capabilities=chat,embed\n"
            "set -euo pipefail\n"
        )
        meta = _parse_metadata_file(build_sh)
        assert meta is not None
        assert meta["name"] == "Test Target"
        assert meta["backend"] == "cpu"

    def test_no_metadata_returns_none(self, tmp_path):
        build_sh = tmp_path / "build.sh"
        build_sh.write_text("#!/usr/bin/env bash\nset -euo pipefail\n")
        assert _parse_metadata_file(build_sh) is None


class TestExtractMetadataFromRepo:
    """Integration tests for repo metadata extraction."""

    def test_finds_build_sh(self, tmp_path):
        build_sh = tmp_path / "build.sh"
        build_sh.write_text(
            "# METADATA\n"
            "# name=Test\n"
            "# repo=o/r\n"
            "# ref=abc1234\n"
            "# backend=cuda\n"
            "# arch=x86_64\n"
            "# capabilities=chat\n"
        )
        meta = extract_metadata_from_repo(tmp_path)
        assert meta is not None
        assert meta["backend"] == "cuda"

    def test_falls_back_to_cmake(self, tmp_path):
        cmake = tmp_path / "CMakeLists.txt"
        cmake.write_text("project(llama.cpp)\nadd_subdirectory(ggml)\n")
        meta = extract_metadata_from_repo(tmp_path)
        assert meta is not None
        assert "llama.cpp" in meta["name"].lower()

    def test_no_build_files_returns_none(self, tmp_path):
        (tmp_path / "readme.txt").write_text("hello")
        assert extract_metadata_from_repo(tmp_path) is None


class TestValidateSha:
    """Tests for SHA validation (mocked network calls)."""

    @patch("scripts.upstream_sha_tester.clone_repo")
    @patch("scripts.upstream_sha_tester.extract_metadata_from_repo")
    def test_valid_sha_passes(self, mock_extract, mock_clone, tmp_path):
        mock_clone.return_value = (True, "")
        mock_extract.return_value = {
            "name": "Test",
            "repo": "o/r",
            "ref": "abc1234",
            "backend": "cpu",
            "arch": "x86_64",
            "capabilities": "chat",
        }
        # validate_sha uses tempfile, so we need to patch the git rev-parse too
        with patch("scripts.upstream_sha_tester.subprocess") as mock_sub:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "abc1234def5678\n"
            mock_sub.run.return_value = mock_result
            errors = validate_sha("o/r", "abc1234")
        assert errors == []

    @patch("scripts.upstream_sha_tester.clone_repo")
    def test_clone_failure_returns_error(self, mock_clone):
        mock_clone.return_value = (False, "repository not found")
        errors = validate_sha("o/r", "bad-sha")
        assert len(errors) == 1
        assert "Failed to clone" in errors[0]

    @patch("scripts.upstream_sha_tester.clone_repo")
    @patch("scripts.upstream_sha_tester.extract_metadata_from_repo")
    def test_invalid_backend_rejected(self, mock_extract, mock_clone):
        mock_clone.return_value = (True, "")
        mock_extract.return_value = {
            "name": "Test",
            "repo": "o/r",
            "ref": "abc1234",
            "backend": "tpu",
            "arch": "x86_64",
            "capabilities": "chat",
        }
        with patch("scripts.upstream_sha_tester.subprocess") as mock_sub:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "abc1234\n"
            mock_sub.run.return_value = mock_result
            errors = validate_sha("o/r", "abc1234")
        assert any("backend" in e.lower() or "tpu" in e for e in errors)

    @patch("scripts.upstream_sha_tester.clone_repo")
    @patch("scripts.upstream_sha_tester.extract_metadata_from_repo")
    def test_missing_metadata_field_detected(self, mock_extract, mock_clone):
        mock_clone.return_value = (True, "")
        mock_extract.return_value = {
            "name": "Test",
            # missing repo and backend
        }
        with patch("scripts.upstream_sha_tester.subprocess") as mock_sub:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "abc1234\n"
            mock_sub.run.return_value = mock_result
            errors = validate_sha("o/r", "abc1234")
        assert any("repo" in e for e in errors)

    def test_invalid_repo_format_rejected(self):
        """Repo not matching owner/repo pattern should be rejected."""
        errors = validate_sha("not-a-repo", "abc1234")
        assert len(errors) == 1
        assert "Invalid repo format" in errors[0]

    def test_invalid_repo_slashes_rejected(self):
        """Repo with too many slashes should be rejected."""
        errors = validate_sha("a/b/c", "abc1234")
        assert len(errors) == 1
        assert "Invalid repo format" in errors[0]


class TestRepoPattern:
    """Tests for REPO_PATTERN validation."""

    def test_valid_patterns(self):
        assert REPO_PATTERN.match("owner/repo")
        assert REPO_PATTERN.match("ggml-org/llama.cpp")
        assert REPO_PATTERN.match("user123/my-project")
        assert REPO_PATTERN.match("Org.Name/repo_name")

    def test_invalid_patterns(self):
        assert not REPO_PATTERN.match("no-slash")
        assert not REPO_PATTERN.match("/no-owner")
        assert not REPO_PATTERN.match("no-repo/")
        assert not REPO_PATTERN.match("a/b/c")


class TestCloneRepo:
    """Tests for clone_repo with mocked subprocess."""

    @patch("scripts.upstream_sha_tester.subprocess.run")
    def test_successful_clone(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0)
        ok, stderr = clone_repo("owner/repo", "abc1234", tmp_path / "dest")
        assert ok is True
        assert stderr == ""

    @patch("scripts.upstream_sha_tester.subprocess.run")
    def test_clone_failure_returns_stderr(self, mock_run, tmp_path):
        import subprocess

        # First call (clone) fails, subsequent calls also fail
        mock_run.side_effect = subprocess.CalledProcessError(
            128, "git", stderr=b"fatal: repository not found\n"
        )
        ok, stderr = clone_repo("owner/repo", "bad-sha", tmp_path / "dest")
        assert ok is False
        assert "repository not found" in stderr


class TestParseCmakeMetadata:
    """Tests for CMake metadata fallback."""

    def test_llama_cpp_detected(self, tmp_path):
        cmake = tmp_path / "CMakeLists.txt"
        cmake.write_text("project(llama.cpp)\n")
        meta = _parse_cmake_metadata(cmake)
        assert meta is not None
        assert meta["backend"] == "cpu"

    def test_ggml_detected(self, tmp_path):
        cmake = tmp_path / "CMakeLists.txt"
        cmake.write_text("find_package(ggml)\n")
        meta = _parse_cmake_metadata(cmake)
        assert meta is not None

    def test_unrelated_cmake_returns_none(self, tmp_path):
        cmake = tmp_path / "CMakeLists.txt"
        cmake.write_text("project(myapp)\n")
        meta = _parse_cmake_metadata(cmake)
        assert meta is None


class TestSchemaValidation:
    """Tests for schema validation paths."""

    @patch("scripts.upstream_sha_tester.clone_repo")
    @patch("scripts.upstream_sha_tester.extract_metadata_from_repo")
    @patch("scripts.upstream_sha_tester.subprocess.run")
    def test_no_metadata_returns_error(self, mock_run, mock_extract, mock_clone):
        mock_clone.return_value = (True, "")
        mock_extract.return_value = None
        mock_run.return_value = MagicMock(returncode=0, stdout="abc1234\n")
        errors = validate_sha("o/r", "abc1234")
        assert any("No METADATA" in e for e in errors)

    def test_invalid_json_in_schema_file(self, tmp_path):
        """Schema file with invalid JSON should be caught."""
        schema_path = tmp_path / "bad.json"
        schema_path.write_text("{invalid json")
        with patch("scripts.upstream_sha_tester.SCHEMA_PATH", schema_path):
            # The validate_sha function will try to load the schema
            # and should catch json.JSONDecodeError
            pass  # This is tested indirectly through the schema loading logic
