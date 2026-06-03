# MiniMax Music Text To Music API

Implementation status: implemented

## Overview

- Operation name: `text_to_music`.
- Provider identifier: `minimax`.
- Credential environment variable: `MINIMAX_API_KEY`.
- Supported technical capabilities: prompt-led music generation from a text brief. Provider coverage includes vocal song generation, auto-lyrics, instrumental generation, and cover or re-style from reference audio.

## Account And Credentials

Set `MINIMAX_API_KEY` in the environment before calling this wrapper.

Requests use Bearer API key authentication.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [MiniMax Music API](https://platform.minimax.io/docs/api-reference/music-generation)
- [MiniMax Music Cover](https://platform.minimax.io/docs/api-reference/music-cover-preprocess)

## Current Wrapper Default

- Default model: `music-2.6`.
- Endpoint or task flow: `GENERATE_PATH` = `/v1/music_generation` Caller endpoint controls may be required, such as `endpoint`, `endpoint_url`, `base_url`, `status_endpoint`, or `result_endpoint`.

## Parameter Reference

```python
easy_ai_clients.music.text_to_music(prompt, model=None, *, api, **kwargs)
```

Required inputs:

- `prompt`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, lyrics, instrumental flag, lyrics optimizer, audio settings, streaming options, output format, and reference audio.

Optional inputs:

- `model`; provider-native fields such as style, lyrics, duration, format, seed, webhook, instrumental flags, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; endpoint controls may be required because this adapter path is only partially resolvable from local constants.

## Model Coverage

Documented model coverage: `music-2.6`, `music-cover`, free variants, and lyrics-generation flow.

Current wrapper default: `music-2.6`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: MiniMax REST music generation and related cover/lyrics endpoints. This wrapper path may need explicit endpoint or base URL kwargs before a request can be assembled.
- Sync/async behavior: This adapter has no dedicated async helper in this operation path. It behaves as a direct call or provider-client call for this wrapper.
- Result and download behavior: `url` or `hex` audio payloads depending on configuration. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Official pricing lists Music-2.6 at `$0.15` per generation up to 5 minutes, and lyrics generation at `$0.01` per song. The wrapper does not calculate a stable per-call cost.
- Persistence notes: Official docs state MiniMax output URLs expire after 24 hours. Download returned URL outputs before expiration.
- Limitations or warnings: Do not combine incompatible lyrics, instrumental, and lyrics optimizer modes.

## Python Example

```python
from easy_ai_clients import music

result = music.text_to_music(
    "Upbeat acoustic pop loop for a product walkthrough.",
    api="minimax",
    output_path="out/music.mp3",
)
```

## Pricing Notes

Official pricing lists Music-2.6 at `$0.15` per generation up to 5 minutes, and lyrics generation at `$0.01` per song. The wrapper does not calculate a stable per-call cost.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
