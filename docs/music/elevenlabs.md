# ElevenLabs Music Provider

Public dispatcher: `music.generate(..., api="elevenlabs")`.

## Public Models

| Native model ID | Standard model key | Default |
| --- | --- | ---: |
| `music_v1` | `eleven_music` | Yes |

`model` may be either `music_v1` or `eleven_music`.

When `model` is omitted, `music.generate(..., api="elevenlabs")` uses
`music_v1`.

## Endpoint

| Purpose | Endpoint |
| --- | --- |
| Compose music | `https://api.elevenlabs.io/v1/music` |

Credential variable: `ELEVENLABS_API_KEY`.

The provider returns binary audio synchronously.

The wrapper starts that request in a local background thread and returns a
normalized submitted generation immediately.

## Public Call

```python
from easy_ai_clients import music

generation = music.generate(
    lyrics="...",
    api="elevenlabs",
    model="eleven_music",
    style="rock",
)

generation = music.get_status(generation)
generation = music.download_result(generation)
```

## Accepted Parameters

`style` or `prompt` is required.

If both are passed, `prompt` wins.

| Parameter | Behavior |
| --- | --- |
| `duration` | Converted to `music_length_ms = duration * 1000`. Accepts `3` to `600`. Default: `60`. |

`negative_prompt` is rejected by presence, including `None`.

`_force_instrumental` is an internal style-adapter control. It is not a public
documented parameter.

Removed technical kwargs are rejected before provider dispatch:
`audio_settings`, `include_cost`, `number_results`, `output_format`,
`output_type`, `seed`, and `ttl`.

## Normalized Result

The public result keeps only safe normalized fields:

```python
{
    "provider": "elevenlabs",
    "model": "music_v1",
    "model_key": "eleven_music",
    "status": "submitted",
    "request_id": "...",
    "output_path": None,
    "cost_usd": 0.15,
    "cost_currency": "USD",
    "cost_source": "official_pricing_table",
    "cost_is_estimated": True,
    "cost_details": {
        "duration_seconds": 60,
        "usd_per_minute": 0.15,
    },
    "metadata": {},
}
```

Cost is calculated locally as:

```text
(duration / 60) * 0.150
```

Raw binary audio, credentials, auth headers, and raw provider responses are not
returned in the public dictionary.

