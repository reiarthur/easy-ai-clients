# Hedra Image To Video API

## Overview

This adapter targets Hedra `POST /generations` with `type="video"`, a text prompt, and a start keyframe. Local images are uploaded through Hedra assets; remote images are sent as `start_keyframe_url`.

## Current Wrapper Default

`minimax-hailuo-2.3-fast-standard-i2v`

## Parameters

Required inputs: `prompt` and one of `image`, `image_path`, `image_url`, `start_keyframe_id`, or `start_keyframe_url`.

Accepted kwargs include `model`, `duration_ms`, `duration_seconds`, `aspect_ratio`, `resolution`, `batch_size`, `enhance_prompt`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`.

## Model Coverage

| Model | Status | Notes |
| --- | --- | --- |
| `grok-video-i2v` | `implemented` | Hedra catalog ID `0435547d-1b30-41ad-bf66-ca476ff0564e`, 7 credits/s. |
| `minimax-hailuo-2.3-fast-standard-i2v` | `implemented` | Default, 4 credits/s. |
| `minimax-hailuo-2.3-fast-pro-i2v`, `minimax-hailuo-2.3-standard-i2v`, `minimax-hailuo-2.3-pro-i2v`, `minimax-hailuo-02-standard-i2v`, `minimax-hailuo-02-pro-i2v` | `implemented` | Catalog-backed MiniMax image-to-video. |
| `kling-1.6-i2v`, `kling-2.1-pro-i2v`, `kling-2.1-master-i2v`, `kling-2.5-turbo-i2v`, `kling-2.6-pro-i2v`, `kling-o1-i2v`, `kling-o3-standard-i2v`, `kling-o3-pro-i2v`, `kling-v3-standard-i2v`, `kling-v3-pro-i2v` | `implemented` | Catalog-backed Kling image-to-video. |
| `veo-3-fast-i2v`, `veo-3-i2v` | `implemented` | Hedra-hosted Veo image-to-video entries. |
| `sora-2-pro-i2v`, `seedance-2.0-i2v` | `implemented` | Higher-cost catalog entries. |
| Hedra motion-control/reference rows from the planning notes | `not_implemented` | No `requires_input_video`/`requires_character_orientation` motion-control model was exposed by authenticated `GET /models` on 2026-05-14. |
| Other live Hedra I2V UUIDs | `forward_compatible` | Pass the catalog UUID as `model`; cost may be unavailable. |

## Pricing

Costs are estimated as Hedra catalog credits per second times duration and batch size. USD conversion is not documented, so `cost_usd` remains `0.0`.
