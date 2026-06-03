# deAPI Text-to-Music Text To Music API

Implementation status: implemented

## Overview

- Operation name: `text_to_music`.
- Provider identifier: `deapi`.
- Credential environment variable: `DEAPI_API_KEY`.
- Supported technical capabilities: prompt-led music generation from a text brief. Provider coverage includes vocal music, instrumental generation, lyrics-to-song, parameter control, audio reference, audio-to-audio, and remix variation.

## Account And Credentials

Set `DEAPI_API_KEY` in the environment before calling this wrapper.

Requests use Bearer token authentication.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [deAPI Text-to-Music](https://docs.deapi.ai/api/v2/audio/music)
- [deAPI Text-to-Music price calculation](https://docs.deapi.ai/api/v2/audio/music-price)
- [deAPI job results](https://docs.deapi.ai/api/v2/utilities/jobs)

## Current Wrapper Default

- Default model: `ACE-Step-v1.5-turbo`.
- Endpoint or task flow: `POST https://api.deapi.ai/api/v2/audio/music`; status and results use `GET https://api.deapi.ai/api/v2/jobs/{request_id}`.

## Parameter Reference

```python
easy_ai_clients.music.text_to_music(prompt, model=None, *, api, **kwargs)
```

Required inputs:

- `prompt`, `api`, and the provider credential environment variable.
- Provider-native required input notes: caption, model, lyrics, duration, inference steps, guidance scale, seed, output format, BPM, key, time signature, vocal language, reference audio, and webhook URL.

Optional inputs:

- `model`; provider-native fields such as style, lyrics, duration, format, seed, webhook, instrumental flags, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `ACE-Step-v1.5-turbo` and other slugs returned by the deAPI model selection endpoint.

Current wrapper default: `ACE-Step-v1.5-turbo`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: multipart REST request with asynchronous polling or webhook result delivery. API v2 is the current documented API; API v1 is deprecated by deAPI docs.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: `request_id` plus `result_url` from polling or webhook. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use the official price calculation endpoint before generation. Several wrappers implement `update_cost`.
- Persistence notes: `result_url` retention is not confirmed locally. Download the result after completion.
- Limitations or warnings: Use the same model, duration, and inference settings for price calculation and generation. `reference_audio` supports common audio formats with a documented default max size of 15 MB.

## Python Example

```python
from easy_ai_clients import music

result = music.text_to_music(
    "Upbeat acoustic pop loop for a product walkthrough.",
    api="deapi",
    output_path="out/music.mp3",
)
```

## Pricing Notes

Use the official price calculation endpoint before generation. Several wrappers implement `update_cost`.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
