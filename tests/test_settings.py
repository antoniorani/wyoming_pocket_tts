"""Tests for runtime quality settings."""

import pytest

from wyoming_pocket_tts.settings import (
    QUALITY_PROFILES,
    sampler_decode_steps_for_quality,
)


def test_quality_profiles_increase_decode_steps():
    assert QUALITY_PROFILES == {
        "fast": 1,
        "balanced": 2,
        "high": 4,
        "maximum": 8,
    }


@pytest.mark.parametrize(
    ("quality", "steps"),
    [
        ("fast", 1),
        ("balanced", 2),
        ("high", 4),
        ("maximum", 8),
    ],
)
def test_quality_profile_resolution(quality: str, steps: int):
    assert sampler_decode_steps_for_quality(quality) == steps


def test_explicit_decode_steps_override_profile():
    assert sampler_decode_steps_for_quality("fast", override=6) == 6


@pytest.mark.parametrize("steps", [0, 33])
def test_invalid_decode_step_override_is_rejected(steps: int):
    with pytest.raises(ValueError):
        sampler_decode_steps_for_quality("high", override=steps)


def test_unknown_quality_profile_is_rejected():
    with pytest.raises(ValueError):
        sampler_decode_steps_for_quality("ultra")
