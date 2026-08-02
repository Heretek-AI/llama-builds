# scripts/version_tag.py
"""Generate traceable version tags for llama-builds artifacts.

Version tag format: {ref_prefix}-{build_number}
- ref_prefix: First 7 chars of the upstream SHA
- build_number: Sequential integer per upstream ref (starts at 1)
"""

from __future__ import annotations

import re

TAG_PATTERN = re.compile(r"^([0-9a-f]{7})-(\d+)$")


def generate_version_tag(ref_sha: str, build_number: int) -> str:
    """Generate a version tag from an upstream SHA and build number.

    Args:
        ref_sha: Git SHA (full or short) of the upstream ref.
        build_number: Sequential build number (>= 1).

    Returns:
        Version tag string, e.g. "abc1234-1".

    Raises:
        ValueError: If ref_sha is empty or build_number < 1.
    """
    if not ref_sha:
        raise ValueError("ref_sha must not be empty")
    if build_number < 1:
        raise ValueError("build_number must be >= 1")

    prefix = ref_sha[:7]
    return f"{prefix}-{build_number}"


def parse_version_tag(tag: str) -> tuple[str, int]:
    """Parse a version tag back into ref prefix and build number.

    Args:
        tag: Version tag string, e.g. "abc1234-1".

    Returns:
        Tuple of (ref_prefix, build_number).

    Raises:
        ValueError: If tag doesn't match the expected format.
    """
    match = TAG_PATTERN.match(tag)
    if not match:
        raise ValueError(f"Invalid version tag format: {tag!r} (expected 'abcdef0-N')")
    return match.group(1), int(match.group(2))
