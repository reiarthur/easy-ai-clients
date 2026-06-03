# Replicate Hosted Music Models Text To Music API

Implementation status: implemented

## Overview

- Operation name: `text_to_music`.
- Provider identifier: `replicate`.
- Credential environment variable: `REPLICATE_API_TOKEN`.
- Supported technical capabilities: prompt-led music generation from a text brief. Provider coverage includes Python-first hosted music models for text, lyrics, vocals, audio guidance, continuation, and loops.

## Account And Credentials

Set `REPLICATE_API_TOKEN` in the environment before calling this wrapper.

Requests use the Replicate API token or Bearer token.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Replicate MiniMax Music 2.6](https://replicate.com/minimax/music-2.6)
- [Replicate Python docs](https://replicate.com/docs/get-started/python)
- [Replicate pricing](https://replicate.com/pricing)

## Current Wrapper Default

- Default model: `minimax/music-2.6`.
- Endpoint or task flow: No complete endpoint constant is defined in this wrapper path.

## Parameter Reference

```python
easy_ai_clients.music.text_to_music(prompt, model=None, *, api, **kwargs)
```

Required inputs:

- `prompt`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, lyrics, input audio or melody, duration, seed, continuation flag, and model-specific fields.

Optional inputs:

- `model`; provider-native fields such as style, lyrics, duration, format, seed, webhook, instrumental flags, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `minimax/music-2.6`, Meta MusicGen, ACE-Step, and other hosted music models are cited locally.

Current wrapper default: `minimax/music-2.6`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: Replicate Python client or HTTP Predictions API.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: `FileOutput`, URL, or prediction output depending on the selected model. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Replicate official pricing for `minimax/music-2.6` lists `$0.15` per audio output. Other Replicate models remain model-specific. The wrapper preserves provider-returned cost fields when present.
- Persistence notes: Prediction output URLs should not be treated as permanent. Download or copy results to your storage.
- Limitations or warnings: Use only models whose terms and model page match the music use case.

## Python Example

```python
from easy_ai_clients import music

result = music.text_to_music(
    "Upbeat acoustic pop loop for a product walkthrough.",
    api="replicate",
    output_path="out/music.mp3",
)
```

## Pricing Notes

Replicate official pricing for `minimax/music-2.6` lists `$0.15` per audio output. Other Replicate models remain model-specific. The wrapper preserves provider-returned cost fields when present.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
