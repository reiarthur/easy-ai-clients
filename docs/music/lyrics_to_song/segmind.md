# Segmind Music Lyrics To Song API

Implementation status: implemented

## Overview

- Operation name: `lyrics_to_song`.
- Provider identifier: `segmind`.
- Credential environment variable: `SEGMIND_API_KEY`.
- Supported technical capabilities: song generation where lyrics are the primary structured input. Provider coverage includes ACE-Step lyrics/vocal generation, Meta MusicGen instrumental clips, parameter control, and loops.

## Account And Credentials

Set `SEGMIND_API_KEY` in the environment before calling this wrapper.

Requests use the `x-api-key` header.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Segmind ACE-Step Music](https://www.segmind.com/models/ace-step-music/api)
- [Segmind Meta MusicGen](https://www.segmind.com/models/meta-musicgen-medium/api)

## Current Wrapper Default

- Default model: `ace-step-music`.
- Endpoint or task flow: `ENDPOINT` = `https://api.segmind.com/v1/ace-step-music`

## Parameter Reference

```python
easy_ai_clients.music.lyrics_to_song(lyrics, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `lyrics`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, genres or elements, lyrics, duration, seed, steps, CFG, lyrics strength, and base64 flag.

Optional inputs:

- `prompt`, `model`; provider-native fields such as style, duration, voice, instrumental flags, format, seed, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `ace-step-music` and `meta-musicgen-medium` are cited locally.

Current wrapper default: `ace-step-music`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST endpoint per hosted model.
- Sync/async behavior: This adapter has no dedicated async helper in this operation path. It behaves as a direct call or provider-client call for this wrapper.
- Result and download behavior: audio bytes or base64 depending on the selected hosted model. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use Segmind model credits. Text wrappers record the `segmind_model_credits` source.
- Persistence notes: Retention is not confirmed locally. Persist downloaded or decoded audio yourself.
- Limitations or warnings: Each Segmind model page has its own payload contract and limits.

## Python Example

```python
from easy_ai_clients import music

result = music.lyrics_to_song(
    "[Verse] Walking under city lights\n[Chorus] We keep moving on",
    prompt="Modern pop ballad with warm vocals.",
    api="segmind",
    output_path="out/song.mp3",
)
```

## Pricing Notes

Use Segmind model credits. Text wrappers record the `segmind_model_credits` source.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
