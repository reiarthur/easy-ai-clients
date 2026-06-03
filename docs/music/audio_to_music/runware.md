# Runware Music Models Audio To Music API

Implementation status: implemented

## Overview

- Operation name: `audio_to_music`.
- Provider identifier: `runware`.
- Credential environment variable: `RUNWARE_API_KEY`.
- Supported technical capabilities: music generation or transformation guided by source audio. Provider coverage includes MiniMax Music, MiniMax Cover, ACE-Step, text-to-music, lyrics-to-song, audio-guided music, audio-to-audio, and continuation or repainting.

## Account And Credentials

Set `RUNWARE_API_KEY` in the environment before calling this wrapper.

Requests use Bearer API key authentication or a Runware auth task.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Runware MiniMax Music 2.6](https://runware.ai/docs/models/minimax-music-2-6)
- [Runware ACE-Step](https://runware.ai/docs/models/ace-step-v1-5-turbo)

## Current Wrapper Default

- Default model: `runware:ace-step@v1.5-turbo`.
- Endpoint or task flow: `DEFAULT_ENDPOINT` = `https://api.runware.ai/v1`

## Parameter Reference

```python
easy_ai_clients.music.audio_to_music(audio, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `audio`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, lyrics, instrumental flag, webhook, output type and format, audio settings, input audio URL or UUID, and repaint/outpaint controls.

Optional inputs:

- `prompt`, `model`; provider-native fields such as reference type, strength, duration, format, seed, webhook, upload IDs, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; media values may be URL, local path, bytes, or data URI when the adapter supports that transport.

## Model Coverage

Documented model coverage: `minimax:music@2.6`, `minimax:music@cover`, and `runware:ace-step@v1.5-turbo`.

Current wrapper default: `runware:ace-step@v1.5-turbo`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST, WebSocket, task API, and Python SDK style workflows.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: `audioURL`, `audioBase64Data`, or `audioDataURI`; webhook can deliver the final result. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use `includeCost` where supported. Official ACE-Step pricing is per generated second. The wrapper preserves provider-returned cost fields when present.
- Persistence notes: `ttl` controls generated URL lifetime when output is a URL. Prefer `uploadEndpoint` for storage you control.
- Limitations or warnings: Do not mix incompatible lyrics, instrumental, and repainting fields. Verify rights to the source audio before transformation or editing.

## Python Example

```python
from easy_ai_clients import music

result = music.audio_to_music(
    "https://example.com/reference.wav",
    prompt="Turn this melody into a polished synthwave track.",
    api="runware",
    output_path="out/remix.mp3",
)
```

## Pricing Notes

Use `includeCost` where supported. The wrapper preserves provider-returned cost fields when present; otherwise cost is unavailable locally.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
