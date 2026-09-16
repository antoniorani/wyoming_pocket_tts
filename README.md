<p align="center">
  <img src="logo.png" alt="Wyoming Pocket TTS" width="400">
</p>

<p align="center">
  <strong>Local Pocket TTS for Home Assistant, with quality profiles, voice selectors and voice cloning</strong>
</p>

<p align="center">
  <a href="https://github.com/antoniorani/wyoming_pocket_tts/actions/workflows/on-merge.yml"><img src="https://github.com/antoniorani/wyoming_pocket_tts/actions/workflows/on-merge.yml/badge.svg" alt="CI"></a>
</p>

This repository is a maintained personal fork of
[`araa47/wyoming_pocket_tts`](https://github.com/araa47/wyoming_pocket_tts).
It exposes [Kyutai Pocket TTS](https://github.com/kyutai-labs/pocket-tts) through
the [Wyoming protocol](https://github.com/rhasspy/wyoming) so it can be used as a
local text-to-speech engine in Home Assistant.

The fork focuses on Home Assistant usability and speech quality: the add-on UI has
proper preset-voice selectors, separate custom voice entries, and quality profiles
that control Pocket TTS sampler decode steps.

## What is different in this fork

- Fixes the optimized Docker image startup regression caused by removing `sympy`
  and `torch/_inductor`.
- Adds a token-independent runtime import smoke test to CI.
- Adds Home Assistant image metadata required by current Supervisor releases.
- Adds **preset voice dropdowns** instead of requiring built-in voice names to be
  typed manually.
- Separates **custom/cloned voices** from built-in presets.
- Adds **quality profiles** (`fast`, `balanced`, `high`, `maximum`).
- Keeps the old `voices` field for backwards compatibility with existing installs.
- Adds Spanish translations for the Home Assistant Configuration tab.
- Defaults new installs of this fork to **Spanish high quality**:
  `es_24l` + `lola` + `high`.

## Recommended Spanish setup

For the best starting point when comparing Pocket TTS with Piper:

```yaml
language: es_24l
preset_voices:
  - lola
custom_voices: []
quality: high
voices_dir: /share/tts-voices
device: cpu
hf_token: ""
debug: false
```

`es_24l` is the larger Spanish model. Kyutai describes the 24-layer models as
larger preview models, and Pocket TTS documents that increasing
`sampler_decode_steps` can improve generation quality at the cost of more compute.
This fork maps `high` to 4 decode steps.

If latency is acceptable and you want to push quality further, try `maximum`.

## Installation in Home Assistant

Home Assistant now calls add-ons **Apps** in current documentation, although the
older “Add-on” wording is still common in the UI and community.

1. Open **Settings → Apps → Install app**.
2. Open the repository menu and add:

   ```text
   https://github.com/antoniorani/wyoming_pocket_tts
   ```

3. Install **Wyoming Pocket TTS (antoniorani)**.
4. Open **Configuration**.
5. Select the language, one or more preset voices and a quality profile.
6. Start the App/Add-on.
7. Accept the discovered Wyoming service under **Settings → Devices & services**.
8. Select that Wyoming TTS service in your Home Assistant voice assistant.

The first start can take significantly longer because Pocket TTS model files must
be downloaded and initialised.

## Home Assistant configuration

| Option | Default | Purpose |
|---|---|---|
| `language` | `es_24l` | Pocket TTS language/model. Use a 24-layer variant when quality is more important than latency. |
| `preset_voices` | `[lola]` | Built-in voices. Each list row is a selector; the first voice becomes the default. |
| `custom_voices` | `[]` | Custom/cloned voice names, entered without the file extension. |
| `quality` | `high` | Generation profile controlling sampler decode steps. |
| `voices` | `[]` | Legacy/advanced compatibility field from releases up to 1.4.9. Usually leave empty in new configurations. |
| `voices_dir` | `/share/tts-voices` | Folder containing custom voice samples. |
| `device` | `cpu` | Inference device. The Home Assistant build is intended for CPU; CUDA is for a separately built CUDA container. |
| `hf_token` | empty | Hugging Face token, required only for custom voice cloning when gated weights are needed. |
| `debug` | `false` | Verbose server logging. |

### Quality profiles

| Profile | Sampler decode steps | Use case |
|---|---:|---|
| `fast` | 1 | Lowest latency / upstream-style default generation cost. |
| `balanced` | 2 | Small quality increase with moderate extra cost. |
| `high` | 4 | Recommended Home Assistant quality profile for this fork. |
| `maximum` | 8 | Highest profile exposed by the add-on; expect noticeably higher CPU use and latency. |

Pocket TTS itself exposes the decode-step parameter. The mapping above is a
convenience layer in this repository, not an upstream Kyutai naming convention.

Standalone users can bypass the profiles and set an explicit value:

```bash
uv run python -m wyoming_pocket_tts \
  --language es_24l \
  --voices lola \
  --sampler-decode-steps 6
```

## Built-in voices

The Home Assistant `preset_voices` field presents these as dropdown choices.
Choose voices that match the selected language model.

| Language | Presets |
|---|---|
| Spanish | `lola` |
| French | `estelle` |
| German | `juergen` |
| Portuguese | `rafael` |
| Italian | `giovanni` |
| English | `alba`, `anna`, `azelma`, `bill_boerst`, `caro_davy`, `charles`, `cosette`, `eponine`, `eve`, `fantine`, `george`, `jane`, `jean`, `javert`, `marius`, `mary`, `michael`, `paul`, `peter_yearsley`, `stuart_bell`, `vera` |

The first selected preset is the default voice used when a Wyoming request does
not explicitly name another advertised voice.

## Custom voice cloning

Custom voices are deliberately separate from preset selection because Home
Assistant cannot build a dynamic dropdown from arbitrary files in
`/share/tts-voices`.

1. Record a clean voice sample. Around 15–30 seconds is a useful target.
2. Save it in `/share/tts-voices`, for example:

   ```text
   /share/tts-voices/rocky.ogg
   ```

3. Add `rocky` under **Custom / cloned voices** in the add-on configuration.
4. If required, accept the Kyutai Pocket TTS model terms on Hugging Face and add a
   read token to `hf_token`.
5. Restart the add-on.
6. Reload the Wyoming integration in Home Assistant so its cached voice list is
   refreshed.

Supported custom voice file extensions in the server are `.wav`, `.mp3`, `.ogg`,
`.flac`, `.m4a` and `.safetensors`.

### Recording guidance

- Use a quiet room with little reverberation.
- Avoid music and background speakers.
- Use natural speech rather than a single monotone sentence.
- Include varied intonation.
- Avoid clipped or very quiet recordings.

Voice cloning changes timbre and speaker identity, but it does not remove the
fundamental prosody/quality limits of the selected Pocket TTS model.

## Upgrading from 1.4.9 or earlier

Older versions used one free-form `voices` list for both built-in and custom
voices. Version 1.5.0 keeps that field so saved Home Assistant options remain
valid.

When you select values in the new `preset_voices` field:

- the selected presets become authoritative;
- old built-in preset names from `voices` are ignored;
- arbitrary names in `voices` are retained as custom voice names;
- names in `custom_voices` are also added.

After upgrading, for this repository's recommended Spanish setup choose:

- Language: `es_24l`
- Preset voices: `lola`
- Generation quality: `high`

Then restart the add-on and reload the Wyoming integration.

## Languages

| Configuration | Language | Matching preset |
|---|---|---|
| `en` | English | `alba` (or another English preset) |
| `fr` / `fr_24l` | French | `estelle` |
| `de` / `de_24l` | German | `juergen` |
| `pt` / `pt_24l` | Portuguese | `rafael` |
| `it` / `it_24l` | Italian | `giovanni` |
| `es` / `es_24l` | Spanish | `lola` |

Availability of specific upstream model aliases can change between Pocket TTS
versions. `es_24l` is the recommended Spanish choice in this fork.

## Standalone Docker

The standard `Dockerfile` is CPU-only:

```bash
docker build -t wyoming-pocket-tts .

docker run --rm -p 10200:10200 \
  -e LANGUAGE=es_24l \
  -e QUALITY=high \
  -e VOICES=lola \
  wyoming-pocket-tts
```

For NVIDIA systems, build the separate CUDA Dockerfile:

```bash
docker build -f Dockerfile.cuda -t wyoming-pocket-tts-cuda .

docker run --rm --gpus all -p 10200:10200 \
  -e LANGUAGE=es_24l \
  -e QUALITY=high \
  -e VOICES=lola \
  -e DEVICE=cuda \
  wyoming-pocket-tts-cuda
```

## Local development

This project uses `uv`.

```bash
uv sync --all-extras --dev --frozen
uv run pytest
uv run python -m wyoming_pocket_tts \
  --language es_24l \
  --voices lola \
  --quality high \
  --debug
```

The server listens on Wyoming TCP port `10200` by default.

## Troubleshooting

### Speech quality is worse than Piper

Start with `es_24l`, `lola` and `high`. If latency is acceptable, compare with
`maximum`. A clean cloned voice can improve speaker identity, but a clone is not
a substitute for a stronger acoustic/language model.

### Custom voice does not appear in Home Assistant

Restart Wyoming Pocket TTS, then reload its Wyoming Protocol integration under
**Settings → Devices & services**. Home Assistant caches advertised voice names.

### Custom voice fails to load

Check that:

- the filename in `custom_voices` matches the sample filename without extension;
- the file is in `/share/tts-voices`;
- the selected language is correct;
- the required Hugging Face model terms have been accepted;
- `hf_token` is a valid read token when cloning weights require authentication.

### App starts but Wyoming cannot connect

The server advertises an IPv4 address to Home Assistant where possible to avoid
hosts whose add-on hostname resolves to an unreachable IPv6 address. Check the
add-on log for `Successfully sent discovery information to Home Assistant` and
reload the Wyoming integration if necessary.

## Project history and acknowledgements

This fork builds on the work in
[`araa47/wyoming_pocket_tts`](https://github.com/araa47/wyoming_pocket_tts),
including prior fixes for streaming, custom audio formats, Home Assistant
connectivity and CUDA support.

Thanks to:

- [Kyutai](https://kyutai.org/) for Pocket TTS.
- The upstream `wyoming_pocket_tts` contributors.
- The Wyoming and Home Assistant projects.

## Licensing

The Python project metadata declares the wrapper project as MIT licensed. The
Pocket TTS model and its weights have their own licensing/usage terms; review the
current Kyutai model card and Hugging Face terms before redistribution or voice
cloning use.
