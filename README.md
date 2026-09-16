<p align="center">
  <img src="logo.png" alt="Wyoming Pocket TTS" width="400">
</p>

<p align="center">
  <strong>Local Pocket TTS for Home Assistant, with quality profiles, voice selectors and voice cloning</strong>
</p>

<p align="center">
  <a href="https://github.com/antoniorani/wyoming_pocket_tts/actions/workflows/on-merge.yml"><img src="https://github.com/antoniorani/wyoming_pocket_tts/actions/workflows/on-merge.yml/badge.svg" alt="CI"></a>
</p>

This is a maintained personal fork of
[`araa47/wyoming_pocket_tts`](https://github.com/araa47/wyoming_pocket_tts).
It exposes [Kyutai Pocket TTS](https://github.com/kyutai-labs/pocket-tts)
through the [Wyoming protocol](https://github.com/rhasspy/wyoming) for local
text-to-speech in Home Assistant.

## Highlights of this fork

- Fixes the optimized image startup regression caused by removing `sympy` and
  `torch/_inductor`.
- Adds Home Assistant-friendly **preset voice selectors**.
- Separates **custom/cloned voices** from built-in presets.
- Adds **quality profiles**: `fast`, `balanced`, `high`, and `maximum`.
- Keeps the legacy `voices` field so existing 1.4.x configurations continue to
  work when upgrading.
- Adds English and Spanish descriptions in the Home Assistant Configuration tab.
- Adds CI coverage for the final Docker runtime image.

## Recommended Spanish quality setup

The defaults remain compatible with older releases so upgrades do not silently
change language or voice. For Spanish, this is the recommended starting point:

```yaml
language: es_24l
preset_voices:
  - lola
custom_voices: []
voices: []
quality: high
voices_dir: /share/tts-voices
device: cpu
hf_token: ""
debug: false
```

`es_24l` is the larger Spanish model variant. Pocket TTS supports multiple
generation/decode steps; more steps can improve quality at the cost of more CPU
and latency. This fork maps `high` to 4 steps and `maximum` to 8.

## Install in Home Assistant

1. Open **Settings → Apps → Install app**.
2. Open the repository menu and add:

   ```text
   https://github.com/antoniorani/wyoming_pocket_tts
   ```

3. Install **Wyoming Pocket TTS (antoniorani)**.
4. Open **Configuration** and choose language, preset voices and quality.
5. Start the App/Add-on.
6. Configure the discovered Wyoming service under **Settings → Devices & services**.
7. Select it as the text-to-speech engine in your Home Assistant voice assistant.

The first start can take longer while Pocket TTS downloads and initializes model
files.

## Home Assistant configuration

| Option | Upgrade-safe default | Purpose |
|---|---|---|
| `language` | `en` | Pocket TTS language/model. Use a 24-layer variant when quality is more important than latency. |
| `preset_voices` | `[]` | Built-in voices. Each row is a dropdown; the first selected voice becomes the default. |
| `custom_voices` | `[]` | Custom/cloned voice filenames without their extension. |
| `voices` | `[alba]` | Legacy compatibility field from 1.4.x. New setups should normally move built-in voices to `preset_voices`. |
| `quality` | `balanced` | Generation quality profile. |
| `voices_dir` | `/share/tts-voices` | Folder containing custom voice samples. |
| `device` | `cpu` | Home Assistant uses CPU. CUDA is for a separately built CUDA container. |
| `hf_token` | empty | Hugging Face read token, required only when custom cloning weights need authentication. |
| `debug` | `false` | Verbose server logging. |

### Quality profiles

| Profile | Decode steps | Intended use |
|---|---:|---|
| `fast` | 1 | Lowest latency. |
| `balanced` | 2 | Moderate extra compute; upgrade-safe default. |
| `high` | 4 | Recommended starting point when speech quality matters. |
| `maximum` | 8 | Highest profile exposed in the add-on; expect more latency and CPU use. |

The profile names and step mapping are a convenience layer in this fork. Pocket
TTS itself exposes the underlying generation-step parameter.

Standalone users can override the profile explicitly. Both flag names below are
accepted; `--decode-steps` is the fork's version-neutral name:

```bash
uv run python -m wyoming_pocket_tts \
  --language es_24l \
  --voices lola \
  --decode-steps 6
```

## Built-in voices

Choose a preset that matches the selected language model.

| Language | Presets |
|---|---|
| Spanish | `lola` |
| French | `estelle` |
| German | `juergen` |
| Portuguese | `rafael` |
| Italian | `giovanni` |
| English | `alba`, `anna`, `azelma`, `bill_boerst`, `caro_davy`, `charles`, `cosette`, `eponine`, `eve`, `fantine`, `george`, `jane`, `jean`, `javert`, `marius`, `mary`, `michael`, `paul`, `peter_yearsley`, `stuart_bell`, `vera` |

## Custom / cloned voices

1. Put a clean voice sample in `/share/tts-voices`, for example
   `/share/tts-voices/rocky.ogg`.
2. Add `rocky` under **Custom / cloned voices** in the Configuration tab.
3. If required, accept Kyutai's Pocket TTS model terms on Hugging Face and add a
   read token to `hf_token`.
4. Restart Wyoming Pocket TTS.
5. Reload the Wyoming Protocol integration in Home Assistant so its cached voice
   list is refreshed.

Supported sample types are `.wav`, `.mp3`, `.ogg`, `.flac`, `.m4a`, and
`.safetensors`. A clean 15–30 second recording with natural intonation is a good
starting point.

Voice cloning improves speaker identity and timbre, but it cannot remove all
model-level prosody limitations.

## Upgrading from 1.4.9 or earlier

Version 1.5.0 deliberately keeps the old `voices` option. If the new
`preset_voices` selector is empty, the old list behaves as before.

Once you select a value in `preset_voices`:

- the new selector becomes authoritative for built-in presets;
- old built-in preset names in `voices` are ignored;
- arbitrary/custom names in `voices` are preserved;
- names in `custom_voices` are added as well.

For the recommended Spanish setup, select `es_24l`, `lola`, and `high`, then
restart the app and reload the Wyoming integration.

## Languages

| Configuration | Language | Matching preset |
|---|---|---|
| `en` | English | `alba` or another English preset |
| `fr` / `fr_24l` | French | `estelle` |
| `de` / `de_24l` | German | `juergen` |
| `pt` / `pt_24l` | Portuguese | `rafael` |
| `it` / `it_24l` | Italian | `giovanni` |
| `es` / `es_24l` | Spanish | `lola` |

## Standalone Docker

CPU image:

```bash
docker build -t wyoming-pocket-tts .

docker run --rm -p 10200:10200 \
  -e LANGUAGE=es_24l \
  -e QUALITY=high \
  -e VOICES=lola \
  wyoming-pocket-tts
```

CUDA image for a host with the NVIDIA Container Toolkit:

```bash
docker build -f Dockerfile.cuda -t wyoming-pocket-tts-cuda .

docker run --rm --gpus all -p 10200:10200 \
  -e LANGUAGE=es_24l \
  -e QUALITY=high \
  -e VOICES=lola \
  -e DEVICE=cuda \
  wyoming-pocket-tts-cuda
```

## Development

```bash
uv sync --all-extras --dev --frozen
uv run pytest
uv run prek run --all-files
```

The Wyoming server listens on TCP port `10200` by default.

## Troubleshooting

### Speech still sounds worse than Piper

Start with `es_24l`, `lola`, and `high`. If latency is acceptable, compare
`maximum`. A cloned voice can improve speaker identity, but a clone is not a
substitute for a stronger acoustic/language model.

### Custom voice does not appear

Restart Wyoming Pocket TTS and reload the Wyoming Protocol integration. Home
Assistant caches advertised voice names.

### Custom voice fails to load

Check the filename, `/share/tts-voices`, selected language, accepted model terms,
and `hf_token` when gated cloning weights require authentication.

### Wyoming cannot connect

Check the app log for successful discovery and reload the Wyoming integration if
necessary. This fork prefers advertising the container's IPv4 address where
possible to avoid systems with an unreachable IPv6 route.

## Acknowledgements and licensing

This fork builds on
[`araa47/wyoming_pocket_tts`](https://github.com/araa47/wyoming_pocket_tts) and
the work of its contributors. Pocket TTS is developed by
[Kyutai](https://kyutai.org/).

The Python project metadata declares the wrapper as MIT licensed. Pocket TTS and
its model weights have their own licensing and usage terms; review Kyutai's
current model card and Hugging Face terms before redistribution or voice cloning.
