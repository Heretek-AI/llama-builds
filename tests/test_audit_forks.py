"""Tests for scripts/audit_forks.py with mocked GitHub API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.audit_forks import audit_all_forks, check_repo_health


@pytest.fixture
def tmp_targets(tmp_path: Path) -> Path:
    """Create a minimal targets/ tree with two build.sh files."""
    (tmp_path / "targets").mkdir()
    (tmp_path / "targets" / "_template").mkdir()
    (tmp_path / "targets" / "_template" / "build.sh").write_text(
        "# METADATA\n# name=T\n# repo=o/r\n# ref=abc1234\n# backend=cpu\n"
    )

    for slug in ("upstream-cpu", "ik-llama-cpp"):
        d = tmp_path / "targets" / slug
        d.mkdir()
        (d / "build.sh").write_text(
            f"# METADATA\n# name={slug}\n# repo=ggml-org/llama.cpp\n# ref=abc1234\n# backend=cpu\n"
        )
    return tmp_path / "targets"


def test_check_repo_health_healthy() -> None:
    now = datetime.now(UTC).isoformat()
    mock_data = {"archived": False, "pushed_at": now}
    with patch("scripts.audit_forks._github_api", return_value=mock_data):
        result = check_repo_health("owner", "repo")
    assert result["health_status"] == "healthy"
    assert result["is_archived"] is False
    assert result["is_404"] is False


def test_check_repo_health_stale() -> None:
    old = (datetime.now(UTC) - timedelta(days=120)).isoformat()
    mock_data = {"archived": False, "pushed_at": old}
    with patch("scripts.audit_forks._github_api", return_value=mock_data):
        result = check_repo_health("owner", "repo")
    assert result["health_status"] == "stale"
    assert result["days_since_commit"] >= 90


def test_check_repo_health_404() -> None:
    with patch("scripts.audit_forks._github_api", return_value=None):
        result = check_repo_health("owner", "nonexistent")
    assert result["is_404"] is True
    assert result["health_status"] == "not_found"


def test_check_repo_health_archived() -> None:
    mock_data = {"archived": True, "pushed_at": datetime.now(UTC).isoformat()}
    with patch("scripts.audit_forks._github_api", return_value=mock_data):
        result = check_repo_health("owner", "repo")
    assert result["is_archived"] is True
    assert result["health_status"] == "archived"


def test_audit_all_forks(tmp_targets: Path) -> None:
    now = datetime.now(UTC).isoformat()
    mock_data = {"archived": False, "pushed_at": now}
    with patch("scripts.audit_forks._github_api", return_value=mock_data):
        report = audit_all_forks(tmp_targets)

    assert "generated_at" in report
    assert "summary" in report
    assert report["summary"]["healthy"] >= 1
    assert len(report["targets"]) >= 2


def test_health_report_output_format(tmp_targets: Path) -> None:
    now = datetime.now(UTC).isoformat()
    mock_data = {"archived": False, "pushed_at": now}
    with patch("scripts.audit_forks._github_api", return_value=mock_data):
        report = audit_all_forks(tmp_targets)

    schema_keys = {"generated_at", "targets", "summary"}
    assert set(report.keys()) == schema_keys

    for info in report["targets"].values():
        assert "repo" in info
        assert "health_status" in info
        assert info["health_status"] in ("healthy", "stale", "archived", "not_found", "unknown")
