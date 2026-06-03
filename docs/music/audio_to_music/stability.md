# Stability AI Stable Audio Audio To Music API

Implementation status: implemented

## Overview

- Operation name: `audio_to_music`.
- Provider identifier: `stability`.
- Credential environment variable: `STABILITY_API_KEY`.
- Supported technical capabilities: music generation or transformation guided by source audio. Provider coverage includes instrumental generation, sound design, audio-to-audio, remix variation, loops, and inpainting.

## Account And Credentials

Set `STABILITY_API_KEY` in the environment before calling this wrapper.

Requests use `Authorization` with the Stability API key.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Stability AI API pricing](https://platform.stability.ai/pricing)
- [Stability AI getting started](https://platform.stability.ai/docs/getting-started)

## Current Wrapper Default

- Default model: `stable-audio-2.5`.
- Endpoint or task flow: `DEFAULT_ENDPOINT` = `https://api.stability.ai/v2beta/audio/stable-audio-2/audio-to-audio`

## Parameter Reference

```python
easy_ai_clients.music.audio_to_music(audio, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `audio`, `api`, and the provider credential environment variable.
- Provider-native required input notes: text prompts and source audio when using transformation, variation, or inpainting.

Optional inputs:

- `prompt`, `model`; provider-native fields such as reference type, strength, duration, format, seed, webhook, upload IDs, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; media values may be URL, local path, bytes, or data URI when the adapter supports that transport.

## Model Coverage

Documented model coverage: Stable Audio 2.5 and Stable Audio 3.0 are cited locally.

Current wrapper default: `stable-audio-2.5`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: Stability Platform REST flow for generation or audio transformation.
- Sync/async behavior: This adapter has no dedicated async helper in this operation path. It behaves as a direct call or provider-client call for this wrapper.
- Result and download behavior: generated or transformed audio returned by the API. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Stability billing is credit based. Official Stable Audio pricing lists credit costs by model version. The wrapper does not calculate a stable per-call cost.
- Persistence notes: Retention and deletion behavior are not confirmed locally. Store downloaded outputs yourself.
- Limitations or warnings: Payload details vary by model and endpoint version. Verify rights to the source audio before transformation or editing.

## Python Example

```python
from easy_ai_clients import music

result = music.audio_to_music(
    "https://example.com/reference.wav",
    prompt="Turn this melody into a polished synthwave track.",
    api="stability",
    output_path="out/remix.mp3",
)
```

## Pricing Notes

Stability billing is credit based. Official Stable Audio pricing lists credit costs by model version. The wrapper does not calculate a stable per-call cost.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
