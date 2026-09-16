# Wyoming Pocket TTS (antoniorani)

Local Pocket TTS for Home Assistant through the Wyoming protocol.

This fork adds Home Assistant-friendly voice selectors and generation quality
profiles on top of the upstream Wyoming Pocket TTS server.

## Recommended Spanish configuration

For the best starting point when prioritising quality:

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

`es_24l` is the larger Spanish model variant. `high` uses 4 Pocket TTS sampler
decode steps. More decode steps can improve generation quality but increase CPU
usage and latency.

## Configuration

| Option | Description |
|---|---|
| `language` | Pocket TTS language/model. For Spanish quality, use `es_24l`. |
| `preset_voices` | Built-in voices selected from dropdowns. The first selected voice is the default. |
| `custom_voices` | Custom/cloned voice filenames without their extension. |
| `quality` | `fast`, `balanced`, `high`, or `maximum`. |
| `voices` | Legacy free-form list retained for upgrades from 1.4.9 and earlier. New setups should normally leave it empty. |
| `voices_dir` | Custom voice sample folder. Keep `/share/tts-voices` in Home Assistant. |
| `device` | Use `cpu` for the Home Assistant App. CUDA requires a separately built CUDA container. |
| `hf_token` | Hugging Face read token, needed only when custom cloning weights require authentication. |
| `debug` | Verbose logging. |

### Quality profiles

| Profile | Decode steps | Notes |
|---|---:|---|
| `fast` | 1 | Lowest latency. |
| `balanced` | 2 | Moderate extra compute. |
| `high` | 4 | Recommended quality profile for this fork. |
| `maximum` | 8 | Highest exposed profile; expect more latency and CPU use. |

## Built-in preset voices

| Language | Presets |
|---|---|
| Spanish | `lola` |
| French | `estelle` |
| German | `juergen` |
| Portuguese | `rafael` |
| Italian | `giovanni` |
| English | `alba`, `anna`, `azelma`, `bill_boerst`, `caro_davy`, `charles`, `cosette`, `eponine`, `eve`, `fantine`, `george`, `jane`, `jean`, `javert`, `marius`, `mary`, `michael`, `paul`, `peter_yearsley`, `stuart_bell`, `vera` |

Use a preset that matches the configured language model.

## Custom / cloned voices

1. Put a clean voice sample in `/share/tts-voices`, for example
   `/share/tts-voices/rocky.ogg`.
2. Add `rocky` under **Custom / cloned voices** in the Configuration tab.
3. If required, accept Kyutai's Pocket TTS model terms on Hugging Face and put a
   read token in `hf_token`.
4. Restart the App/Add-on.
5. Reload the Wyoming integration under **Settings → Devices & services** so Home
   Assistant refreshes its cached voice list.

Supported custom voice files: `.wav`, `.mp3`, `.ogg`, `.flac`, `.m4a`, and
`.safetensors`.

A 15–30 second clean recording with natural intonation is a useful starting
point. Avoid echo, background music and clipping.

## Upgrading from 1.4.9 or earlier

Older versions stored preset and custom names together in `voices`. Version
1.5.0 keeps that option so existing Home Assistant settings remain valid.

When `preset_voices` is populated, it becomes authoritative for built-in voices.
The startup script ignores old built-in names in `voices` but preserves arbitrary
custom names, then combines them with `custom_voices`.

After upgrading this fork, select:

- `language`: `es_24l`
- `preset_voices`: `lola`
- `quality`: `high`

Restart the app and reload the Wyoming integration.

## Connect to Home Assistant

The app sends Wyoming discovery automatically after the server is ready.

1. Start Wyoming Pocket TTS.
2. Wait for the model to initialise on first start.
3. Open **Settings → Devices & services**.
4. Configure the discovered Wyoming service.
5. Select it as the TTS engine for your Home Assistant voice assistant.

The server listens on TCP port `10200`.

## Troubleshooting

### Quality is worse than Piper

Confirm you are using `es_24l`, `lola`, and `high`. Then compare `maximum` if the
extra latency is acceptable. Voice cloning can improve the speaker identity but
cannot remove all model-level prosody limitations.

### Custom voice is missing

Restart the app and reload the Wyoming Protocol integration. Home Assistant
caches the advertised voice list.

### Custom voice fails to load

Check the filename, `/share/tts-voices`, selected language, accepted model terms
and `hf_token`.

### Wyoming integration cannot connect

Check the app log for successful discovery. This fork prefers advertising the
container's IPv4 address to avoid systems where the Home Assistant app hostname
resolves to an unreachable IPv6 address first.

## Source

Repository: https://github.com/antoniorani/wyoming_pocket_tts

Upstream project: https://github.com/araa47/wyoming_pocket_tts

Pocket TTS: https://github.com/kyutai-labs/pocket-tts
