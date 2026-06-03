# Musicfy Voice Conversion API

Implementation status: implemented

## Overview

- Operation name: `voice_conversion`.
- Provider identifier: `musicfy`.
- Credential environment variable: `MUSICFY_API_KEY`.
- Supported technical capabilities: conversion or application of a vocal identity in a musical workflow. Provider coverage includes text-to-music, audio-to-music, cover-style workflows, and voice conversion.

## Account And Credentials

Set `MUSICFY_API_KEY` in the environment before calling this wrapper.

Requests use Bearer token authentication.

Do not pass credentials through kwargs. The public dispatcher rejects credential-like kwargs.

## Official Sources

- [Musicfy API](https://docs.musicfy.lol/)
- [Musicfy API pricing](https://docs.musicfy.lol/pricing)

## Current Wrapper Default

- Default model: No explicit default model is set by this wrapper path.
- Endpoint or task flow: No complete endpoint constant is defined in this wrapper path. Caller endpoint controls may be required, such as `endpoint`, `endpoint_url`, `base_url`, `status_endpoint`, or `result_endpoint`.

## Parameter Reference

```python
easy_ai_clients.music.voice_conversion(audio, voice=None, prompt=None, model=None, *, api, **kwargs)
```

Required inputs:

- `audio`, `api`, and the provider credential environment variable. Most provider flows also need `voice` or a provider-native voice ID.
- Provider-native required input notes: prompt text, voice identifiers, style controls, duration, format, and source audio for vocal transformation.

Optional inputs:

- `voice`, `prompt`, `model`; provider-native fields such as singer, voice ID, reference audio, style, format, webhook, and endpoint controls.
- Provider-native kwargs are forwarded whenever a request can be assembled.
- Common wrapper controls include `output_path`, `sync`, `timeout`, `retries`, `poll_interval`, and `max_polls`; media values may be URL, local path, bytes, or data URI when the adapter supports that transport; endpoint controls may be required because this adapter path is only partially resolvable from local constants.

## Model Coverage

Documented model coverage: No stable default model is documented locally for most Musicfy wrappers.

Current wrapper default: No explicit default model is set by this wrapper path.

Pass `model=...` to override when the adapter and provider endpoint support model selection.

## Domain Notes

- Endpoint or task flow: HTTPS REST flow for Musicfy generation or conversion endpoints. This wrapper path may need explicit endpoint or base URL kwargs before a request can be assembled.
- Sync/async behavior: This adapter has no dedicated async helper in this operation path. It behaves as a direct call or provider-client call for this wrapper.
- Result and download behavior: JSON with generated or converted audio references. If `output_path` is supplied, the wrapper attempts to save returned audio when a final URL, bytes, base64, data URI, or compatible provider object is present.
- Cost behavior: Official docs list generated audio pricing at `$0.07` per minute. The wrapper marks cost unavailable unless response usage is provided.
- Persistence notes: Official docs state generated file URLs are short lived and deleted after 1 hour.
- Limitations or warnings: Voice and cover workflows require consent and rights checks by the caller. Voice consent, likeness rights, and allowed-use policy checks are the caller responsibility.

## Python Example

```python
from easy_ai_clients import music

result = music.voice_conversion(
    "https://example.com/vocal.wav",
    voice="voice_id",
    prompt="Keep the original melody and timing.",
    api="musicfy",
    output_path="out/voice.mp3",
)
```

## Pricing Notes

Official docs list generated audio pricing at `$0.07` per minute. The wrapper marks cost unavailable unless response usage is provided.

The normalized result may include `cost_usd`, `cost_is_estimated`, `cost_source`, and `cost_details`. Treat missing or unavailable cost metadata as a signal to reconcile against provider billing.

## Validation Note

This page documents the local wrapper contract only. Safe validation must avoid live provider calls.

Use:

```bash
python -m compileall -q src/easy_ai_clients/music
```
