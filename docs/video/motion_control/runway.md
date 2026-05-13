# Runway Motion Control API

Implementation status: implemented

## Overview

This wrapper targets Runway Act-Two character performance through `/v1/character_performance`. Snapshot date for model and pricing assumptions: 2026-05-13.

## Account And Credentials

Use `RUNWAYML_API_SECRET` from the environment. Requests include `Authorization: Bearer` and `X-Runway-Version: 2024-11-06`.

## Official Sources

- Runway API docs: https://docs.dev.runwayml.com/api
- Runway models: https://docs.dev.runwayml.com/guides/models
- Runway pricing: https://docs.dev.runwayml.com/guides/pricing
- Runway character concepts: https://docs.dev.runwayml.com/characters/concepts

## Current Wrapper Default

`act_two`

This is the official Runway model that clearly fits motion/performance transfer.

## Lowest-Cost Default Policy

Use `act_two` because it is the only true motion-control candidate and has published 5 credits/s pricing. Generic video editing endpoints are documented as adjacent.

## Parameter Reference

Public dispatcher signature:

```python
def motion_control(prompt=None, image=None, video=None, reference=None, model=None, *, api, **kwargs):
    pass
```

Required normalized inputs: a character image through `image_path` or `image_url`, or a character video through `video_path` or `video_url`; and a driving performance video through `reference_path` or `reference_url`. `duration_seconds` or `billing_duration_seconds` is required for cost estimation.

Accepted `kwargs`: `model`, `duration_seconds`, `billing_duration_seconds`, `body_control`, `bodyControl`, `expression_intensity`, `expressionIntensity`, `ratio`, `seed`, `content_moderation`, `public_figure_threshold`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`.

Validated values: `duration_seconds` 3 to 30, `expressionIntensity` 1 to 5, seed 0 to 4294967295, and ratios `1280:720`, `720:1280`, `960:960`, `1104:832`, `832:1104`, or `1584:672`.

## Model Coverage

| Model or endpoint | Official source | Status | Implemented default | Notes |
| --- | --- | --- | --- | --- |
| `act_two` `/v1/character_performance` | https://docs.dev.runwayml.com/api | `implemented` | yes | Character image/video plus driving reference video. |
| `gen4_aleph` `/v1/video_to_video` | https://docs.dev.runwayml.com/api | `adjacent_only` | no | Generic video-to-video editing; not true motion-control transfer. |
| `/v1/video_to_video` | https://docs.dev.runwayml.com/api | `adjacent_only` | no | Edit endpoint outside fixed motion-control contract. |
| `/v1/realtime_sessions` | https://docs.dev.runwayml.com/api | `adjacent_only` | no | Realtime avatar session, not generated motion-control video. |

## Domain Notes

`prompt` is rejected for Act-Two because the official contract uses character and reference media rather than a prompt. `sync=False` returns the Runway task ID. Helper functions are available.

## Python Example

```python
from easy_ai_clients import video

result = video.motion_control(
    image="inputs/character.png",
    reference="inputs/performance.mp4",
    api="runway",
    duration_seconds=6,
    output_path="outputs/runway_motion_control.mp4",
)
print(result["cost_usd"])
```

## Pricing Notes

Act-Two is estimated at 5 credits/s. The wrapper converts credits to USD with the documented `$0.01` per credit purchase rate and returns `cost_credits`, `credit_source`, and `cost_is_estimated=True`.

## Validation Note

Validated locally with package import and dispatcher tests. No paid Runway task was submitted.
