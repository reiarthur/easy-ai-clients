# Jen Music Music Edit API

Implementation status: implemented

## Overview

- Operation name: `edit`.
- Provider identifier: `jen`.
- Credential environment variable: `JEN_MUSIC_API_KEY`.
- Supported technical capabilities: continuation, extension, inpainting, repainting, or repair of existing music. Provider coverage includes text-to-track generation and extension of existing tracks.

## Account And Credentials

Set `JEN_MUSIC_API_KEY` in the environment before calling this wrapper.

API access requires onboarding or approval before use.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Jen Music API](https://api.jenmusic.ai/docs/getting-started)
- [Jen Music pricing](https://api.jenmusic.ai/docs/pricing)

## Current Wrapper Default

- Default model: No explicit default model is set by this wrapper path.
- Endpoint or task flow: `STATUS_ENDPOINT_PATH` = `/api/v3/public/generation_status/{track_id}` Caller endpoint controls may be required, such as `endpoint`, `endpoint_url`, `base_url`, `status_endpoint`, or `result_endpoint`.

## Parameter Reference

```python
easy_ai_clients.music.edit(audio, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `audio`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt and duration for generation; track ID for extension flows.

Optional inputs:

- `prompt`, `model`; provider-native fields such as edit mode, extension point, mask or region, duration, seed, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; media values may be URL, local path, bytes, or data URI when the adapter supports that transport; endpoint controls may be required because this adapter path is only partially resolvable from local constants.

## Model Coverage

Documented model coverage: No stable default model is documented locally.

Current wrapper default: No explicit default model is set by this wrapper path.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: asynchronous REST generation or extension with status polling. This wrapper path may need explicit endpoint or base URL kwargs before a request can be assembled.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`, `download_generation`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: temporary MP3 or WAV URL when the task completes. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use Jen pricing. Some wrappers implement `update_cost` from official pricing metadata.
- Persistence notes: Official docs state returned file URLs are valid for 24 hours.
- Limitations or warnings: Public API access may not be available until the provider approves the account. Official limits include 150 requests per 10 seconds and 10 concurrent generations. Verify rights to the source audio before transformation or editing.

## Python Example

```python
from easy_ai_clients import music

result = music.edit(
    "https://example.com/song.wav",
    prompt="Extend the chorus for 30 seconds.",
    api="jen",
    output_path="out/extended.mp3",
)
```

## Pricing Notes

Use Jen pricing. Some wrappers implement `update_cost` from official pricing metadata.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
