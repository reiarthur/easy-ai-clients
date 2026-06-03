# Sonauto Melodia Lyrics To Song API

Implementation status: implemented

## Overview

- Operation name: `lyrics_to_song`.
- Provider identifier: `sonauto`.
- Credential environment variable: `SONAUTO_API_KEY`.
- Supported technical capabilities: song generation where lyrics are the primary structured input. Provider coverage includes full song, instrumental, lyrics, duration control, audio-guided music, extension, inpainting, streaming, and webhook workflows.

## Account And Credentials

Set `SONAUTO_API_KEY` in the environment before calling this wrapper.

Requests use Bearer API key authentication.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Sonauto Melodia API](https://sonauto.ai/developers/docs)
- [Sonauto pricing](https://sonauto.ai/developers/pricing)

## Current Wrapper Default

- Default model: `v3`.
- Endpoint or task flow: `ENDPOINT` = `https://api.sonauto.ai/v1/generations/v3`; `STATUS_ENDPOINT` = `https://api.sonauto.ai/v1/generations/status/{request_id}`; `RESULT_ENDPOINT` = `https://api.sonauto.ai/v1/generations/{request_id}`

## Parameter Reference

```python
easy_ai_clients.music.lyrics_to_song(lyrics, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `lyrics`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, tags, negative tags, lyrics, instrumental flag, duration range, format, webhook, and source audio for edits.

Optional inputs:

- `prompt`, `model`; provider-native fields such as style, duration, voice, instrumental flags, format, seed, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `v3` is the wrapper default where documented.

Current wrapper default: `v3`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: asynchronous REST generation with polling, result fetch, webhook, or streaming.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: `task_id`, status responses, `song_paths`, and streaming URLs. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use Sonauto pricing. Some wrappers implement `update_cost`; otherwise use provider billing.
- Persistence notes: Official docs state generated URLs expire after 168 hours. Download `song_paths` promptly.
- Limitations or warnings: Extension and inpainting need the right task, source audio, or region controls. Sonauto `v3` streaming docs are preview/beta.

## Python Example

```python
from easy_ai_clients import music

result = music.lyrics_to_song(
    "[Verse] Walking under city lights\n[Chorus] We keep moving on",
    prompt="Modern pop ballad with warm vocals.",
    api="sonauto",
    output_path="out/song.mp3",
)
```

## Pricing Notes

Use Sonauto pricing. Some wrappers implement `update_cost`; otherwise use provider billing.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
