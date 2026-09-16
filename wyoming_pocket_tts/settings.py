"""Runtime settings for Wyoming Pocket TTS."""

QUALITY_PROFILES: dict[str, int] = {
    "fast": 1,
    "balanced": 2,
    "high": 4,
    "maximum": 8,
}


def sampler_decode_steps_for_quality(
    quality: str,
    override: "int | None" = None,
) -> int:
    """Resolve a quality profile to Pocket TTS sampler decode steps.

    Pocket TTS documents that additional sampler decode steps can improve
    quality at the cost of extra computation. ``override`` is intended for
    standalone/CLI users who want direct control while Home Assistant users can
    choose one of the named profiles.
    """
    if override is not None:
        if not 1 <= override <= 32:
            raise ValueError("sampler decode steps must be between 1 and 32")
        return override

    try:
        return QUALITY_PROFILES[quality]
    except KeyError as exc:
        supported = ", ".join(QUALITY_PROFILES)
        raise ValueError(
            f"unknown quality profile {quality!r}; choose one of: {supported}"
        ) from exc
