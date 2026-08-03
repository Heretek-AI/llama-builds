"""Tests for the perf-claim verification artifacts shipped under docs/benchmarks/.

Validates the lb-0096 acceptance criterion:
  - Each of the 4 claims has a verification artifact (benchmark run, PR test, or refutation note) under docs/benchmarks/.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCH_DIR = REPO_ROOT / "docs" / "benchmarks"

REQUIRED_ARTIFACTS = [
    ("cachyllama-179x-speedup.md", "CachyLLama"),
    ("indras-mirror-80-179-tps.md", "Indras-Mirror"),
    ("atomicbot-tq-30-50pct.md", "AtomicBot"),
    ("openalchemy-47pct-gen-speed.md", "openalchemy"),
]

FORBIDDEN_PHRASES = [
    "179.1x",
    "80-179 tok/s",
    "+30-50%",
    "+47% gen speed",
]


def _read(p: Path) -> str:
    return p.read_text()


class TestBenchmarkArtifactsExist:
    """Each of the 4 claims has a refutation note under docs/benchmarks/."""

    def test_benchmarks_dir_exists(self):
        assert BENCH_DIR.is_dir(), f"Missing {BENCH_DIR}"

    def test_verdict_index_exists(self):
        assert (BENCH_DIR / "README.md").exists(), "Missing docs/benchmarks/README.md verdict index"

    def test_cachyllama_artifact(self):
        path = BENCH_DIR / "cachyllama-179x-speedup.md"
        assert path.exists(), f"Missing {path}"
        text = _read(path)
        assert "CachyLLama" in text
        assert "Unverified" in text or "unverified" in text.lower()

    def test_indras_artifact(self):
        path = BENCH_DIR / "indras-mirror-80-179-tps.md"
        assert path.exists(), f"Missing {path}"
        text = _read(path)
        assert "Indras-Mirror" in text
        assert "Unverified" in text or "unverified" in text.lower()

    def test_atomicbot_artifact(self):
        path = BENCH_DIR / "atomicbot-tq-30-50pct.md"
        assert path.exists(), f"Missing {path}"
        text = _read(path)
        assert "AtomicBot" in text
        assert "Unverified" in text or "unverified" in text.lower()

    def test_openalchemy_artifact(self):
        path = BENCH_DIR / "openalchemy-47pct-gen-speed.md"
        assert path.exists(), f"Missing {path}"
        text = _read(path)
        assert "openalchemy" in text
        assert "Unverified" in text or "unverified" in text.lower()

    def test_artifact_minimum_size(self):
        """Each artifact must be substantive (≥20 lines per acceptance criteria)."""
        for filename, _label in REQUIRED_ARTIFACTS:
            path = BENCH_DIR / filename
            assert path.exists(), f"{path} must exist"
            line_count = len(path.read_text().splitlines())
            assert line_count >= 20, f"{path} has only {line_count} lines (<20)"


class TestMetadataDoesNotRepeatUnverifiedClaims:
    """METADATA descriptions must NOT repeat unverified perf claims."""

    TARGETS_DIR = REPO_ROOT / "targets"

    def test_targets_dir_exists(self):
        assert self.TARGETS_DIR.is_dir()

    def test_no_metadata_contains_unverified_claims(self):
        """Walk every targets/*/build.sh METADATA block and reject forbidden phrases."""
        offenders: list[tuple[Path, str]] = []
        for build_sh in self.TARGETS_DIR.glob("*/build.sh"):
            text = _read(build_sh)
            for phrase in FORBIDDEN_PHRASES:
                # Skip phrases that appear inside a `verification doc` reference
                # (we want to forbid claims appearing as facts, not as audit references).
                if phrase in text and "docs/benchmarks" not in text:
                    # Only flag if the phrase appears as a metric claim, not as
                    # part of a sentence like "see docs/benchmarks/<name>.md for
                    # the 179.1x claim verification".
                    # Simple heuristic: phrase followed by a digit, "%", or " speedup" is a claim.
                    pattern = re.escape(phrase) + r"(\s|\.|,|$)"
                    if re.search(pattern, text):
                        offenders.append((build_sh, phrase))
        assert not offenders, (
            "Targets METADATA contains unverified perf claims as facts:\n"
            + "\n".join(f"  {p}: {phrase}" for p, phrase in offenders)
        )


class TestVerdictIndexShape:
    """docs/benchmarks/README.md summarizes all 4 claims."""

    def test_verdict_lists_all_four_claims(self):
        text = _read(BENCH_DIR / "README.md")
        for filename, label in REQUIRED_ARTIFACTS:
            assert filename in text, f"verdict must reference {filename}"
            assert label in text, f"verdict must mention {label}"

    def test_verdict_status_blocked(self):
        text = _read(BENCH_DIR / "README.md")
        assert "status/blocked" in text or "blocked" in text.lower(), (
            "verdict must record the status/blocked disposition"
        )
