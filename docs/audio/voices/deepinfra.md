# audio voice helpers(api="deepinfra")

DeepInfra exposes a voice catalog for its OpenAI-compatible speech models. Use
the public helpers in `easy_ai_clients.audio` instead of importing the provider
module directly.

Credential: `DEEPINFRA_API_KEY`.

## Supported helpers

| Helper | Status | Notes |
| --- | --- | --- |
| `audio.list_voices(api="deepinfra")` | Supported | Calls the DeepInfra voice catalog endpoint. |
| `audio.get_voice("voice-id", api="deepinfra")` | Supported | Fetches/catalog-filters a single voice by `voice_id`. |
| `audio.design_voice(..., api="deepinfra")` | Unsupported | Returns a normalized `unsupported_operation` result. |
| `audio.clone_voice(..., api="deepinfra")` | Unsupported | Returns a normalized `unsupported_operation` result. |

## Example

```python
from easy_ai_clients import audio

voices = audio.list_voices(api="deepinfra")
print(voices["provider"], voices["data"])

voice = audio.get_voice("af_bella", api="deepinfra")
print(voice["voice_id"], voice["data"])
```

Voice helper responses use a lightweight dictionary contract:
`provider`, `operation`, `data`, and `raw_response`. Unsupported helpers also
include `warnings` and an `error` object with `type="unsupported_operation"`.

