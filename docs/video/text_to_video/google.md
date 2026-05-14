# Google Veo Text To Video API

Implementation status: implemented

## Overview

This wrapper targets the Gemini Developer API long-running operation flow for prompt-only Veo generation. Snapshot date for model and pricing assumptions: 2026-05-13.

## Account And Credentials

Use `GOOGLE_API_KEY` from the environment. Create and manage keys in Google AI Studio or the Google Cloud console. The wrapper does not accept API keys as public parameters.

## Official Sources

- Gemini video generation: https://ai.google.dev/gemini-api/docs/video
- Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
- Gemini billing: https://ai.google.dev/gemini-api/docs/billing
- Vertex Veo reference for model parity notes: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation

## Current Wrapper Default

`veo-3.1-lite-generate-preview`

This is the lowest-cost documented Gemini Veo 3.1 option in the official pricing table. It supports text-to-video and a deterministic per-second estimate.

## Lowest-Cost Default Policy

Prefer Gemini Developer API models with a public model ID, public duration and resolution limits, and a published per-second USD price. Stable `*-001` aliases are documented but normalized to preview IDs when Google documentation presents them as API aliases.

## Parameter Reference

Public dispatcher signature:

```python
def text_to_video(prompt, model=None, *, api, **kwargs):
    pass
```

Accepted `kwargs`: `model`, `duration_seconds`, `aspect_ratio`, `resolution`, `person_generation`, `seed`, `number_of_videos`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`.

Validated values include `aspect_ratio` `16:9` or `9:16`, model-specific durations, model-specific resolutions, `number_of_videos` 1 for Veo 3 and Veo 3.1 models or 1 to 2 for Veo 2, and seed 0 to 4294967295. Text-to-video `person_generation` is `allow_all` for Veo 3 and Veo 3.1, and `allow_all`, `allow_adult`, or `dont_allow` for Veo 2.

Google requires `duration_seconds=8` for 1080p and 4K output. When `resolution` is 1080p or 4K and `duration_seconds` is omitted, the wrapper uses 8 seconds by default.

Documented kwargs are reference metadata only. Undocumented kwargs are forwarded; provider rejections are returned through the normalized public error shape. `extra_payload` may override the generated REST payload and should be used only after checking current Google docs.

## Model Coverage

| Model or endpoint | Official source | Status | Implemented default | Notes |
| --- | --- | --- | --- | --- |
| `veo-3.1-lite-generate-preview` | https://ai.google.dev/gemini-api/docs/video | `implemented` | yes | `$0.05/s` at 720p and `$0.08/s` at 1080p. |
| `veo-3.1-fast-generate-preview` | https://ai.google.dev/gemini-api/docs/video | `implemented` | no | 720p, 1080p, and 4K pricing supported. |
| `veo-3.1-fast-generate-001` | Google model docs | `official_available` | no | Alias normalized to `veo-3.1-fast-generate-preview` by wrapper. |
| `veo-3.1-generate-preview` | https://ai.google.dev/gemini-api/docs/video | `implemented` | no | Standard 3.1 pricing supported. |
| `veo-3.1-generate-001` | Google model docs | `official_available` | no | Alias normalized to `veo-3.1-generate-preview`. |
| `veo-3.0-fast-generate-001` | https://ai.google.dev/gemini-api/docs/video | `implemented` | no | `$0.10/s` at 720p, `$0.12/s` at 1080p, and `$0.30/s` at 4K. |
| `veo-3.0-generate-001` | https://ai.google.dev/gemini-api/docs/video | `implemented` | no | `$0.40/s` Gemini pricing. |
| `veo-2.0-generate-001` | https://ai.google.dev/gemini-api/docs/video | `implemented` | no | `$0.35/s`; no native audio in Gemini table. |

## Domain Notes

The wrapper uses `models/{model}:predictLongRunning`, polls operations, extracts the generated video URI, and downloads with the API key header when `output_path` is provided.

`sync=False` returns the operation name as `request_id`. Use `video.get_status`, `video.get_result`, and `video.download` with operation `text_to_video` for async follow-up work.

## Python Example

```python
from easy_ai_clients import video

result = video.text_to_video(
    "A cinematic orbit shot around a glass greenhouse at dusk.",
    api="google",
    duration_seconds=4,
    resolution="720p",
    output_path="outputs/google_text_to_video.mp4",
)
print(result["cost_usd"])
```

## Pricing Notes

Google responses do not expose per-request cost. The wrapper estimates `cost_usd` from official per-second pricing, `duration_seconds`, `resolution`, and `number_of_videos`. The result includes `cost_is_estimated=True`.

## Validation Note

Validated locally with package import, dispatcher, and selected parameter-validation tests. No paid Gemini Veo generation request was made.
