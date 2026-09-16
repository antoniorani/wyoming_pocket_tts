#!/usr/bin/env python3
"""Wyoming server for Pocket TTS."""

import argparse
import asyncio
import logging
import os
from functools import partial
from typing import cast

from pocket_tts import TTSModel
from wyoming.server import AsyncTcpServer

from . import __version__
from .handler import (
    PRESET_VOICES,
    PocketTTSEventHandler,
    get_wyoming_info,
    list_custom_voice_names,
    load_voice,
    normalize_language,
    plan_voices,
)
from .settings import QUALITY_PROFILES, decode_steps_for_quality

_LOGGER = logging.getLogger(__name__)


async def main() -> None:
    """Run the Wyoming Pocket TTS server."""
    parser = argparse.ArgumentParser(description="Wyoming server for Pocket TTS")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=10200,
        help="Port to bind to (default: 10200)",
    )
    parser.add_argument(
        "--voices",
        default="",
        help=(
            "Comma-separated voices to load and advertise, e.g. 'rocky' or "
            "'alba,rocky'. Each is preloaded for fast first response and is the "
            "ONLY set advertised to Home Assistant. Names are presets (e.g. alba) "
            "or custom sample filenames without extension (e.g. rocky). Leave empty "
            "to advertise every preset + custom voice, loaded on demand."
        ),
    )
    parser.add_argument(
        "--voice",
        default="",
        help="Legacy: default voice, used only when --voices is empty.",
    )
    parser.add_argument(
        "--voices-dir",
        default="/share/tts-voices",
        help="Directory containing custom voice samples (default: /share/tts-voices)",
    )
    parser.add_argument(
        "--preload-voices",
        default="",
        help="Legacy: comma-separated voices to preload, used only when --voices is empty.",
    )
    parser.add_argument(
        "--language",
        default="en",
        help=(
            "Language to use (default: en). Supported: en, fr, de, pt, it, es, "
            "fr_24l, de_24l, pt_24l, it_24l, es_24l, plus upstream language "
            "names. The 24-layer models prioritise quality over speed. Custom "
            "voices are loaded through the selected language model."
        ),
    )
    parser.add_argument(
        "--quality",
        default="balanced",
        choices=tuple(QUALITY_PROFILES),
        help=(
            "Generation quality profile. Higher quality uses more decode steps "
            "and is slower (default: balanced)."
        ),
    )
    parser.add_argument(
        "--decode-steps",
        "--sampler-decode-steps",
        dest="decode_steps",
        type=int,
        default=None,
        help=(
            "Advanced: override the quality profile with an explicit Pocket TTS "
            "generation step count (1-32)."
        ),
    )
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to run inference on (default: cpu)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        _LOGGER.info("Using HuggingFace token from environment")
        os.environ["HF_TOKEN"] = hf_token

    try:
        decode_steps = decode_steps_for_quality(args.quality, args.decode_steps)
    except ValueError as err:
        parser.error(str(err))

    _LOGGER.info("Starting Wyoming Pocket TTS server v%s", __version__)
    args.language = normalize_language(args.language)
    _LOGGER.info(
        "Loading Pocket TTS model for language: %s | quality: %s | decode steps: %d",
        args.language,
        args.quality if args.decode_steps is None else "custom",
        decode_steps,
    )

    # Pocket TTS 2.1.0 calls this parameter ``lsd_decode_steps``. Newer releases
    # keep that name as a deprecated compatibility alias for
    # ``sampler_decode_steps``, so using the old keyword here works across both
    # APIs while this project is still locked to 2.1.0 for development/testing.
    model = TTSModel.load_model(
        language=args.language,
        lsd_decode_steps=decode_steps,
    ).to(args.device)
    _LOGGER.info(
        "Model loaded successfully (sample rate: %d Hz, device: %s)",
        model.sample_rate,
        args.device,
    )

    custom_voice_names = list_custom_voice_names(args.voices_dir)
    if custom_voice_names:
        _LOGGER.info(
            "Found %d custom voice(s) in %s: %s",
            len(custom_voice_names),
            args.voices_dir,
            ", ".join(custom_voice_names),
        )

    configured = [v.strip() for v in (args.voices or "").split(",") if v.strip()]
    to_preload, available_voices, default_voice = plan_voices(
        configured, custom_voice_names, args.language
    )

    if not configured:
        preload_raw = (args.preload_voices or "").strip()
        if preload_raw.lower() == "all":
            to_preload = list(dict.fromkeys(PRESET_VOICES + custom_voice_names))
        elif preload_raw:
            to_preload = [v.strip() for v in preload_raw.split(",") if v.strip()]
        if args.voice:
            default_voice = args.voice
        if default_voice not in to_preload:
            to_preload.append(default_voice)

    args.voice = default_voice

    voice_states: dict = {}
    for name in dict.fromkeys(to_preload):
        state = load_voice(model, name, args.voices_dir)
        if state is not None:
            voice_states[name] = state
            _LOGGER.info("Preloaded voice: %s", name)
        elif configured:
            _LOGGER.error(
                "Configured voice '%s' could not be loaded. If it is a custom voice, "
                "set a Hugging Face token (hf_token) and ensure %s/%s.<ext> exists.",
                name,
                args.voices_dir,
                name,
            )
        else:
            _LOGGER.warning(
                "Could not preload voice '%s' (unknown name?); will try on demand",
                name,
            )

    _LOGGER.info(
        "Default voice: %s | preloaded %d voice(s) | advertising %d voice(s): %s",
        default_voice,
        len(voice_states),
        len(available_voices),
        ", ".join(available_voices),
    )

    wyoming_info = get_wyoming_info(available_voices, args.language)

    # Bind all interfaces (IPv4 + IPv6) when host is the wildcard. Home Assistant
    # networks can be dual-stack, while some hosts cannot actually route IPv6.
    bind_host = None if args.host in ("", "0.0.0.0", "::") else args.host
    server = AsyncTcpServer(host=cast("str", bind_host), port=args.port)
    _LOGGER.info("Server listening on %s:%d", args.host, args.port)

    await server.run(
        partial(
            PocketTTSEventHandler,
            wyoming_info,
            args,
            model,
            voice_states,
        )
    )


def run() -> None:
    """Entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
