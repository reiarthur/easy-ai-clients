# fal.ai Image To Video API

Implementation status: implemented

## Overview

This wrapper targets fal.ai queued image-to-video generation. Snapshot date for model and pricing assumptions: 2026-05-13.

## Account And Credentials

Use `FAL_KEY` from the environment. The wrapper validates the key before submission and never logs it.

## Official Sources

- fal.ai model APIs: https://fal.ai/docs/documentation/model-apis
- fal.ai queue: https://fal.ai/docs/documentation/model-apis/inference/queue
- fal.ai pricing: https://fal.ai/docs/documentation/model-apis/pricing
- Default model page: https://fal.ai/models/fal-ai/kling-video/v1.6/pro/image-to-video/api

## Current Wrapper Default

`fal-ai/kling-video/v1.6/pro/image-to-video`

This default was selected because the official model page accepts an image and prompt through a stable schema and has a clear per-second USD price.

## Lowest-Cost Default Policy

Prefer an officially documented endpoint with prompt plus one image, fixed duration values, and deterministic per-second pricing. Candidate endpoints that require reference-video semantics, LoRA flows, or unclear billing remain documented but not executable.

## Parameter Reference

Public dispatcher signature:

```python
def image_to_video(prompt, image=None, model=None, *, api, **kwargs):
    pass
```

Normalized parameters:

| Parameter | Required | Notes |
| --- | ---: | --- |
| `prompt` | yes | Sent unchanged. |
| `image` | yes | Local file path, public URL, or data URL. |
| `output_path` | no | Downloads completed output when `sync=True`. |
| `sync` | no | `False` returns queue identifiers. |

Accepted `kwargs`: `model`, `duration`, `aspect_ratio`, `tail_image_url`, `negative_prompt`, `cfg_scale`, `static_mask_url`, `dynamic_masks`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`.

Validated values: `duration` `5` or `10`, and `aspect_ratio` `16:9`, `9:16`, or `1:1`. `cfg_scale`, `static_mask_url`, and `dynamic_masks` are forwarded because the official model schema documents them without additional wrapper-side enum or numeric bounds.

## Model Coverage

| Model or endpoint | Official source | Status | Implemented default | Notes |
| --- | --- | --- | --- | --- |
| `fal-ai/kling-video/v1.6/pro/image-to-video` | https://fal.ai/models/fal-ai/kling-video/v1.6/pro/image-to-video/api | `implemented` | yes | Estimated at `$0.098/s`. |
| `fal-ai/ltx-2-19b/distilled/image-to-video` | fal.ai model catalog | `official_available` | no | Candidate retained; schema/pricing not implemented. |
| `fal-ai/ltx-2-19b/distilled/image-to-video/lora` | fal.ai model catalog | `official_available` | no | LoRA-specific schema not normalized. |
| `fal-ai/ltx-2.3-22b/distilled/image-to-video` | fal.ai model catalog | `official_available` | no | Candidate retained. |
| `fal-ai/fast-svd-lcm` | fal.ai model catalog | `official_available` | no | Candidate retained; older SVD-style flow. |
| `fal-ai/stable-video` | fal.ai model catalog | `official_available` | no | Candidate retained; not selected as default. |
| `fal-ai/kling-video/o1/standard/reference-to-video` | fal.ai model catalog | `adjacent_only` | no | Reference-to-video behavior is closer to motion/reference workflows. |
| `fal-ai/kling-video/v2.1/pro/image-to-video` | fal.ai model catalog | `official_available` | no | Candidate retained for future explicit mapping. |
| `fal-ai/kling-video/v3/standard/image-to-video` | fal.ai model catalog | `official_available` | no | Candidate retained for future explicit mapping. |
| `fal-ai/veo3.1/fast/image-to-video` | fal.ai model catalog | `official_available` | no | Provider-backed Veo through fal.ai; direct Google wrapper exists. |
| `fal-ai/veo3.1/image-to-video` | fal.ai model catalog | `official_available` | no | Provider-backed Veo through fal.ai; not implemented here. |
| `fal-ai/bytedance/seedance/v1/pro/fast/image-to-video` | fal.ai model catalog | `official_available` | no | Candidate retained. |
| `fal-ai/bytedance/seedance/v1.5/pro/image-to-video` | fal.ai model catalog | `official_available` | no | Candidate retained. |
| `moonvalley/marey/i2v` | fal.ai model catalog | `official_available` | no | Candidate retained. |
| `fal-ai/bytedance/seedance/v1/pro/image-to-video` | fal.ai model catalog | `official_available` | no | Candidate retained. |

## Domain Notes

Use `video.get_status`, `video.get_result`, and `video.download` with operation `image_to_video` for async follow-up work. `extra_payload` is supported but can bypass validation.

## Python Example

```python
from easy_ai_clients import video

result = video.image_to_video(
    "The portrait smiles and turns toward soft window light.",
    "inputs/portrait.png",
    api="falai",
    duration="5",
    output_path="outputs/falai_image_to_video.mp4",
)
print(result["cost_usd"])
```

## Pricing Notes

The wrapper estimates `cost_usd` as `$0.098 * duration`. Usage reconciliation is not performed during safe validation, so `cost_is_estimated=True`.

## Validation Note

Validated locally with package import and dispatcher tests. No paid fal.ai generation request was made.
