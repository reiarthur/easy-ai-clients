# Hedra Motion Control API

## Overview

This adapter targets Hedra `/generations` for motion-control VI2V models. The
contract requires Hedra asset ids for the source motion video and start
keyframe. Local files are uploaded to Hedra assets; remote URLs are rejected for
these id-only fields.

## Current Wrapper Default

`kling-2.6-motion-control-standard-vi2v`

## Parameters

Required inputs: `video_id` / `video_asset_id` / local `video`, and
`start_keyframe_id` / `image_id` / `image_asset_id` / local `image`.

Required kwarg: `character_orientation`.

Accepted kwargs include `duration_seconds`, `duration_ms`, `aspect_ratio`,
`resolution`, `batch_size`, `timeout_seconds`, `poll_interval_seconds`, and
`extra_payload`.

## Model Coverage

| Model | Status | Notes |
| --- | --- | --- |
| `kling-2.6-motion-control-standard-vi2v` | `implemented` | 720p, 8 credits/s, requires video + start frame + character orientation. |
| `kling-2.6-motion-control-pro-vi2v` | `implemented` | 720p, 16 credits/s, requires video + start frame + character orientation. |

## Pricing

The wrapper reports estimated Hedra credits when duration is supplied. It does
not convert Hedra credits to USD.
