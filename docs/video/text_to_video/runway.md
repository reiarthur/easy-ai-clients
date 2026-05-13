# Runway Text To Video API

Implementation status: implemented

## Overview

This wrapper targets Runway `/v1/text_to_video` async tasks. Snapshot date for model and pricing assumptions: 2026-05-13.

## Account And Credentials

Use `RUNWAYML_API_SECRET` from the environment. Requests send `Authorization: Bearer` and `X-Runway-Version: 2024-11-06`.

## Official Sources

- Runway API docs: https://docs.dev.runwayml.com/api
- Runway models: https://docs.dev.runwayml.com/guides/models
- Runway pricing: https://docs.dev.runwayml.com/guides/pricing
- Runway usage and tiers: https://docs.dev.runwayml.com/usage/tiers

## Current Wrapper Default

`veo3.1_fast`

The default was selected because it is the lowest-cost Runway text-to-video model listed in the official pricing table when audio is disabled.

## Lowest-Cost Default Policy

Prefer the lowest-cost official text-to-video endpoint with published credits per second and a documented USD credit purchase rate. `audio=False` is the cost-minimizing default for Veo 3.1 Fast.

## Parameter Reference

Public dispatcher signature:

```python
def text_to_video(prompt, model=None, *, api, **kwargs):
    pass
```

Accepted `kwargs`: `model`, `ratio`, `duration`, `seed`, `audio`, `content_moderation`, `public_figure_threshold`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`.

Model-specific validation:

| Model | Duration | Ratios | Notes |
| --- | --- | --- | --- |
| `gen4.5` | 2 to 10 | `1280:720`, `720:1280` | Supports `seed`; 12 credits/s. |
| `veo3` | 8 | `1280:720`, `720:1280`, `1080:1920`, `1920:1080` | 40 credits/s. |
| `veo3.1` | 4, 6, 8 | same Veo ratios | 20 credits/s without audio; 40 credits/s with audio. The wrapper sends `audio=False` when omitted. |
| `veo3.1_fast` | 4, 6, 8 | same Veo ratios | 10 credits/s without audio; 15 credits/s with audio. The wrapper sends `audio=False` when omitted. |

Runway's OpenAPI schema requires integer seconds for the `gen4.5` duration. Unsupported kwargs are rejected. `extra_payload` may bypass wrapper validation.

## Model Coverage

| Model or endpoint | Official source | Status | Implemented default | Notes |
| --- | --- | --- | --- | --- |
| `gen4.5` | https://docs.dev.runwayml.com/guides/models | `implemented` | no | Implemented for `/v1/text_to_video`. |
| `veo3` | https://docs.dev.runwayml.com/guides/models | `implemented` | no | Implemented with fixed 8 second duration. |
| `veo3.1` | https://docs.dev.runwayml.com/guides/models | `implemented` | no | Audio option changes credit rate. |
| `veo3.1_fast` | https://docs.dev.runwayml.com/guides/models | `implemented` | yes | Lowest-cost default with `audio=False`. |

## Domain Notes

Runway generation is async. `sync=True` submits a task, polls `GET /v1/tasks/{id}`, and downloads the first output URL when requested. `sync=False` returns the task ID immediately. Use `video.get_status`, `video.get_result`, and `video.download` with operation `text_to_video` for async follow-up work.

## Python Example

```python
from easy_ai_clients import video

result = video.text_to_video(
    "A handheld documentary shot of a small robot watering plants.",
    api="runway",
    duration=4,
    output_path="outputs/runway_text_to_video.mp4",
)
print(result["cost_usd"])
```

## Pricing Notes

Runway tasks do not expose per-task credit usage. The wrapper estimates credits from official credits per second and converts with the documented `$0.01` per credit purchase rate. Results include `cost_credits`, `credit_source`, and `cost_is_estimated=True`.

## Validation Note

Validated locally with package import and dispatcher tests. No paid Runway task was submitted.
