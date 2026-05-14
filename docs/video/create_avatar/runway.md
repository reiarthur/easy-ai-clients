# Runway Create Avatar API

## Overview

This adapter targets Runway `/v1/avatars` for custom avatar creation from a
reference image. Local images are uploaded through Runway ephemeral uploads and
sent as `runway://...` URIs.

## Current Wrapper Default

`gwm1_avatars`

## Parameters

Required inputs: `image` / `image_path` / `image_url`, `name`, and `voice`.

`voice` may be a preset id such as `clara`, which is normalized to
`{"type": "runway-live-preset", "presetId": "clara"}`, or a provider-native
voice object.

Accepted kwargs include `personality`, `timeout_seconds`, and `extra_payload`.

## Model Coverage

| Model | Status | Notes |
| --- | --- | --- |
| `gwm1_avatars` | `implemented` | Custom avatar creation through Runway Characters API. |

## Pricing

The wrapper returns `cost_source="unavailable"` because avatar creation
responses do not expose per-request USD cost.
