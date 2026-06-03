# TopMediai AI Music Generator Voice Conversion API

Implementation status: implemented

## Overview

- Operation name: `voice_conversion`.
- Provider identifier: `topmediai`.
- Credential environment variable: `TOPMEDIAI_API_KEY`.
- Supported technical capabilities: conversion or application of a vocal identity in a musical workflow. Provider coverage includes vocal music, instrumental music, lyrics-to-song, audio reference generation, extension, singer generation, and MP4 or WAV export.

## Account And Credentials

Set `TOPMEDIAI_API_KEY` in the environment before calling this wrapper.

Requests use the `x-api-key` header.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [TopMediai API](https://docs.topmediai.com/ai-music-generator)

## Current Wrapper Default

- Default model: `v4.5-plus`.
- Endpoint or task flow: `BASE_URL` = `https://api.topmediai.com`; `VOICE_ENDPOINT_PATH` = `/v3/music/generate-singer`; `STATUS_ENDPOINT_PATH` = `/v3/music/tasks`; task lookup uses query parameter `ids`.

## Parameter Reference

```python
easy_ai_clients.music.voice_conversion(audio, voice=None, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `audio`, `api`, and the provider credential environment variable. Most provider flows also need `voice` or a provider-native voice ID.
- Provider-native required input notes: action, style, lyrics, instrumental flag, title, gender or singer, uploaded audio, reference audio, and task IDs.

Optional inputs:

- `voice`, `prompt`, `model`; provider-native fields such as singer, voice ID, reference audio, style, format, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; media values may be URL, local path, bytes, or data URI when the adapter supports that transport; endpoint controls may be required because this adapter path is only partially resolvable from local constants.

## Model Coverage

Documented model coverage: `v5.0`, `v4.5-plus`, and `v4.5` are documented model versions. Wrapper defaults remain operation-specific.

Current wrapper default: `v4.5-plus`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST task flow with generation, task query, singer generation, and format conversion endpoints. This wrapper path may need explicit endpoint or base URL kwargs before a request can be assembled.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`, `download_generation`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: MP3, MP4, or WAV URLs depending on the endpoint. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use TopMediai plan or package limits. MP4 and WAV conversions can add extra credits. The wrapper marks cost unavailable.
- Persistence notes: URL retention is not confirmed locally. Download final files promptly.
- Limitations or warnings: Some wrappers need `base_url`, `endpoint`, or status endpoint controls when only endpoint paths are present locally. Voice consent, likeness rights, and allowed-use policy checks are the caller responsibility.

## Python Example

```python
from easy_ai_clients import music

result = music.voice_conversion(
    "https://example.com/vocal.wav",
    voice="voice_id",
    prompt="Keep the original melody and timing.",
    api="topmediai",
    output_path="out/voice.mp3",
)
```

## Pricing Notes

Use TopMediai plan or package limits. MP4 and WAV conversions can add extra credits. The wrapper marks cost unavailable.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
