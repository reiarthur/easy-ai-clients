# Musicful AI Music Text To Music API

Implementation status: implemented

## Overview

- Operation name: `text_to_music`.
- Provider identifier: `musicful`.
- Credential environment variable: `MUSICFUL_API_KEY`.
- Supported technical capabilities: prompt-led music generation from a text brief. Provider coverage includes full music, vocal songs with lyrics, auto-lyrics-style flows, instrumental generation, and prompt-to-vocals.

## Account And Credentials

Set `MUSICFUL_API_KEY` in the environment before calling this wrapper.

Requests use the `x-api-key` header.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Musicful AI Music API](https://docs.musicful.ai/api-reference/ai-music-generator/v1-generate-music)

## Current Wrapper Default

- Default model: `MFV3.0`.
- Endpoint or task flow: No complete endpoint constant is defined in this wrapper path.

## Parameter Reference

```python
easy_ai_clients.music.text_to_music(prompt, model=None, *, api, **kwargs)
```

Required inputs:

- `prompt`, `api`, and the provider credential environment variable.
- Provider-native required input notes: action, style, model version, lyrics, instrumental flag, and gender.

Optional inputs:

- `model`; provider-native fields such as style, lyrics, duration, format, seed, webhook, instrumental flags, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `MFV3.0`, `MFV2.0`, `MFV1.5X`, `MFV1.5`, and `MFV1.0`.

Current wrapper default: `MFV3.0`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST task creation with polling for music task results.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: `audio_url` for final music; additional endpoints can convert to MP4 and WAV. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use Musicful account billing and official plan or credit pricing. The wrapper records `musicful_account_billing` for text flows.
- Persistence notes: URL retention is not confirmed locally. Download `audio_url` promptly.
- Limitations or warnings: Official docs describe the Musicful API as experimental. Model and action compatibility should be validated before accepting end-user input.

## Python Example

```python
from easy_ai_clients import music

result = music.text_to_music(
    "Upbeat acoustic pop loop for a product walkthrough.",
    api="musicful",
    output_path="out/music.mp3",
)
```

## Pricing Notes

Use Musicful account billing and official plan or credit pricing. The wrapper records `musicful_account_billing` for text flows.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
