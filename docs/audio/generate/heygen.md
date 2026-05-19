# HeyGen audio.generate

Use HeyGen v3 Starfish speech through `easy_ai_clients.audio.generate(..., api="heygen")`.

Credential: `HEYGEN_KEY`.

```python
from easy_ai_clients import audio

speech = audio.generate(
    "Hello from HeyGen.",
    api="heygen",
    voice="your-starfish-voice-id",
)
```

The adapter calls `POST /v3/voices/speech`, downloads the returned `audio_url`,
and returns the package synthesis contract: `cost_usd`, `audio`, `words`,
`request_id`, `provider_metadata`, and `raw_response`.

Voice helpers are exposed on `easy_ai_clients.audio`: `list_voices`,
`get_voice`, `design_voice`, and `clone_voice`.

