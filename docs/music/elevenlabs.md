# ElevenLabs Music Provider

Public dispatcher: `music.generate(..., api="elevenlabs")`.

## Public Models

| Public model key | Native model ID | Default |
| --- | --- | ---: |
| `eleven_music` | `music_v2` | Yes |
| `eleven_music_v2` | `music_v2` | No |
| `music_v2` | `music_v2` | No |

When `model` is omitted, `music.generate(..., api="elevenlabs")` uses the
public default key `eleven_music`, which resolves to native `music_v2`.

Explicit `music_v1` is not supported by this wrapper.

## Endpoint

| Purpose | Endpoint |
| --- | --- |
| Compose music | `https://api.elevenlabs.io/v1/music` |

Credential variable: `ELEVENLABS_API_KEY`.

The provider returns binary audio synchronously. The wrapper starts that request
in a local background thread and returns a normalized submitted generation
immediately.

The wrapper uses prompt mode only:

- Sends `model_id="music_v2"`.
- Sends the final prompt in `prompt`.
- Sends valid duration as `music_length_ms`.
- Sends internal query parameter `output_format=auto`.
- Does not send `composition_plan`, `seed`, or `force_instrumental`.

`output_format` is an internal provider detail and is not a public music kwarg.
Downloaded files keep the local `.mp3` extension.

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

When `style` is used, the local preset provides `style_prompts` and
`voice_presets`. ElevenLabs uses `style_prompts.large` with
`voice_presets.small` by default. Other providers start with `large` style and
`large` voice prompts.

Local prompt controls:

| Parameter | Behavior |
| --- | --- |
| `language` | Overrides preset language in generated prompt text. |
| `gender` | Selects `male`, `female`, or `both` voice guidance from `voice_presets`. |
| `voice_description` | Replaces preset voice guidance with caller-provided voice text. |

Duration behavior:

| Public model key | Native model ID | Min | Max | Missing or invalid `duration` | Provider application |
| --- | --- | ---: | ---: | --- | --- |
| `eleven_music` | `music_v2` | `3s` | `600s` | Omits duration | Sent as `music_length_ms = duration * 1000` |
| `eleven_music_v2` | `music_v2` | `3s` | `600s` | Omits duration | Sent as `music_length_ms = duration * 1000` |
| `music_v2` | `music_v2` | `3s` | `600s` | Omits duration | Sent as `music_length_ms = duration * 1000` |

| Parameter | Behavior |
| --- | --- |
| `duration` | Valid numeric values are clamped to `3` to `600` and converted to `music_length_ms = duration * 1000`. Missing or invalid values omit `music_length_ms`. |

The final ElevenLabs prompt combines the music prompt, lyric text, and
language-neutral delivery rules. The prompt asks for native diction, complete
word endings, preserved accents and diacritics, section tags used only as
structure, and natural pacing between sections. If the resolved language is
Brazilian Portuguese, an extra cedilla and nasal-vowel pronunciation rule is
added.

`negative_prompt` is rejected by presence, including `None`.

`_force_instrumental` is not supported by the public music dispatcher.

The final ElevenLabs prompt must be `4100` characters or shorter. Over-limit
input raises `music.MusicInputLimitError` with a repair prompt for `prompt`.

Removed technical kwargs are rejected before provider dispatch:
`audio_settings`, `include_cost`, `number_results`, `output_format`,
`output_type`, `seed`, and `ttl`.

## Lyrics Prompt Helper

`music.build_lyrics_prompt(..., api="elevenlabs")` keeps the same return shape
as the default helper and does not call provider APIs. It adds lyric-format
guidance suited for direct music generation:

- Uses `style_prompts.large` for valid style presets.
- Uses `voice_presets.small` for valid style voices.
- Asks for short, naturally singable lines.
- Avoids vocal-role tags such as `[Male Lead]`, `[Female Lead]`, and `[Duet]`.
- For `gender="both"`, asks for natural sharing between two voices without
  labeling individual lines by singer gender.

Other `api` values keep the default prompt-builder behavior.

## Normalized Result

The public result keeps only safe normalized fields:

```python
{
    "provider": "elevenlabs",
    "model": "music_v2",
    "model_key": "eleven_music",
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

When a valid duration is supplied, cost is estimated locally as:

```text
(duration / 60) * 0.150
```

Raw binary audio, credentials, auth headers, and raw provider responses are not
returned in the public dictionary.
