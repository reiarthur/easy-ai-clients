# fal.ai Music Models Text To Music API

Implementation status: implemented

## Overview

- Operation name: `text_to_music`.
- Provider identifier: `falai`.
- Credential environment variable: `FAL_KEY`.
- Supported technical capabilities: prompt-led music generation from a text brief. Provider coverage includes music generation, lyrics-to-song, audio-to-audio, remix, inpaint, outpaint, clips, and samples through hosted model pages.

## Account And Credentials

Set `FAL_KEY` in the environment before calling this wrapper.

Requests use `FAL_KEY` authentication.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [fal.ai MiniMax Music](https://fal.ai/models/fal-ai/minimax-music/v2.6/api)
- [fal.ai pricing](https://fal.ai/pricing)

## Current Wrapper Default

- Default model: `fal-ai/minimax-music/v2.6`.
- Endpoint or task flow: No complete endpoint constant is defined in this wrapper path.

## Parameter Reference

```python
easy_ai_clients.music.text_to_music(prompt, model=None, *, api, **kwargs)
```

Required inputs:

- `prompt`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, duration, tags, lyrics, reference audio, audio settings, and model-specific edit fields.

Optional inputs:

- `model`; provider-native fields such as style, lyrics, duration, format, seed, webhook, instrumental flags, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: MiniMax Music, ACE-Step, DiffRhythm, Sonauto v2, CassetteAI, and other hosted music models are cited locally.

Current wrapper default: `fal-ai/minimax-music/v2.6`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: fal queue, subscribe, Python client, JavaScript client, or raw HTTP depending on model.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: CDN or file URL; some models return WAV or model-specific file objects. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use the fal model pricing page. Cost is model-specific.
- Persistence notes: CDN retention is not confirmed for all models locally. Download returned files promptly.
- Limitations or warnings: Treat every fal model page as a separate payload, price, and license contract.

## Python Example

```python
from easy_ai_clients import music

result = music.text_to_music(
    "Upbeat acoustic pop loop for a product walkthrough.",
    api="falai",
    output_path="out/music.mp3",
)
```

## Pricing Notes

Use the fal model pricing page. Cost is model-specific.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
