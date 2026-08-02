# tests/test_version_tag.py
"""Tests for version_tag.py — generates traceable version strings."""

from scripts.version_tag import generate_version_tag, parse_version_tag


class TestGenerateVersionTag:
    def test_basic_tag(self):
        assert generate_version_tag("abc1234def5678", 1) == "abc1234-1"

    def test_short_sha(self):
        assert generate_version_tag("abc1234", 1) == "abc1234-1"

    def test_build_number_increments(self):
        assert generate_version_tag("abc1234def5678", 3) == "abc1234-3"

    def test_full_sha_prefixes_7_chars(self):
        tag = generate_version_tag("abc1234def567890123", 1)
        assert tag == "abc1234-1"
        assert len(tag.split("-")[0]) == 7

    def test_empty_sha_raises(self):
        import pytest

        with pytest.raises(ValueError):
            generate_version_tag("", 1)

    def test_zero_build_number_raises(self):
        import pytest

        with pytest.raises(ValueError):
            generate_version_tag("abc1234", 0)

    def test_negative_build_number_raises(self):
        import pytest

        with pytest.raises(ValueError):
            generate_version_tag("abc1234", -1)


class TestParseVersionTag:
    def test_parse_basic(self):
        ref, num = parse_version_tag("abc1234-1")
        assert ref == "abc1234"
        assert num == 1

    def test_parse_large_number(self):
        ref, num = parse_version_tag("abc1234-42")
        assert ref == "abc1234"
        assert num == 42

    def test_parse_invalid_format(self):
        import pytest

        with pytest.raises(ValueError):
            parse_version_tag("invalid")

    def test_parse_no_build_number(self):
        import pytest

        with pytest.raises(ValueError):
            parse_version_tag("abc1234")
