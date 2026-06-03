# ModelsLab MusicGen Audio To Music API

Implementation status: implemented

## Overview

- Operation name: `audio_to_music`.
- Provider identifier: `modelslab`.
- Credential environment variable: `MODELSLAB_API_KEY`.
- Supported technical capabilities: music generation or transformation guided by source audio. Provider coverage includes instrumental generation, prompt-led MusicGen, parameter control, audio-guided music, and loops.

## Account And Credentials

Set `MODELSLAB_API_KEY` in the environment before calling this wrapper.

The provider key is sent in the request body as documented by ModelsLab.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [ModelsLab MusicGen](https://docs.modelslab.com/voice-cloning/music-gen)
- [ModelsLab pricing](https://modelslab.com/pricing)

## Current Wrapper Default

- Default model: `musicgen`.
- Endpoint or task flow: `DEFAULT_ENDPOINT` = `https://modelslab.com/api/v6/voice/music_gen`

## Parameter Reference

```python
easy_ai_clients.music.audio_to_music(audio, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `audio`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, `init_audio`, duration, format, bitrate, base64 flag, webhook, and track ID.

Optional inputs:

- `prompt`, `model`; provider-native fields such as reference type, strength, duration, format, seed, webhook, upload IDs, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; media values may be URL, local path, bytes, or data URI when the adapter supports that transport.

## Model Coverage

Documented model coverage: `musicgen` is the wrapper default for audio-guided paths.

Current wrapper default: `musicgen`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST call to hosted MusicGen with optional fetch for queued jobs.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: `output` arrays with URLs; queued jobs can require fetch-result polling. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use ModelsLab pricing or account credits. The wrapper marks cost unavailable.
- Persistence notes: Output URL retention is not confirmed locally. Download returned URLs promptly.
- Limitations or warnings: Queued responses require fetch/result handling before download. Verify rights to the source audio before transformation or editing.

## Python Example

```python
from easy_ai_clients import music

result = music.audio_to_music(
    "https://example.com/reference.wav",
    prompt="Turn this melody into a polished synthwave track.",
    api="modelslab",
    output_path="out/remix.mp3",
)
```

## Pricing Notes

Use ModelsLab pricing or account credits. The wrapper marks cost unavailable.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
