# ElevenLabs Music Stem Separation API

Implementation status: implemented

## Overview

- Operation name: `stem_separation`.
- Provider identifier: `elevenlabs`.
- Credential environment variable: `ELEVENLABS_API_KEY`.
- Supported technical capabilities: separation or retrieval of music parts such as vocals, drums, bass, melody, or grouped stem files. Provider coverage includes structured composition, vocal songs, video-to-music, and stem separation.

## Account And Credentials

Set `ELEVENLABS_API_KEY` in the environment before calling this wrapper.

Requests use the `xi-api-key` header.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [ElevenLabs Music API](https://elevenlabs.io/docs/api-reference/music/compose)

## Current Wrapper Default

- Default model: `music_v1`.
- Endpoint or task flow: No complete endpoint constant is defined in this wrapper path. Caller endpoint controls may be required, such as `endpoint`, `endpoint_url`, `base_url`, `status_endpoint`, or `result_endpoint`.

## Parameter Reference

```python
easy_ai_clients.music.stem_separation(audio, model=None, *, api, **kwargs)
```

Required inputs:

- `audio`, `api`, and the provider credential environment variable.
- Provider-native required input notes: `prompt`, `composition_plan`, section lines, video media, and source audio for stems.

Optional inputs:

- `model`; provider-native fields such as stem count, output format, task IDs, `output_path`, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; media values may be URL, local path, bytes, or data URI when the adapter supports that transport; endpoint controls may be required because this adapter path is only partially resolvable from local constants.

## Model Coverage

Documented model coverage: `music_v1`.

Current wrapper default: `music_v1`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST composition, video-to-music, or stem-separation flow. This wrapper path may need explicit endpoint or base URL kwargs before a request can be assembled.
- Sync/async behavior: This adapter has no dedicated async helper in this operation path. It behaves as a direct call or provider-client call for this wrapper.
- Result and download behavior: audio in the selected format, or ZIP output for stems. If `output_path` is supplied, the wrapper attempts to save returned stems or grouped stem artifacts when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Official ElevenLabs API pricing lists Music at `$0.15` per minute, while provider FAQ wording also references per-generation billing. The wrapper records unavailable cost metadata unless the response exposes usable cost fields.
- Persistence notes: Output URL or ZIP retention is not confirmed locally. Download final artifacts promptly.
- Limitations or warnings: Stem outputs can be ZIP files or grouped artifacts, not a single audio track.

## Python Example

```python
from easy_ai_clients import music

result = music.stem_separation(
    "https://example.com/song.wav",
    api="elevenlabs",
    output_path="out/stems.zip",
)
```

## Pricing Notes

Official ElevenLabs API pricing lists Music at `$0.15` per minute, while provider FAQ wording also references per-generation billing. The wrapper records unavailable cost metadata unless the response exposes usable cost fields.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
