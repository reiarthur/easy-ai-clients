# WaveSpeedAI Song Generation Lyrics To Song API

Implementation status: implemented

## Overview

- Operation name: `lyrics_to_song`.
- Provider identifier: `wavespeedai`.
- Credential environment variable: `WAVESPEEDAI_API_KEY`.
- Supported technical capabilities: song generation where lyrics are the primary structured input. Provider coverage includes lyrics-to-song and audio-reference-guided song generation.

## Account And Credentials

Set `WAVESPEEDAI_API_KEY` in the environment before calling this wrapper.

Requests use Bearer API key authentication.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [WaveSpeedAI Song Generation](https://wavespeed.ai/models/wavespeed-ai/song-generation)

## Current Wrapper Default

- Default model: `wavespeed-ai/song-generation`.
- Endpoint or task flow: `ENDPOINT` = `https://api.wavespeed.ai/api/v3/wavespeed-ai/song-generation`; `RESULT_ENDPOINT` = `https://api.wavespeed.ai/api/v3/predictions/{request_id}/result`

## Parameter Reference

```python
easy_ai_clients.music.lyrics_to_song(lyrics, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `lyrics`, `api`, and the provider credential environment variable.
- Provider-native required input notes: `lyric`, description, `prompt_audio`, genre, guidance scale, temperature, top-k, and seed.

Optional inputs:

- `prompt`, `model`; provider-native fields such as style, duration, voice, instrumental flags, format, seed, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `wavespeed-ai/song-generation`.

Current wrapper default: `wavespeed-ai/song-generation`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST model API with polling for prediction result.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: output URL after polling by `request_id`. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Official WaveSpeedAI model pricing lists `$0.05` per run. Some wrappers attach estimated starting-price metadata.
- Persistence notes: Official docs state prediction retention is 7 days. Download returned URLs promptly.
- Limitations or warnings: Best fit is lyrics-led generation; it is not a broad editing provider.

## Python Example

```python
from easy_ai_clients import music

result = music.lyrics_to_song(
    "[Verse] Walking under city lights\n[Chorus] We keep moving on",
    prompt="Modern pop ballad with warm vocals.",
    api="wavespeedai",
    output_path="out/song.mp3",
)
```

## Pricing Notes

Official WaveSpeedAI model pricing lists `$0.05` per run. Some wrappers attach estimated starting-price metadata.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
