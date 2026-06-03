# MusicGPT Text To Music API

Implementation status: implemented

## Overview

- Operation name: `text_to_music`.
- Provider identifier: `musicgpt`.
- Credential environment variable: `MUSICGPT_API_KEY`.
- Supported technical capabilities: prompt-led music generation from a text brief. Provider coverage includes prompt-to-song, lyrics-to-song, auto-lyrics, remix, extension, inpainting, image-to-song, cover, and voice changer workflows.

## Account And Credentials

Set `MUSICGPT_API_KEY` in the environment before calling this wrapper.

Requests use an API key in `Authorization`.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [MusicGPT API](https://docs.musicgpt.com/api-documentation/conversions/musicai)
- [MusicGPT pricing](https://docs.musicgpt.com/api-documentation/index/pricing)

## Current Wrapper Default

- Default model: No explicit default model is set by this wrapper path.
- Endpoint or task flow: `ENDPOINT` = `https://api.musicgpt.com/api/public/v1/MusicAI`; status/result lookup uses `https://api.musicgpt.com/api/public/v1/byId` with `conversionType=MUSIC_AI` and `task_id`.

## Parameter Reference

```python
easy_ai_clients.music.text_to_music(prompt, model=None, *, api, **kwargs)
```

Required inputs:

- `prompt`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, style, lyrics, instrumental or vocal-only flags, genre, voice ID, duration, image, audio, and webhook fields.

Optional inputs:

- `model`; provider-native fields such as style, lyrics, duration, format, seed, webhook, instrumental flags, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `MusicAI` is used by several wrapper paths; other task models can be passed where supported.

Current wrapper default: No explicit default model is set by this wrapper path.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST task flow with optional status endpoint, result endpoint, or webhook.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: task, status, webhook, or CDN URLs for final audio. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use MusicGPT Free, Plus, Pro, or Enterprise plan pricing. Some status and webhook responses include `credit_estimate` or `conversion_cost`; the wrapper marks cost unavailable unless usable response fields are present.
- Persistence notes: CDN URL retention is not confirmed locally. Download outputs after completion.
- Limitations or warnings: Separate MusicGPT task endpoints by use case to avoid mixed payload contracts.

## Python Example

```python
from easy_ai_clients import music

result = music.text_to_music(
    "Upbeat acoustic pop loop for a product walkthrough.",
    api="musicgpt",
    output_path="out/music.mp3",
)
```

## Pricing Notes

Use MusicGPT Free, Plus, Pro, or Enterprise plan pricing. Some status and webhook responses include `credit_estimate` or `conversion_cost`; the wrapper marks cost unavailable unless usable response fields are present.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
