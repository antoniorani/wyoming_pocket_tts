"""Tests for Home Assistant app configuration."""

from pathlib import Path

CONFIG_YAML = Path(__file__).resolve().parent.parent / "config.yaml"


def _config_text() -> str:
    return CONFIG_YAML.read_text()


def test_config_has_no_environment_block():
    """Supervisor does not template values in an ``environment`` block."""
    text = _config_text()
    assert "environment:" not in text
    assert "# Environment" not in text


def test_hf_token_option_is_preserved():
    """Voice cloning still exposes the supported token path."""
    text = _config_text()
    assert "hf_token:" in text
    assert "hf_token: password?" in text


def test_quality_profile_is_exposed():
    """Quality must be selectable from the Home Assistant UI."""
    text = _config_text()
    assert "quality: high" in text
    assert "quality: list(fast|balanced|high|maximum)" in text


def test_preset_voice_selector_is_exposed():
    """Built-in voices should be selected, not typed free-form."""
    text = _config_text()
    assert "preset_voices:" in text
    assert "list(alba|anna|azelma|" in text
    assert "|lola)" in text


def test_custom_and_legacy_voice_paths_are_preserved():
    """Custom names and older saved configurations remain supported."""
    text = _config_text()
    assert "custom_voices:" in text
    assert "voices:" in text


def test_spanish_quality_defaults_for_personal_fork():
    """Fresh installs of this fork start with the preferred Spanish setup."""
    text = _config_text()
    assert "language: es_24l" in text
    assert "        - lola" in text
