# audio voice helpers(api="together")

Together AI exposes a voice catalog for text-to-speech workflows. The library
wraps the catalog through `audio.list_voices` and `audio.get_voice`.

Credential: `TOGETHER_API_KEY`.

## Supported helpers

| Helper | Status | Notes |
| --- | --- | --- |
| `audio.list_voices(api="together")` | Supported | Calls `GET /v1/voices`. |
| `audio.get_voice("voice-id", api="together")` | Supported | Calls `GET /v1/voices/{voice_id}`. |
| `audio.design_voice(..., api="together")` | Unsupported | Returns a normalized `unsupported_operation` result. |
| `audio.clone_voice(..., api="together")` | Unsupported | Returns a normalized `unsupported_operation` result. |

## Example

```python
from easy_ai_clients import audio

voices = audio.list_voices(api="together")
print(voices["data"])

voice = audio.get_voice("helpful-woman", api="together")
print(voice["data"])
```

Voice helper responses use `provider`, `operation`, `data`, and `raw_response`.
Unsupported helpers return the same shape plus `warnings` and an `error`
object.

