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

| Parameter | Behavior |
| --- | --- |
| `duration` | Accepted for standardized API shape, but ignored in the provider payload. |

`negative_prompt` is rejected by presence, including `None`.

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

