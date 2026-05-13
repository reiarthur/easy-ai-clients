# Runway Image To Video API

Implementation status: implemented

## Overview

This wrapper targets Runway `/v1/image_to_video` tasks. Snapshot date for model and pricing assumptions: 2026-05-13.

## Account And Credentials

Use `RUNWAYML_API_SECRET` from the environment. Requests include `X-Runway-Version: 2024-11-06`.

## Official Sources

- Runway API docs: https://docs.dev.runwayml.com/api
- Runway input assets: https://docs.dev.runwayml.com/assets/inputs
- Runway models: https://docs.dev.runwayml.com/guides/models
- Runway pricing: https://docs.dev.runwayml.com/guides/pricing

## Current Wrapper Default

`gen4_turbo`

This default was selected because it is one of the lowest-cost official Runway image-to-video models at 5 credits/s and has a direct image plus prompt contract.

## Lowest-Cost Default Policy

Prefer the lowest credits-per-second model that supports an image input and prompt through `/v1/image_to_video`.

## Parameter Reference

Public dispatcher signature:

```python
def image_to_video(prompt, image=None, model=None, *, api, **kwargs):
    pass
```

Accepted `kwargs`: `model`, `ratio`, `duration`, `seed`, `audio`, `content_moderation`, `public_figure_threshold`, `last_image_url`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`.

Model-specific validation:

| Model | Duration | Ratios | Notes |
| --- | --- | --- | --- |
| `gen4.5` | integer 2 to 10 | `1280:720`, `720:1280`, `1104:832`, `960:960`, `832:1104`, `1584:672` | 12 credits/s. |
| `gen4_turbo` | integer 2 to 10 | `1280:720`, `720:1280`, `1104:832`, `832:1104`, `960:960`, `1584:672` | 5 credits/s default. |
| `gen3a_turbo` | 5 or 10 | `768:1280`, `1280:768` | 5 credits/s; supports `last_image_url`. |
| `veo3` | 8 | `1280:720`, `720:1280`, `1080:1920`, `1920:1080` | 40 credits/s. |
| `veo3.1` | 4, 6, 8 | same Veo ratios | 20 credits/s without audio; 40 credits/s with audio. The wrapper sends `audio=False` when omitted. |
| `veo3.1_fast` | 4, 6, 8 | same Veo ratios | 10 credits/s without audio; 15 credits/s with audio. The wrapper sends `audio=False` when omitted. |

Unsupported kwargs are rejected. `extra_payload` may bypass validation.

## Model Coverage

| Model or endpoint | Official source | Status | Implemented default | Notes |
| --- | --- | --- | --- | --- |
| `gen4.5` | https://docs.dev.runwayml.com/guides/models | `implemented` | no | Implemented for image-to-video. |
| `gen4_turbo` | https://docs.dev.runwayml.com/guides/models | `implemented` | yes | Lowest-cost default. |
| `gen3a_turbo` | Runway OpenAPI/pricing docs | `implemented` | no | Implemented with 5 or 10 second duration. |
| `veo3` | https://docs.dev.runwayml.com/guides/models | `implemented` | no | Fixed 8 second duration. |
| `veo3.1` | https://docs.dev.runwayml.com/guides/models | `implemented` | no | Audio option changes cost. |
| `veo3.1_fast` | https://docs.dev.runwayml.com/guides/models | `implemented` | no | Lower-cost Veo option. |

## Domain Notes

Runway supports HTTPS, `runway://`, and data URI image inputs. The wrapper uses direct data URLs for local images. `sync=False` returns a task ID. Helper functions are available.

## Python Example

```python
from easy_ai_clients import video

result = video.image_to_video(
    "The camera pulls back as waves move across the scene.",
    "inputs/coast.png",
    api="runway",
    duration=5,
    output_path="outputs/runway_image_to_video.mp4",
)
print(result["cost_usd"])
```

## Pricing Notes

The wrapper estimates `cost_usd` from credits per second and the documented `$0.01` per credit purchase rate. Runway task objects do not expose exact per-task credit use, so `cost_is_estimated=True`.

## Validation Note

Validated locally with package import and dispatcher tests. No paid Runway task was submitted.
