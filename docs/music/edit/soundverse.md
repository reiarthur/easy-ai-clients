# Soundverse Music Edit API

Implementation status: implemented

## Overview

- Operation name: `edit`.
- Provider identifier: `soundverse`.
- Credential environment variable: `SOUNDVERSE_API_KEY`.
- Supported technical capabilities: continuation, extension, inpainting, repainting, or repair of existing music. Provider coverage includes song generation, instrumental music, AI singing, audio reference, extension, streaming, stems, and voice conversion.

## Account And Credentials

Set `SOUNDVERSE_API_KEY` in the environment before calling this wrapper.

Requests use Bearer API key authentication.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Soundverse API](https://help.soundverse.ai/api_documentation)

## Current Wrapper Default

- Default model: No explicit default model is set by this wrapper path.
- Endpoint or task flow: `BASE_URL` = `https://api.soundverse.ai`; `EDIT_ENDPOINT_PATH` = `/v5/extend/song`; `STATUS_ENDPOINT_PATH` = `/v5/status`

## Parameter Reference

```python
easy_ai_clients.music.edit(audio, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `audio`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, lyrics, reference URL, instrumental URL, vocal URL, melody URL, audio URL, and `extend_at`.

Optional inputs:

- `prompt`, `model`; provider-native fields such as edit mode, extension point, mask or region, duration, seed, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; media values may be URL, local path, bytes, or data URI when the adapter supports that transport.

## Model Coverage

Documented model coverage: `music`, `v5-song`, v6 song generation, and provider-native model values depending on endpoint.

Current wrapper default: No explicit default model is set by this wrapper path.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST, sync endpoints, status polling, and streaming/SSE depending on endpoint. Official v6 song generation docs are available.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`, `download_generation`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: `stream_url`, `audio_url`, or `audio_data` with final audio references. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use Soundverse billing. The wrapper marks cost unavailable or response-derived.
- Persistence notes: URL retention is not confirmed locally. Download generated audio and stems promptly.
- Limitations or warnings: Reference URL workflows require rights and consent checks by the caller. Verify rights to the source audio before transformation or editing.

## Python Example

```python
from easy_ai_clients import music

result = music.edit(
    "https://example.com/song.wav",
    prompt="Extend the chorus for 30 seconds.",
    api="soundverse",
    output_path="out/extended.mp3",
)
```

## Pricing Notes

Use Soundverse billing. The wrapper marks cost unavailable or response-derived.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
