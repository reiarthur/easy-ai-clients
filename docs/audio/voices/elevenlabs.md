# audio voice helpers(api="elevenlabs")

ElevenLabs supports voice catalog lookup, voice design, and voice cloning
through the public `easy_ai_clients.audio` helper functions.

Credential: `ELEVENLABS_API_KEY`.

## Supported helpers

| Helper | Status | Notes |
| --- | --- | --- |
| `audio.list_voices(api="elevenlabs")` | Supported | Lists voices available to the account. |
| `audio.get_voice("voice-id", api="elevenlabs")` | Supported | Fetches one voice by ID. |
| `audio.design_voice(prompt, api="elevenlabs")` | Supported | Sends a text description to the text-to-voice design endpoint. |
| `audio.clone_voice(audio_input=..., voice_name=..., api="elevenlabs")` | Supported | Uploads a local/bytes/audio input and creates a cloned voice. |

## Examples

```python
from easy_ai_clients import audio

voices = audio.list_voices(api="elevenlabs")
first_voice = voices["data"]["voices"][0]["voice_id"]

voice = audio.get_voice(first_voice, api="elevenlabs")
print(voice["data"])
```

```python
from easy_ai_clients import audio

designed = audio.design_voice(
    "Warm, calm product narrator with a clear studio sound.",
    api="elevenlabs",
)

cloned = audio.clone_voice(
    audio_input="speaker-sample.wav",
    voice_name="Launch Narrator",
    api="elevenlabs",
)
```

Voice helper responses use a lightweight dictionary contract:
`provider`, `operation`, `data`, and `raw_response`. The clone helper accepts
the same practical local audio forms used by transcription preprocessing.

