# Google Veo Video To Video API

## Overview

This adapter provides limited Gemini Developer API support for Veo 3.1 video extension requests. It uses `models/{model}:predictLongRunning` with a source video object.

## Current Wrapper Default

`veo-3.1-generate-preview`

## Parameters

Required input: `video` / `video_path` / `video_url`. Optional `prompt` guides the extension.

The wrapper enforces the documented extension constraints: `duration_seconds=8`, `resolution="720p"`, and `number_of_videos=1`.

Accepted kwargs include `aspect_ratio`, `person_generation`, `seed`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`.

## Model Coverage

| Model | Status | Notes |
| --- | --- | --- |
| `veo-3.1-generate-preview` / `veo-3.1-generate-001` | `implemented_limited` | Standard Veo 3.1 video extension path: 8s, 720p, one output. |
| `veo-3.1-fast-generate-preview` / `veo-3.1-fast-generate-001` | `implemented_limited` | Lower-cost fast extension path: 8s, 720p, one output. |
| `veo-3.1-lite-generate-preview`, Veo 3.0, Veo 2 | `not_implemented` | Official docs do not describe the same video extension input for these models. |

## Pricing

The wrapper estimates from Gemini Veo per-second pricing and sets `cost_is_estimated=True`.
