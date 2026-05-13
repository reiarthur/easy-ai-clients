# Google Veo Image To Video API

Implementation status: implemented

## Overview

This wrapper targets Gemini Developer API Veo image-to-video generation using `models/{model}:predictLongRunning`. Snapshot date for model and pricing assumptions: 2026-05-13.

## Account And Credentials

Use `GOOGLE_API_KEY` from the environment. Local image files and HTTP/HTTPS image URLs are encoded as REST `inlineData` image bytes; non-HTTP URI references can still be supplied through explicit provider kwargs or `extra_payload` when supported by the current Google API.

## Official Sources

- Gemini video generation: https://ai.google.dev/gemini-api/docs/video
- Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
- Gemini billing: https://ai.google.dev/gemini-api/docs/billing
- Vertex Veo reference: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation

## Current Wrapper Default

`veo-3.1-lite-generate-preview`

The default is the lowest-cost documented Gemini Veo model that supports image-conditioned video in the official video and pricing docs.

## Lowest-Cost Default Policy

Prefer the cheapest documented model with image input, a public long-running operation path, and a per-second price table. Use direct Google Gemini pricing for `cost_usd`.

## Parameter Reference

Public dispatcher signature:

```python
def image_to_video(prompt, image=None, model=None, *, api, **kwargs):
    pass
```

Accepted `kwargs`: `model`, `duration_seconds`, `aspect_ratio`, `resolution`, `person_generation`, `seed`, `number_of_videos`, `last_image_url`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`.

Validated values include `aspect_ratio` `16:9` or `9:16`, model-specific durations, model-specific resolutions, `number_of_videos` 1 for Veo 3 and Veo 3.1 models or 1 to 2 for Veo 2, and seed 0 to 4294967295. Image-to-video `person_generation` is `allow_adult` for Veo 3 and Veo 3.1, and `allow_adult` or `dont_allow` for Veo 2.

Google requires `duration_seconds=8` for 1080p and 4K output. When `resolution` is 1080p or 4K and `duration_seconds` is omitted, the wrapper uses 8 seconds by default.

## Model Coverage

| Model or endpoint | Official source | Status | Implemented default | Notes |
| --- | --- | --- | --- | --- |
| `veo-3.1-lite-generate-preview` | https://ai.google.dev/gemini-api/docs/video | `implemented` | yes | Image input plus prompt, estimated from Gemini per-second pricing. |
| `veo-3.1-fast-generate-preview` | https://ai.google.dev/gemini-api/docs/video | `implemented` | no | Supports 720p, 1080p, and 4K pricing. |
| `veo-3.1-fast-generate-001` | Google model docs | `official_available` | no | Alias normalized to preview model. |
| `veo-3.1-generate-preview` | https://ai.google.dev/gemini-api/docs/video | `implemented` | no | Standard 3.1 pricing. |
| `veo-3.1-generate-001` | Google model docs | `official_available` | no | Alias normalized to preview model. |
| `veo-3.0-fast-generate-001` | https://ai.google.dev/gemini-api/docs/video | `implemented` | no | Implemented with Gemini pricing. |
| `veo-3.0-generate-001` | https://ai.google.dev/gemini-api/docs/video | `implemented` | no | Implemented with Gemini pricing. |
| `veo-2.0-generate-001` | https://ai.google.dev/gemini-api/docs/video | `implemented` | no | Implemented with 720p pricing. |

## Domain Notes

`sync=False` returns the operation name as `request_id`. Use `video.get_status`, `video.get_result`, and `video.download` with operation `image_to_video` for async follow-up work. `last_image_url` maps to the REST `lastFrame` request object where supported by current Google behavior. HTTP/HTTPS `last_image_url` values are also encoded as `inlineData`.

## Python Example

```python
from easy_ai_clients import video

result = video.image_to_video(
    "Animate the scene with a slow dolly-in and drifting fog.",
    "inputs/landscape.png",
    api="google",
    duration_seconds=4,
    output_path="outputs/google_image_to_video.mp4",
)
print(result["cost_usd"])
```

## Pricing Notes

The wrapper estimates from official Gemini Veo per-second pricing. `cost_is_estimated=True` because the operation response does not include billing records.

## Validation Note

Validated locally with package import, dispatcher, and selected parameter-validation tests. No paid Gemini Veo generation request was made.
