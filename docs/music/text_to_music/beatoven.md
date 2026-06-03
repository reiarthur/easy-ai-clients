# Beatoven.ai Text To Music API

Implementation status: implemented

## Overview

- Operation name: `text_to_music`.
- Provider identifier: `beatoven`.
- Credential environment variable: `BEATOVEN_API_KEY`.
- Supported technical capabilities: prompt-led music generation from a text brief. Provider coverage includes background music, instrumental tracks, loops, soundtrack generation, and stems.

## Account And Credentials

Set `BEATOVEN_API_KEY` in the environment before calling this wrapper.

Requests use Bearer token authentication.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Beatoven.ai API](https://github.com/Beatoven/public-api/blob/main/docs/api-spec.md)
- [Beatoven.ai pricing](https://www.beatoven.ai/pricing)

## Current Wrapper Default

- Default model: `maestro`.
- Endpoint or task flow: `STATUS_PATH` = `/api/v1/tasks/{task_id}` Caller endpoint controls may be required, such as `endpoint`, `endpoint_url`, `base_url`, `status_endpoint`, or `result_endpoint`.

## Parameter Reference

```python
easy_ai_clients.music.text_to_music(prompt, model=None, *, api, **kwargs)
```

Required inputs:

- `prompt`, `api`, and the provider credential environment variable.
- Provider-native required input notes: `prompt.text`, format, looping options, and task controls.

Optional inputs:

- `model`; provider-native fields such as style, lyrics, duration, format, seed, webhook, instrumental flags, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; endpoint controls may be required because this adapter path is only partially resolvable from local constants.

## Model Coverage

Documented model coverage: `maestro`.

Current wrapper default: `maestro`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: asynchronous REST task creation followed by status polling. This wrapper path may need explicit endpoint or base URL kwargs before a request can be assembled.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: final track URL and stem URLs when available for the task. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use Beatoven pricing, account minutes, or the documented buy-minutes option. The wrapper marks cost unavailable.
- Persistence notes: URL retention is not confirmed locally. Download task outputs after completion.
- Limitations or warnings: Some wrappers require caller-supplied submit or base URLs because not every endpoint path is local.

## Python Example

```python
from easy_ai_clients import music

result = music.text_to_music(
    "Upbeat acoustic pop loop for a product walkthrough.",
    api="beatoven",
    output_path="out/music.mp3",
)
```

## Pricing Notes

Use Beatoven pricing, account minutes, or the documented buy-minutes option. The wrapper marks cost unavailable.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
