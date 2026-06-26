# Google Lyria Provider

Public dispatcher: `music.generate(..., api="google")`.

## Public Models

| Native model ID | Standard model key | Default |
| --- | --- | ---: |
| `lyria-3-clip-preview` | `lyria_3_clip_preview` | Yes |
| `lyria-3-pro-preview` | `lyria_3_pro_preview` | No |

`model` may be either the native model ID or the standard model key.

When `model` is omitted, `music.generate(..., api="google")` uses
`lyria-3-clip-preview`.

## Endpoints

| Model | Endpoint |
| --- | --- |
| `lyria-3-clip-preview` | `https://generativelanguage.googleapis.com/v1beta/models/lyria-3-clip-preview:generateContent` |
| `lyria-3-pro-preview` | `https://generativelanguage.googleapis.com/v1beta/models/lyria-3-pro-preview:generateContent` |

The wrapper also calls the matching `:countTokens` endpoint on the final
`contents` payload before `:generateContent`.

Credential variable: `GOOGLE_API_KEY`.

Google Lyria returns inline audio synchronously.

The wrapper starts that request in a local background thread and returns a
normalized submitted generation immediately.

## Public Call

```python
from easy_ai_clients import music

generation = music.generate(
    lyrics="...",
    api="google",
    model="lyria_3_clip_preview",
    style="gospel_br",
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
| `language` | Overrides preset language in generated prompt text. |
| `gender` | Selects `male`, `female`, or `both` voice guidance from `voice_presets`. |
| `voice_description` | Replaces preset voice guidance with caller-provided voice text. |

Duration behavior:

| Standard model key | Native model ID | Min | Max | Missing or invalid `duration` | Provider application |
| --- | --- | ---: | ---: | --- | --- |
| `lyria_3_clip_preview` | `lyria-3-clip-preview` | `30s` | `30s` | Ignores duration | Not sent |
| `lyria_3_pro_preview` | `lyria-3-pro-preview` | `15s` | `180s` | Omits duration | Added as natural English prompt text |

| Parameter | Behavior |
| --- | --- |
| `duration` for `lyria-3-clip-preview` | Ignored. Clip output remains fixed at about `30` seconds. |
| `duration` for `lyria-3-pro-preview` | Valid numeric values are clamped to `15` to `180` and appended to the prompt as natural English target duration text. Missing or invalid values are omitted. |

`negative_prompt` is rejected by presence, including `None`.

Google input is limited to `131072` tokens across the final `contents` payload.
If `countTokens` reports an over-limit payload,
`music.MusicInputLimitError` is raised before generation.

Removed technical kwargs are rejected before provider dispatch:
`audio_settings`, `include_cost`, `number_results`, `output_format`,
`output_type`, `seed`, and `ttl`.

## Normalized Result

The public result keeps only safe normalized fields:

```python
{
    "provider": "google",
    "model": "lyria-3-clip-preview",
    "model_key": "lyria_3_clip_preview",
    "status": "submitted",
    "request_id": "...",
    "output_path": None,
    "cost_usd": 0.04,
    "cost_currency": "USD",
    "cost_source": "official_pricing_table",
    "cost_is_estimated": True,
    "cost_details": {"pricing_unit": "request"},
    "metadata": {},
}
```

Cost uses the local validated table:

| Model | `cost_usd` |
| --- | ---: |
| `lyria-3-clip-preview` | `0.04` |
| `lyria-3-pro-preview` | `0.08` |

Inline audio payloads, credentials, auth headers, and raw provider responses are
not returned in the public dictionary.
