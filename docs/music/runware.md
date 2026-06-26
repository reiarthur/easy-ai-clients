# Runware ACE-Step Provider

Public dispatcher: `music.generate(..., api="runware")`.

## Public Models

| Native model ID | Standard model key | Default |
| --- | --- | ---: |
| `runware:ace-step@v1.5-turbo` | `ace_step_v1_5_turbo` | No |
| `runware:ace-step@v1.5-xl-base` | `ace_step_v1_5_xl_base` | No |
| `runware:ace-step@v1.5-xl-turbo` | `ace_step_v1_5_xl_turbo` | Yes |
| `runware:ace-step@v1.5-xl-sft` | `ace_step_v1_5_xl_sft` | No |

`model` may be either the native model ID or the standard model key.

When `model` is omitted, `music.generate(..., api="runware")` uses
`runware:ace-step@v1.5-xl-turbo`.

## Endpoint And Flow

| Purpose | Endpoint |
| --- | --- |
| Submit `audioInference` task | `https://api.runware.ai/v1` |
| Poll or fetch result with `getResponse` | `https://api.runware.ai/v1` |

Credential variable: `RUNWARE_API_KEY`.

The wrapper submits an async `audioInference` task.

`music.get_status()` and `music.download_result()` call Runware `getResponse`
with the stored `taskUUID`.

## Public Call

```python
from easy_ai_clients import music

generation = music.generate(
    lyrics="...",
    api="runware",
    model="ace_step_v1_5_xl_turbo",
    style="rock",
)

generation = music.get_status(generation)
generation = music.download_result(generation)
```

## Accepted Parameters

`style` or `prompt` is required.

If both are passed, `prompt` wins.

When `style` is used, the local preset provides `style_prompts` and
`voice_presets`. `style_prompts` has `small`, `medium`, and `large` strings.
`voice_presets` has `default_gender` plus `small`, `medium`, and `large`
male/female maps. If provider input limits are exceeded, the router tries
smaller preset prompt variants before raising `MusicInputLimitError`.

Local prompt controls:

| Parameter | Behavior |
| --- | --- |
| `language` | Overrides preset language and maps to ACE-Step `settings.vocalLanguage`. |
| `gender` | Selects `male`, `female`, or `both` voice guidance from `voice_presets`. |
| `voice_description` | Replaces preset voice guidance with caller-provided voice text. |

Duration behavior:

| Standard model key | Native model ID | Min | Max | Missing or invalid `duration` | Provider application |
| --- | --- | ---: | ---: | --- | --- |
| `ace_step_v1_5_turbo` | `runware:ace-step@v1.5-turbo` | `30s` | `300s` | Uses `60s` | Sent as `duration` |
| `ace_step_v1_5_xl_base` | `runware:ace-step@v1.5-xl-base` | `30s` | `300s` | Uses `60s` | Sent as `duration` |
| `ace_step_v1_5_xl_sft` | `runware:ace-step@v1.5-xl-sft` | `30s` | `300s` | Uses `60s` | Sent as `duration` |
| `ace_step_v1_5_xl_turbo` | `runware:ace-step@v1.5-xl-turbo` | `30s` | `300s` | Uses `60s` | Sent as `duration` |

| Parameter | Behavior |
| --- | --- |
| `duration` | Always sent as `duration`. Numeric values are clamped to `30` to `300`. Missing or invalid values use `60`. |
| `steps` | Sent as `steps`. When omitted, the wrapper sends a safe model-specific default. XL Base and XL SFT accept `1` to `300`; Turbo and XL Turbo accept `1` to `20`. |
| `bpm` | Sent as `settings.bpm` when provided. Accepts `30` to `300`. |
| `key_scale` | Sent as `settings.keyScale` when provided. |
| `time_signature` | Sent as `settings.timeSignature`. Accepts `2`, `3`, `4`, or `6`. |
| `vocal_language` | Sent as `settings.vocalLanguage`. Must be `unknown` or a documented ISO 639-1 value in the local wrapper list. |

`negative_prompt` is rejected by presence for all Runware music models,
including `None`.

Input guards run before the generation call:

| Field | Limit |
| --- | ---: |
| `positivePrompt` | `3000` characters |
| `settings.lyrics` | `3000` characters |

Over-limit input raises `music.MusicInputLimitError` with repair prompts for
the exceeded fields.

Removed technical kwargs are rejected before provider dispatch:
`audio_settings`, `include_cost`, `number_results`, `output_format`,
`output_type`, `seed`, and `ttl`.

## Fixed Internal Payload Controls

The public API does not expose these controls.

| Internal field | Value |
| --- | --- |
| `outputType` | `URL` |
| `outputFormat` | `MP3` |
| `includeCost` | `True` |
| `numberResults` | `1` |
| `ttl` | `60` |
| `seed` | `12345` |
| `audioSettings` | `320kbps`, `48000Hz`, stereo |

Runware XL SFT also sends:

| Internal field | Value |
| --- | --- |
| `CFGScale` | `8` |
| `settings.cfgIntervalStart` | `0` |
| `settings.cfgIntervalEnd` | `1` |
| `settings.guidanceType` | `apg` |

## Normalized Result

The public result keeps only safe normalized fields:

```python
{
    "provider": "runware",
    "model": "runware:ace-step@v1.5-xl-turbo",
    "model_key": "ace_step_v1_5_xl_turbo",
    "status": "submitted",
    "request_id": "...",
    "output_path": None,
    "cost_usd": 0.0,
    "cost_currency": "USD",
    "cost_source": "unavailable",
    "cost_is_estimated": False,
    "cost_details": {},
    "metadata": {},
}
```

Cost uses numeric provider-returned `cost` when available.

If the provider response does not include a numeric cost, `cost_usd` stays
`0.0` with `cost_source="unavailable"`.

Raw provider responses, credentials, auth headers, and audio URLs are not
returned in the public dictionary.
