"""Tests for action.yml backend-specific logic."""


def _extract_sm_number(gpu_target: str) -> str:
    """Extract SM number from gpu_target string, mirroring the shell logic.

    The action.yml CMake configure step uses:
        SM_NUM="${{ inputs.gpu_target#sm_ }}"
    which strips the 'sm_' prefix and passes the rest as CMAKE_CUDA_ARCHITECTURES.
    """
    if gpu_target.startswith("sm_"):
        return gpu_target[3:]  # strip "sm_" prefix
    return gpu_target


def test_sm_number_extraction():
    """sm_89 -> 89"""
    assert _extract_sm_number("sm_89") == "89"


def test_sm_number_extraction_with_suffix():
    """sm_90a -> 90a"""
    assert _extract_sm_number("sm_90a") == "90a"


def test_sm_number_extraction_small():
    """sm_70 -> 70"""
    assert _extract_sm_number("sm_70") == "70"


def test_sm_number_no_prefix_passthrough():
    """If no sm_ prefix, return as-is."""
    assert _extract_sm_number("gfx1151") == "gfx1151"
