"""Tests for upstream_sha_tester.py — validates upstream SHA compatibility."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.upstream_sha_tester import (
    _parse_metadata_file,
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
        mock_clone.return_value = True
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
        mock_clone.return_value = False
        errors = validate_sha("o/r", "bad-sha")
        assert len(errors) == 1
        assert "Failed to clone" in errors[0]

    @patch("scripts.upstream_sha_tester.clone_repo")
    @patch("scripts.upstream_sha_tester.extract_metadata_from_repo")
    def test_invalid_backend_rejected(self, mock_extract, mock_clone):
        mock_clone.return_value = True
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
        mock_clone.return_value = True
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
