# audio voice helpers(api="heygen")

HeyGen v3 voice helpers expose public/custom voices for speech and talking
video workflows. They are useful before calling `audio.generate(api="heygen")`
or HeyGen video/avatar operations.

Credential: `HEYGEN_KEY`.

## Supported helpers

| Helper | Status | Notes |
| --- | --- | --- |
| `audio.list_voices(api="heygen")` | Supported | Calls `GET /v3/voices`; accepts filters such as `type`, `engine`, `language`, `gender`, `limit`, and `token`. |
| `audio.get_voice("voice-id", api="heygen")` | Supported | Calls `GET /v3/voices/{voice_id}`. |
| `audio.design_voice(prompt, api="heygen")` | Supported | Calls `POST /v3/voices` with the prompt plus provider-native kwargs. |
| `audio.clone_voice(audio_input=..., voice_name=..., api="heygen")` | Supported | Calls `POST /v3/voices/clone`; local media is normalized into a HeyGen asset input. |

## Examples

```python
from easy_ai_clients import audio

voices = audio.list_voices(
    api="heygen",
    type="public",
    engine="starfish",
    limit=5,
)
voice_id = voices["data"]["voices"][0]["voice_id"]

speech = audio.generate(
    "Welcome to the demo.",
    api="heygen",
    voice=voice_id,
)
```

```python
from easy_ai_clients import audio

clone = audio.clone_voice(
    audio_input="speaker.wav",
    voice_name="Demo Host",
    api="heygen",
)
print(clone["data"])
```

Responses include `provider`, `data`, and `raw_response`. Descriptive provider
fields are preserved in `data` instead of being flattened so callers can keep
access to the full HeyGen v3 payload.

