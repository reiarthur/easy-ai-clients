# Novita AI MiniMax Music Lyrics To Song API

Implementation status: implemented

## Overview

- Operation name: `lyrics_to_song`.
- Provider identifier: `novita`.
- Credential environment variable: `NOVITA_API_KEY`.
- Supported technical capabilities: song generation where lyrics are the primary structured input. Provider coverage includes MiniMax-hosted vocal generation, structured lyrics, auto-lyrics, instrumental generation, and prompt-to-vocals.

## Account And Credentials

Set `NOVITA_API_KEY` in the environment before calling this wrapper.

Requests use Bearer API key authentication.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Novita AI MiniMax Music](https://novita.ai/docs/api-reference/model-apis-minimax-music)

## Current Wrapper Default

- Default model: `music-2.5+`.
- Endpoint or task flow: `ENDPOINT` = `https://api.novita.ai/v3/minimax-music`

## Parameter Reference

```python
easy_ai_clients.music.lyrics_to_song(lyrics, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `lyrics`, `api`, and the provider credential environment variable.
- Provider-native required input notes: model, lyrics, prompt, audio setting, output format, `aigc_watermark`, instrumental flag, and lyrics optimizer.

Optional inputs:

- `prompt`, `model`; provider-native fields such as style, duration, voice, instrumental flags, format, seed, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `music-2.5+`, `music-2.5`, and `music-2.0`.

Current wrapper default: `music-2.5+`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: single REST call to Novita-hosted MiniMax Music endpoint.
- Sync/async behavior: This adapter has no dedicated async helper in this operation path. It behaves as a direct call or provider-client call for this wrapper.
- Result and download behavior: `audios` list with URLs. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use Novita billing and credit usage. The wrapper records provider billing as the source where implemented.
- Persistence notes: `audios` URL retention is not confirmed locally. Download all returned URLs promptly.
- Limitations or warnings: Validate model support before using instrumental or lyrics optimizer flags. The official watermark field is `aigc_watermark`; the wrapper keeps `watermark` as a compatibility alias.

## Python Example

```python
from easy_ai_clients import music

result = music.lyrics_to_song(
    "[Verse] Walking under city lights\n[Chorus] We keep moving on",
    prompt="Modern pop ballad with warm vocals.",
    api="novita",
    output_path="out/song.mp3",
)
```

## Pricing Notes

Use Novita billing and credit usage. The wrapper records provider billing as the source where implemented.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
