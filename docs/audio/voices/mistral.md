# audio voice helpers(api="mistral")

Mistral exposes a voice catalog for its speech models. The library wraps the
catalog through `audio.list_voices` and `audio.get_voice`.

Credential: `MISTRAL_API_KEY`.

## Supported helpers

| Helper | Status | Notes |
| --- | --- | --- |
| `audio.list_voices(api="mistral")` | Supported | Calls `GET /v1/audio/voices`. |
| `audio.get_voice("voice-id", api="mistral")` | Supported | Calls `GET /v1/audio/voices/{voice_id}`. |
| `audio.design_voice(..., api="mistral")` | Unsupported | Returns a normalized `unsupported_operation` result. |
| `audio.clone_voice(..., api="mistral")` | Unsupported | Returns a normalized `unsupported_operation` result. |

## Example

```python
from easy_ai_clients import audio

voices = audio.list_voices(api="mistral")
print(voices["data"])

voice = audio.get_voice("alloy", api="mistral")
print(voice["data"])
```

Voice helper responses use `provider`, `operation`, `data`, and `raw_response`.
Unsupported helpers return the same shape plus `warnings` and an `error`
object.

