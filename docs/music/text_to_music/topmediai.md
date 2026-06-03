# TopMediai AI Music Generator Text To Music API

Implementation status: implemented

## Overview

- Operation name: `text_to_music`.
- Provider identifier: `topmediai`.
- Credential environment variable: `TOPMEDIAI_API_KEY`.
- Supported technical capabilities: prompt-led music generation from a text brief. Provider coverage includes vocal music, instrumental music, lyrics-to-song, audio reference generation, extension, singer generation, and MP4 or WAV export.

## Account And Credentials

Set `TOPMEDIAI_API_KEY` in the environment before calling this wrapper.

Requests use the `x-api-key` header.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [TopMediai API](https://docs.topmediai.com/ai-music-generator)

## Current Wrapper Default

- Default model: `v4.5-plus`.
- Endpoint or task flow: `BASE_URL` = `https://api.topmediai.com`; `GENERATE_PATH` = `/v3/music/generate`; `TASKS_PATH` = `/v3/music/tasks`; task lookup uses query parameter `ids`.

## Parameter Reference

```python
easy_ai_clients.music.text_to_music(prompt, model=None, *, api, **kwargs)
```

Required inputs:

- `prompt`, `api`, and the provider credential environment variable.
- Provider-native required input notes: action, style, lyrics, instrumental flag, title, gender or singer, uploaded audio, reference audio, and task IDs.

Optional inputs:

- `model`; provider-native fields such as style, lyrics, duration, format, seed, webhook, instrumental flags, and endpoint controls. The prompt maps to TopMediai `style` for v3 generation.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; endpoint controls may be required because this adapter path is only partially resolvable from local constants.

## Model Coverage

Documented model coverage: `v5.0`, `v4.5-plus`, and `v4.5` are documented model versions. Wrapper defaults remain operation-specific.

Current wrapper default: `v4.5-plus`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: REST task flow with generation, task query, singer generation, and format conversion endpoints. This wrapper path may need explicit endpoint or base URL kwargs before a request can be assembled.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: MP3, MP4, or WAV URLs depending on the endpoint. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use TopMediai plan or package limits. MP4 and WAV conversions can add extra credits. The wrapper marks cost unavailable.
- Persistence notes: URL retention is not confirmed locally. Download final files promptly.
- Limitations or warnings: Some wrappers need `base_url`, `endpoint`, or status endpoint controls when only endpoint paths are present locally.

## Python Example

```python
from easy_ai_clients import music

result = music.text_to_music(
    "Upbeat acoustic pop loop for a product walkthrough.",
    api="topmediai",
    output_path="out/music.mp3",
)
```

## Pricing Notes

Use TopMediai plan or package limits. MP4 and WAV conversions can add extra credits. The wrapper marks cost unavailable.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
