# Stability AI Stable Audio Music Edit API

Implementation status: implemented

## Overview

- Operation name: `edit`.
- Provider identifier: `stability`.
- Credential environment variable: `STABILITY_API_KEY`.
- Supported technical capabilities: continuation, extension, inpainting, repainting, or repair of existing music. Provider coverage includes instrumental generation, sound design, audio-to-audio, remix variation, loops, and inpainting.

## Account And Credentials

Set `STABILITY_API_KEY` in the environment before calling this wrapper.

Requests use `Authorization` with the Stability API key.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Stability AI API pricing](https://platform.stability.ai/pricing)
- [Stability AI getting started](https://platform.stability.ai/docs/getting-started)

## Current Wrapper Default

- Default model: `stable-audio-2.5`.
- Endpoint or task flow: No complete endpoint constant is defined in this wrapper path. Caller endpoint controls may be required, such as `endpoint`, `endpoint_url`, `base_url`, `status_endpoint`, or `result_endpoint`.

## Parameter Reference

```python
easy_ai_clients.music.edit(audio, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `audio`, `api`, and the provider credential environment variable.
- Provider-native required input notes: text prompts and source audio when using transformation, variation, or inpainting.

Optional inputs:

- `prompt`, `model`; provider-native fields such as edit mode, extension point, mask or region, duration, seed, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; media values may be URL, local path, bytes, or data URI when the adapter supports that transport; endpoint controls may be required because this adapter path is only partially resolvable from local constants.

## Model Coverage

Documented model coverage: Stable Audio 2.5 and Stable Audio 3.0 are cited locally.

Current wrapper default: `stable-audio-2.5`.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: Stability Platform REST flow for generation or audio transformation. This wrapper path may need explicit endpoint or base URL kwargs before a request can be assembled.
- Sync/async behavior: This adapter has no dedicated async helper in this operation path. It behaves as a direct call or provider-client call for this wrapper.
- Result and download behavior: generated or transformed audio returned by the API. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Stability billing is credit based. Official Stable Audio pricing lists credit costs by model version. The wrapper does not calculate a stable per-call cost.
- Persistence notes: Retention and deletion behavior are not confirmed locally. Store downloaded outputs yourself.
- Limitations or warnings: Payload details vary by model and endpoint version. Verify rights to the source audio before transformation or editing.

## Python Example

```python
from easy_ai_clients import music

result = music.edit(
    "https://example.com/song.wav",
    prompt="Extend the chorus for 30 seconds.",
    api="stability",
    output_path="out/extended.mp3",
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
