# Scenario Meta MusicGen Text To Music API

Implementation status: implemented

## Overview

- Operation name: `text_to_music`.
- Provider identifier: `scenario`.
- Credential environment variable: `SCENARIO_API_KEY`, `SCENARIO_API_SECRET`.
- Supported technical capabilities: prompt-led music generation from a text brief. Provider coverage includes short instrumental clips, loops, samples, assets, and melody-guided generation through Meta MusicGen.

## Account And Credentials

Set `SCENARIO_API_KEY`, `SCENARIO_API_SECRET` in the environment before calling this wrapper.

Requests use Basic Auth with API key and API secret.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Scenario Meta MusicGen](https://docs.scenario.com/get-started/generation/audio-generation/audio-generation-meta)

## Current Wrapper Default

- Default model: `model_meta-musicgen`.
- Endpoint or task flow: No complete endpoint constant is defined in this wrapper path.

## Parameter Reference

```python
easy_ai_clients.music.text_to_music(prompt, model=None, *, api, **kwargs)
```

Required inputs:

- `prompt`, `api`, and the provider credential environment variable.
- Provider-native required input notes: prompt, duration, model version, seed, temperature, guidance, normalization, multiband diffusion, and input audio for melody versions.

Optional inputs:

- `model`; provider-native fields such as style, lyrics, duration, format, seed, webhook, instrumental flags, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`.

## Model Coverage

Documented model coverage: `model_meta-musicgen` with versions such as `stereo-large`, `melody-large`, and `stereo-melody-large`.

Current wrapper default: `model_meta-musicgen`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: Scenario SDK or REST custom generation endpoint with job polling.
- Sync/async behavior: The adapter exposes async helper(s): `get_generation_status`, `get_generation_result`. `sync=True` may poll where implemented; `sync=False` returns submitted task metadata when the provider returns an ID.
- Result and download behavior: asynchronous job, asset IDs, and asset URL retrieval. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Use Scenario pricing API or account billing. Text wrappers record `scenario_pricing_api` as the source.
- Persistence notes: Asset URL retention is not confirmed locally. Download asset URLs after retrieval.
- Limitations or warnings: This provider is better for short assets than long complete songs.

## Python Example

```python
from easy_ai_clients import music

result = music.text_to_music(
    "Upbeat acoustic pop loop for a product walkthrough.",
    api="scenario",
    output_path="out/music.mp3",
)
```

## Pricing Notes

Use Scenario pricing API or account billing. Text wrappers record `scenario_pricing_api` as the source.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
