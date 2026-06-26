# deAPI Music Provider

Public dispatcher: `music.generate(..., api="deapi")`.

## Public Models

| Native model ID | Standard model key | Default |
| --- | --- | ---: |
| `AceStep_1_5_Turbo` | `ace_step_v1_5_turbo` | Yes |
| `AceStep_1_5_XL_Turbo_INT8` | `ace_step_1_5_xl_turbo_int8` | No |

`model` may be either the native model ID or the standard model key.

When `model` is omitted, `music.generate(..., api="deapi")` uses
`AceStep_1_5_Turbo`.

## Endpoints

| Purpose | Endpoint |
| --- | --- |
| Submit generation | `https://api.deapi.ai/api/v1/client/txt2music` |
| Status and result URL | `https://api.deapi.ai/api/v1/client/request-status/{request_id}` |
| Price lookup | `https://api.deapi.ai/api/v2/audio/music/price` |

Credential variable: `DEAPI_API_KEY`.

## Public Call

```python
from easy_ai_clients import music

generation = music.generate(
    lyrics="...",
    api="deapi",
    model="ace_step_v1_5_turbo",
    style="sertanejo",
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
male/female maps. The deAPI ACE-Step path renders a compact prompt target
before the `caption` payload. If provider input limits are exceeded, the router
tries smaller preset prompt variants before raising `MusicInputLimitError`.

Local prompt controls:

| Parameter | Behavior |
| --- | --- |
| `language` | Overrides preset language and maps to ACE-Step `vocal_language`. |
| `gender` | Selects `male`, `female`, or `both` voice guidance from `voice_presets`. |
| `voice_description` | Replaces preset voice guidance with caller-provided voice text. |

Duration behavior:

| Standard model key | Native model ID | Min | Max | Missing or invalid `duration` | Provider application |
| --- | --- | ---: | ---: | --- | --- |
| `ace_step_v1_5_turbo` | `AceStep_1_5_Turbo` | `10s` | `300s` | Uses `60s` | Sent as `duration` |
| `ace_step_1_5_xl_turbo_int8` | `AceStep_1_5_XL_Turbo_INT8` | `10s` | `300s` | Uses `60s` | Sent as `duration` |

| Parameter | Behavior |
| --- | --- |
| `duration` | Sent as `duration`. Numeric values are clamped to `10` to `300`. Missing or invalid values use `60`. |
| `steps` | Sent as `inference_steps`. Accepts `1` to `8`. Default: `8`. |
| `bpm` | Sent as `bpm`. Accepts `30` to `300` when not `None`. Default: `116`. |
| `key_scale` | Sent as `keyscale`. Default: `"A minor"`. |
| `time_signature` | Sent as `timesignature`. Accepts `2`, `3`, `4`, or `6`. Default: `4`. |
| `vocal_language` | Sent as `vocal_language`. Default: `"pt"`. |
| `reference_audio` | Local audio file path sent as multipart. |
| `webhook_url` | Passed through to the provider payload. |

`negative_prompt` is rejected by presence, including `None`.

The local `300` second maximum comes from paid validation of both implemented
deAPI models. The public deAPI docs can still mention a higher value, but the
live endpoint rejected `600`.

Input guards run before the generation call:

| Field | Limit |
| --- | ---: |
| `caption` / prompt | `3000` characters |
| `lyrics` | `3000` characters |

Over-limit input raises `music.MusicInputLimitError` with repair prompts for
the exceeded fields.

Removed technical kwargs are rejected before provider dispatch:
`audio_settings`, `include_cost`, `number_results`, `output_format`,
`output_type`, `seed`, and `ttl`.

## Normalized Result

The public result keeps only safe normalized fields:

```python
{
    "provider": "deapi",
    "model": "AceStep_1_5_Turbo",
    "model_key": "ace_step_v1_5_turbo",
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

Cost source policy:

| Source | Meaning |
| --- | --- |
| `deapi_price_endpoint` | Cost came from the deAPI price endpoint. |
| `provider_response` | Cost came from a later status response. |
| `unavailable` | No usable cost was returned. `cost_usd` is `0.0`. |

Raw provider responses, credentials, auth headers, and result URLs are not
returned in the public dictionary.
