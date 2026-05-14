# Runway Video To Video API

## Overview

This adapter targets Runway `/v1/video_to_video` for `gen4_aleph`.

## Current Wrapper Default

`gen4_aleph`

## Parameters

Required input: `video` / `video_path` / `video_url`. Local files are uploaded through Runway ephemeral uploads and submitted as `runway://...` URIs.

Optional `prompt`, `image`, or `reference` can guide the edit. Runway accepts at most one image/reference asset for this endpoint.

Accepted kwargs include `ratio`, `seed`, `billing_duration_seconds`, `duration_seconds`, `duration`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`. Duration fields are used only for local cost estimation and are not sent to the `/v1/video_to_video` payload.

## Model Coverage

| Model | Status | Notes |
| --- | --- | --- |
| `gen4_aleph` | `implemented` | `/v1/video_to_video`, estimated at 15 credits/s. |
| Other Runway edit/session endpoints | `adjacent_only` | Realtime sessions and non-video outputs are not exposed through this operation. |

## Pricing

Runway costs are estimated from published credits per second and `$0.01` per credit.
