# Hedra Video With Audio API

## Overview

This adapter targets Hedra `/generations` with `type="video_with_audio"` for
adding or generating audio for an existing video asset.

## Current Wrapper Default

No default model is used. Pass `model` or `video_generation_model_id` explicitly
because the public catalog does not expose a safe default for this flow.

## Parameters

Required input: `video_id`, `video_asset_id`, or local `video` / `video_path`.
Remote `video_url` is not accepted because the request uses `video_id`.

Optional `prompt` guides the generated audio.

Accepted kwargs include `timeout_seconds`, `poll_interval_seconds`, and
`extra_payload`.

## Model Coverage

| Model | Status | Notes |
| --- | --- | --- |
| Explicit Hedra video generation model UUID | `implemented_limited` | Caller must provide the UUID until a safe catalog default is available. |

## Pricing

Cost remains `cost_source="unavailable"` because no reliable per-request credit
or USD estimate is available for this operation without catalog metadata.
