# Hedra Text To Video API

## Overview

This adapter targets Hedra `POST /generations` with `type="video"` and text prompts. It uses `HEDRA_API_KEY` and the public model catalog IDs observed through authenticated `GET /models` on 2026-05-14.

## Current Wrapper Default

`minimax-hailuo-2.3-standard-t2v` (`MiniMax Hailuo 2.3 Standard T2V`)

## Parameters

Required input: `prompt`.

Accepted kwargs include `model`, `duration_ms`, `duration_seconds`, `aspect_ratio`, `resolution`, `batch_size`, `enhance_prompt`, `timeout_seconds`, `poll_interval_seconds`, and `extra_payload`.

## Model Coverage

| Model | Status | Notes |
| --- | --- | --- |
| `grok-video-t2v` | `implemented` | Hedra catalog ID `827122cd-5fdd-4412-86f2-554f7bb8eef9`, 7 credits/s. |
| `minimax-hailuo-2.3-standard-t2v` | `implemented` | Default, 6 credits/s. |
| `minimax-hailuo-2.3-pro-t2v`, `minimax-hailuo-02-standard-t2v`, `minimax-hailuo-02-pro-t2v` | `implemented` | MiniMax catalog entries. |
| `veo-3-fast-t2v`, `veo-3-t2v`, `veo-2-t2v` | `implemented` | Hedra-hosted Veo catalog IDs. |
| `kling-1.6-t2v`, `kling-2.1-pro-t2v`, `kling-2.1-master-t2v`, `kling-2.5-turbo-t2v`, `kling-2.6-pro-t2v`, `kling-v3-standard-t2v`, `kling-v3-pro-t2v`, `kling-o3-standard-t2v`, `kling-o3-pro-t2v` | `implemented` | Kling catalog IDs from `GET /models`. |
| `sora-2-pro-t2v`, `seedance-2.0-t2v` | `implemented` | Higher-cost catalog entries. |
| `Seedance 1.5 Pro` | `not_implemented` | Not present in the authenticated Hedra `GET /models` response on 2026-05-14; `seedance-2.0-t2v` is mapped instead. |
| Other live Hedra video models | `forward_compatible` | Pass the catalog UUID as `model`; cost is unavailable unless the wrapper has pricing metadata. |

## Pricing

Hedra reports credits, not a public USD conversion. Results include `cost_credits`, `credit_source`, `cost_usd=0.0`, and `cost_is_estimated=True`.
