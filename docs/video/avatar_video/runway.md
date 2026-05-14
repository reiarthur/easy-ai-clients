# Runway Avatar Video API

## Overview

This adapter targets Runway `/v1/avatar_videos` with `gwm1_avatars`.

## Current Wrapper Default

`gwm1_avatars`

## Parameters

Pass `avatar`, `preset_id`, or `avatar_id`, plus `text` or `audio` / `audio_path` / `audio_url`.

Local audio files are uploaded through Runway ephemeral uploads and submitted as `runway://...` URIs. Preset avatars use `{"type": "runway-preset"}` and custom avatars use `{"type": "custom"}`.

Accepted kwargs include `voice`, `speech`, `duration_seconds`, `billing_duration_seconds`, `create_avatar`, `name`, `personality`, `avatar_voice`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`.

Passing an image is supported only with `create_avatar=True`; the wrapper first calls `video.create_avatar(..., api="runway")` and then generates the avatar video with the created custom avatar id.

## Model Coverage

| Model | Status | Notes |
| --- | --- | --- |
| `gwm1_avatars` | `implemented` | Avatar preset/custom-avatar plus speech input. |
| `/v1/realtime_sessions` | `adjacent_only` | Interactive sessions are not a generated video operation. |

## Pricing

The wrapper estimates from the published realtime line: 2 upfront credits plus 2 credits per 6 seconds, converted at `$0.01` per credit.
