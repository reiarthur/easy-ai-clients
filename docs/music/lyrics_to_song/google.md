# Google Lyria 3 Lyrics To Song API

Implementation status: implemented

## Overview

- Operation name: `lyrics_to_song`.
- Provider identifier: `google`.
- Credential environment variable: `GOOGLE_API_KEY`.
- Supported technical capabilities: song generation where lyrics are the primary structured input. Provider coverage includes full-track generation, short clips, loops, vocals, lyrics-to-song, and image-guided music.

## Account And Credentials

Set `GOOGLE_API_KEY` in the environment before calling this wrapper.

Google Cloud authentication may also be used for Vertex or Cloud flows.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Google Lyria 3](https://ai.google.dev/gemini-api/docs/music-generation)
- [Google Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)

## Current Wrapper Default

- Default model: `lyria-3-pro-preview`.
- Endpoint or task flow: `ENDPOINT` = `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`

## Parameter Reference

```python
easy_ai_clients.music.lyrics_to_song(lyrics, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `lyrics`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompts, lyrics, style, language, mood, instrumentation, purpose, and image parts where supported.

Optional inputs:

- `prompt`, `model`; provider-native fields such as style, duration, voice, instrumental flags, format, seed, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `lyria-3-clip-preview` and `lyria-3-pro-preview`.

Current wrapper default: `lyria-3-pro-preview`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST or official Google Gen AI SDK generation flow.
- Sync/async behavior: This adapter has no dedicated async helper in this operation path. It behaves as a direct call or provider-client call for this wrapper.
- Result and download behavior: MP3 by default; WAV can be available in Lyria 3 Pro flows. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Official Gemini API pricing lists Lyria 3 clip and full-song request prices. The wrapper does not calculate a stable music cost per call.
- Persistence notes: Generated URL retention is not confirmed locally. Download returned audio promptly.
- Limitations or warnings: Confirm model availability, billing project, and authentication mode before production use.

## Python Example

```python
from easy_ai_clients import music

result = music.lyrics_to_song(
    "[Verse] Walking under city lights\n[Chorus] We keep moving on",
    prompt="Modern pop ballad with warm vocals.",
    api="google",
    output_path="out/song.mp3",
)
```

## Pricing Notes

Official Gemini API pricing lists Lyria 3 clip and full-song request prices. The wrapper does not calculate a stable music cost per call.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
