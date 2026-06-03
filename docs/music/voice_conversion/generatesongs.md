# GenerateSongs.ai Voice Conversion API

Implementation status: implemented

## Overview

- Operation name: `voice_conversion`.
- Provider identifier: `generatesongs`.
- Credential environment variable: `GENERATESONGS_API_KEY`.
- Supported technical capabilities: conversion or application of a vocal identity in a musical workflow. Provider coverage includes full song generation, lyrics-to-song, instrumental, auto-lyrics, audio reference, vocal/melody file guidance, and voice conversion-like workflows.

## Account And Credentials

Set `GENERATESONGS_API_KEY` in the environment before calling this wrapper.

Requests use Bearer API key authentication in the `gs_...` format.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [GenerateSongs.ai](https://generatesongs.ai/docs)
- [GenerateSongs.ai pricing](https://generatesongs.ai/pricing)

## Current Wrapper Default

- Default model: No explicit default model is set by this wrapper path.
- Endpoint or task flow: `BASE_URL` = `https://generatesongs.ai/api/v1`; `STATUS_ENDPOINT_PATH` = `/songs/{song_id}`; `GENERATE_ENDPOINT_PATH` = `/songs/generate`

## Parameter Reference

```python
easy_ai_clients.music.voice_conversion(audio, voice=None, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `audio`, `api`, and the provider credential environment variable. Most provider flows also need `voice` or a provider-native voice ID.
- Provider-native required input notes: style, lyrics, title, instrumental flag, vocal gender, `referenceFileId`, `vocalFileId`, and `melodyFileId`.

Optional inputs:

- `voice`, `prompt`, `model`; provider-native fields such as singer, voice ID, reference audio, style, format, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; media values may be URL, local path, bytes, or data URI when the adapter supports that transport.

## Model Coverage

Documented model coverage: `songs-generate` is used by wrapper paths where documented.

Current wrapper default: No explicit default model is set by this wrapper path.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: asynchronous REST song creation followed by song status/result fetch.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`, `download_generation`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: `songId`, status result, `downloadUrl`, and `flacDownloadUrl`. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Official docs list 1 credit per generated song. USD cost depends on the user's credit package or plan.
- Persistence notes: URL retention is not confirmed locally. Download MP3 or FLAC URLs after completion.
- Limitations or warnings: Reference, vocal, and melody files must be uploaded or identified before generation when required. Voice consent, likeness rights, and allowed-use policy checks are the caller responsibility.

## Python Example

```python
from easy_ai_clients import music

result = music.voice_conversion(
    "https://example.com/vocal.wav",
    voice="voice_id",
    prompt="Keep the original melody and timing.",
    api="generatesongs",
    output_path="out/voice.mp3",
)
```

## Pricing Notes

Official docs list 1 credit per generated song. USD cost depends on the user's credit package or plan.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
