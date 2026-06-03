# ModelsLab MusicGen Text To Music API

Implementation status: implemented

## Overview

- Operation name: `text_to_music`.
- Provider identifier: `modelslab`.
- Credential environment variable: `MODELSLAB_API_KEY`.
- Supported technical capabilities: prompt-led music generation from a text brief. Provider coverage includes instrumental generation, prompt-led MusicGen, parameter control, audio-guided music, and loops.

## Account And Credentials

Set `MODELSLAB_API_KEY` in the environment before calling this wrapper.

The provider key is sent in the request body as documented by ModelsLab.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [ModelsLab MusicGen](https://docs.modelslab.com/voice-cloning/music-gen)
- [ModelsLab pricing](https://modelslab.com/pricing)

## Current Wrapper Default

- Default model: No explicit default model is set by this wrapper path.
- Endpoint or task flow: `ENDPOINT` = `https://modelslab.com/api/v6/voice/music_gen`; queued fetch URLs are called with `POST` and the API `key` in the JSON body.

## Parameter Reference

```python
easy_ai_clients.music.text_to_music(prompt, model=None, *, api, **kwargs)
```

Required inputs:

- `prompt`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, `init_audio`, duration, format, bitrate, base64 flag, webhook, and track ID.

Optional inputs:

- `model`; provider-native fields such as style, lyrics, duration, format, seed, webhook, instrumental flags, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `musicgen` is the wrapper default for audio-guided paths.

Current wrapper default: No explicit default model is set by this wrapper path.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST call to hosted MusicGen with optional fetch for queued jobs.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: `output` arrays with URLs; queued jobs can require fetch-result polling. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use ModelsLab pricing or account credits. The wrapper marks cost unavailable.
- Persistence notes: Output URL retention is not confirmed locally. Download returned URLs promptly.
- Limitations or warnings: Queued responses require fetch/result handling before download.

## Python Example

```python
from easy_ai_clients import music

result = music.text_to_music(
    "Upbeat acoustic pop loop for a product walkthrough.",
    api="modelslab",
    output_path="out/music.mp3",
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
