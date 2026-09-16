"""Runtime settings for Wyoming Pocket TTS."""

from collections.abc import Collection

QUALITY_PROFILES: dict[str, int] = {
    "fast": 1,
    "balanced": 2,
    "high": 4,
    "maximum": 8,
}


def decode_steps_for_quality(
    quality: str,
    override: "int | None" = None,
) -> int:
    """Resolve a quality profile to Pocket TTS generation decode steps.

    Pocket TTS documents that additional decode steps can improve quality at the
    cost of extra computation. ``override`` is intended for standalone/CLI users
    who want direct control while Home Assistant users can choose a named profile.
    """
    if override is not None:
        if not 1 <= override <= 32:
            raise ValueError("decode steps must be between 1 and 32")
        return override

    try:
        return QUALITY_PROFILES[quality]
    except KeyError as exc:
        supported = ", ".join(QUALITY_PROFILES)
        raise ValueError(
            f"unknown quality profile {quality!r}; choose one of: {supported}"
        ) from exc


def decode_steps_parameter(parameter_names: Collection[str]) -> str:
    """Return the decode-step keyword supported by the installed Pocket TTS.

    Pocket TTS 2.1 uses ``lsd_decode_steps``. Newer releases renamed the public
    keyword to ``sampler_decode_steps`` while retaining the old name as a
    compatibility alias. Prefer the new spelling when available so newer
    versions do not emit a deprecation warning.
    """
    if "sampler_decode_steps" in parameter_names:
        return "sampler_decode_steps"
    if "lsd_decode_steps" in parameter_names:
        return "lsd_decode_steps"
    raise RuntimeError("installed Pocket TTS exposes no decode-step parameter")
