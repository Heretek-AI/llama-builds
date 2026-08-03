"""Tests for the unseeded-repo triage doc shipped for lb-0099 (#85).

Validates acceptance criteria:
  - docs/triage/2026-08-03-unseeded-repos.md exists with per-repo decision table.
  - Each decision references the original SYNTHESIS.md line and the chosen disposition.
  - Tag plan recorded for backlog + skipped repos.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRIAGE_PATH = REPO_ROOT / "docs" / "triage" / "2026-08-03-unseeded-repos.md"
SYNTHESIS_PATH = REPO_ROOT / ".omo" / "ulw-research" / "20260803-010124" / "SYNTHESIS.md"

# Minimum set of repos SYNTHESIS.md:131-141 names; the triage must
# mention each of them with a disposition.
EXPECTED_REPOS = [
    "Indras-Mirror",
    "openalchemy",
    "atomicmilkshake",
    "unixsysdev",
    "LL4nc33",
    "LyndonBlack",
    "Anbeeld",
    "onthenose-record446",
    "Aulora137",
]

REQUIRED_DISPOSITIONS = {"seed", "defer", "skip", "out-of-scope"}
REQUIRED_SYNTHESIS_LINE_HINT = re.compile(r"SYNTHESIS\.md:\d{2,3}")


def _read(p: Path) -> str:
    return p.read_text()


class TestTriageDocExists:
    def test_triage_doc_exists(self):
        assert TRIAGE_PATH.exists(), f"Missing {TRIAGE_PATH}"

    def test_triage_doc_substantial(self):
        text = _read(TRIAGE_PATH)
        lines = text.splitlines()
        assert len(lines) >= 30, f"Triage doc has only {len(lines)} lines (<30)"


class TestTriageDocCoversAllExpectedRepos:
    def test_each_expected_repo_appears(self):
        text = _read(TRIAGE_PATH)
        for repo in EXPECTED_REPOS:
            assert repo in text, f"Triage doc must mention {repo} from SYNTHESIS.md:131-141"

    def test_buun_and_cachyllama_listed(self):
        """lb-0092 / lb-0093 already shipped (#79, #80 closed); triage must reference them."""
        text = _read(TRIAGE_PATH)
        assert "CachyLLama" in text or "fewtarius/CachyLLama" in text
        assert "buun-llama-cpp" in text or "spiritbuun" in text

    def test_kv_cache_and_runtimes_categories_listed(self):
        text = _read(TRIAGE_PATH)
        # KV-cache + alternative-runtimes categories must be acknowledged.
        assert "KV-cache" in text or "LMCache" in text
        assert "openinfer" in text or "vmlx" in text


class TestTriageDocHasDecisionTable:
    def test_disposition_table_present(self):
        text = _read(TRIAGE_PATH)
        # Find a table row with a disposition word (allow leading | + whitespace).
        for disp in REQUIRED_DISPOSITIONS:
            pattern = rf"\|\s*\*\*{disp}\*\*"
            assert re.search(pattern, text), f"Disposition table must include a row with **{disp}**"

    def test_each_row_references_synthesis_line(self):
        text = _read(TRIAGE_PATH)
        # Each table row should reference a SYNTHESIS.md line — accept either
        # the explicit "SYNTHESIS.md:131" form or a bare line number in the
        # SYNTHESIS.md column.
        explicit = REQUIRED_SYNTHESIS_LINE_HINT.findall(text)
        # Count table rows: lines starting with "| <num> |" or just "| N |".
        import re as _re

        row_lines = [line for line in text.splitlines() if _re.match(r"^\|\s*\d+\s*\|", line)]
        assert len(row_lines) >= 9, (
            f"Triage table must have >= 9 numeric rows (one per repo); got {len(row_lines)}"
        )
        assert len(explicit) + len(row_lines) >= 9, (
            f"Triage must reference SYNTHESIS.md lines; explicit={len(explicit)}, rows={len(row_lines)}"
        )


class TestTriageDocTagPlan:
    def test_backlog_tag_recorded(self):
        text = _read(TRIAGE_PATH)
        assert "roadmap/backlog" in text, (
            "Triage must record roadmap/backlog tag for deferred repos"
        )

    def test_skip_tag_recorded(self):
        text = _read(TRIAGE_PATH)
        assert "meta/skip-rationale" in text, (
            "Triage must record meta/skip-rationale tag for skipped/out-of-scope repos"
        )


class TestTriageDocCrossReferences:
    def test_references_related_issues(self):
        text = _read(TRIAGE_PATH)
        # Must cross-reference the perf-claim verification (#83) and the
        # already-closed fork seeds (#79, #80).
        for marker in ("#83", "#84", "#79", "#80"):
            assert marker in text, f"Triage must cross-reference {marker}"


class TestTriageDocSynthesisPathExists:
    def test_synthesis_file_referenced_exists(self):
        """The SYNTHESIS path the triage points at must actually exist on disk."""
        assert SYNTHESIS_PATH.exists(), (
            f"Triage references {SYNTHESIS_PATH} but the file is missing"
        )
