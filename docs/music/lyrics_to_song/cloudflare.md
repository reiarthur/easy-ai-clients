# Cloudflare Workers AI MiniMax Music Lyrics To Song API

Implementation status: implemented

## Overview

- Operation name: `lyrics_to_song`.
- Provider identifier: `cloudflare`.
- Credential environment variable: `CLOUDFLARE_API_TOKEN`.
- Supported technical capabilities: song generation where lyrics are the primary structured input. Provider coverage includes Workers AI hosted MiniMax Music for vocal or instrumental generation, lyrics-to-song, and prompt-to-vocals.

## Account And Credentials

Set `CLOUDFLARE_API_TOKEN` in the environment before calling this wrapper.

`CLOUDFLARE_ACCOUNT_ID` is also required to assemble the REST endpoint.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Cloudflare Workers AI MiniMax Music](https://developers.cloudflare.com/ai/models/minimax/music-2.6/)

## Current Wrapper Default

- Default model: `minimax/music-2.6`.
- Endpoint or task flow: `ENDPOINT` = `https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run`

## Parameter Reference

```python
easy_ai_clients.music.lyrics_to_song(lyrics, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `lyrics`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, lyrics, `is_instrumental`, `lyrics_optimizer`, format, and sample rate.

Optional inputs:

- `prompt`, `model`; provider-native fields such as style, duration, voice, instrumental flags, format, seed, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `minimax/music-2.6`. The wrapper strips the legacy `@cf/` prefix when provided.

Current wrapper default: `minimax/music-2.6`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: single REST `ai/run` request or Workers binding style flow. REST requests use body shape `{"model": "minimax/music-2.6", "input": {...}}`.
- Sync/async behavior: This adapter has no dedicated async helper in this operation path. It behaves as a direct call or provider-client call for this wrapper.
- Result and download behavior: `result.audio` URL for final audio. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use Cloudflare Workers AI billing. Public pricing uses Workers AI neurons; model-specific cost can require account billing data.
- Persistence notes: `result.audio` retention is not confirmed locally. Download the returned URL promptly.
- Limitations or warnings: A valid account ID and token scope are required for Workers AI.

## Python Example

```python
from easy_ai_clients import music

result = music.lyrics_to_song(
    "[Verse] Walking under city lights\n[Chorus] We keep moving on",
    prompt="Modern pop ballad with warm vocals.",
    api="cloudflare",
    output_path="out/song.mp3",
)
```

## Pricing Notes

Use Cloudflare Workers AI billing. Public pricing uses Workers AI neurons; model-specific cost can require account billing data.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
