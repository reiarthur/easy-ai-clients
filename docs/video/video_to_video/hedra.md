# Hedra Video To Video API

## Overview

This adapter targets Hedra `/generations` for catalog-backed video-to-video
models that require a Hedra video asset id. Local video and image files are
uploaded to Hedra assets before the generation request. Remote URLs are rejected
for fields that Hedra documents as asset ids.

## Current Wrapper Default

`kling-o3-standard-edit-v2v`

## Parameters

Required input: `video_id`, `video_asset_id`, or local `video` / `video_path`.
Remote `video_url` is not accepted by this wrapper because the generation
contract uses `video_id`.

Required prompt: `prompt`.

Optional references: `reference_image_ids`, `reference_image_asset_ids`,
`reference_image_id`, `image_id`, `image_asset_id`, local `image`, or local
`reference`. The submitted payload uses Hedra's documented
`reference_image_ids` field.

Accepted kwargs include `duration_seconds`, `duration_ms`, `aspect_ratio`,
`resolution`, `keep_audio`, `elements`, `batch_size`, `timeout_seconds`,
`poll_interval_seconds`, and `extra_payload`.

## Model Coverage

| Model | Status | Notes |
| --- | --- | --- |
| `kling-o3-standard-edit-v2v` | `implemented` | 720p, 30 credits/s, edit V2V. |
| `kling-o3-pro-edit-v2v` | `implemented` | 1080p, 35 credits/s, edit V2V. |
| `kling-o3-standard-reference-v2v` | `implemented` | 720p, 30 credits/s, reference V2V. |
| `kling-o3-pro-reference-v2v` | `implemented` | 1080p, 35 credits/s, reference V2V. |

## Pricing

The wrapper reports estimated Hedra credits from the authenticated model
catalog. It does not convert Hedra credits to USD.
