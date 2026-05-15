# Usage Patterns

This guide documents the public dispatcher layer. Provider modules under
private `_apis` packages are implementation details and should not be imported
by applications.

## Imports

```python
from easy_ai_clients import audio, image, text, video
```

Direct submodule imports are also supported:

```python
from easy_ai_clients.text import generate as text_generate
from easy_ai_clients.audio import generate as speech_generate
from easy_ai_clients.audio import prepare_transcription_audio
from easy_ai_clients.audio import transcribe
from easy_ai_clients.image import analyze
from easy_ai_clients.video import text_to_video
```

## Provider Selection

Every operation requires `api=`. Use the discovery helpers to inspect supported
provider identifiers:

```python
from easy_ai_clients import audio, image, text, video

text.available_apis()
audio.available_synthesize_apis()
audio.available_transcribe_apis()
image.available_generate_apis()
image.available_edit_apis()
image.available_remix_apis()
image.available_analyze_apis()
video.available_text_to_video_apis()
video.available_image_to_video_apis()
video.available_video_to_video_apis()
video.available_motion_control_apis()
video.available_avatar_video_apis()
video.available_video_with_audio_apis()
video.available_create_avatar_apis()
video.available_image_lipsync_apis()
video.available_video_lipsync_apis()
```

## Text Generation

```python
from easy_ai_clients import text

result = text.generate(
    "Write a concise status update.",
    instruction="Use plain English.",
    api="openai",
    model="gpt-5-nano",
    max_output_tokens=80,
)

print(result["output_text"])
```

Return keys:

- `request_id`
- `cost_source`
- `cost_usd`
- `input_text`
- optional `instruction`
- `output_text`

`text.list_models(api=...)` and `text.update_cost(result, api=...)` are
available only for providers that implement those helper functions.

## Text Streaming

For providers that support streaming, pass `stream=True` as a provider-native
kwarg. The adapter consumes the stream internally and returns the same final
dictionary contract as a non-streaming call.

```python
from easy_ai_clients import text

result = text.generate("Reply with OK.", api="openai", stream=True)
print(result["output_text"])
```

## Speech Synthesis

```python
from easy_ai_clients import audio

result = audio.generate(
    "Hello from easy-ai-clients.",
    api="openai",
    model="tts-1",
    voice="alloy",
    language_code="en",
)

result["audio"].export("speech.mp3", format="mp3")
```

Return keys:

- `cost_usd`
- `audio`, a `pydub.AudioSegment`
- `words`, a list of timing records when available

Some synthesis providers use alignment calls to recover word timings. Configure
the credentials documented for the selected provider path.

## Speech Transcription

```python
from easy_ai_clients import audio

bundle = audio.transcribe(
    "speech.mp3",
    api="deepgram",
)

print(bundle["text"])
```

The backwards-compatible dispatcher form remains:

```python
from easy_ai_clients.audio import transcribe

result = transcribe("audio.mp3", api="deepgram")
```

Supported input forms depend on the selected adapter, but public preprocessing
supports local paths, supported URLs, bytes, base64 strings, data URLs, and
`pydub.AudioSegment` objects.

By default, transcription prepares a normalized WAV payload: 16 kHz, mono,
PCM16. This is the safest cross-provider behavior and preserves older calls.
When comparing providers or models, prepare the audio once and reuse it:

```python
from easy_ai_clients.audio import prepare_transcription_audio, transcribe

prepared = prepare_transcription_audio("audio.mp3")

fireworks = transcribe(
    prepared,
    api="fireworks",
    model="whisper-v3-turbo",
    preprocessing="none",
)
deepgram = transcribe(prepared, api="deepgram", model="nova-3")
elevenlabs = transcribe(
    prepared,
    api="elevenlabs",
    model="scribe_v2",
    tag_audio_events=False,
)
```

You can opt into compressed uploads when a provider supports the format:

```python
from easy_ai_clients.audio import prepare_transcription_audio, transcribe

prepared = prepare_transcription_audio(
    "audio.mp3",
    upload_format="ogg",
    codec="libopus",
    bitrate="24k",
)
result = transcribe(prepared, api="deepgram", model="nova-3")
```

Compressed formats can reduce upload size, but they may change provider-side
decoding/runtime and should be validated for the selected provider/model.
Prepared audio avoids repeated local decode/export; automatic language defaults
are unchanged. Provider-native kwargs such as Fireworks `preprocessing="none"`
remain separate from library audio preparation options such as
`audio_upload_format=`.

Common return keys include:

- `text`
- `words`
- `segments`
- `silences`
- `speaker_count`
- `speaker_details`
- `provider_metadata`
- `request_id`
- `cost_usd`
- `cost_source`
- `cost_is_estimated`
- `cost_lookup_error`
- optional `mkd`

Empty optional lists and dictionaries may be omitted from the returned bundle.
Provider defaults avoid concrete language codes where possible. Deepgram sends
`detect_language=true`, Speechmatics and Together send `language="auto"`, and
ElevenLabs, Fal.ai, and Fireworks omit their language field by default.

## Image Generation, Editing, and Remixing

```python
from easy_ai_clients import image

generated = image.generate(
    "a minimal app icon with a blue compass",
    api="openai",
)

edited = image.edit(
    "replace the background with a white studio backdrop",
    "input.png",
    api="openai",
)

remixed = image.remix(
    "keep the subject but use watercolor style",
    ["input.png"],
    api="openai",
)
```

Return keys for these operations:

- `cust_usd`
- `base64`
- `warnings`
- `request_id`

The cost key is currently spelled `cust_usd` for this public contract.

Image inputs can be local paths, public `http` / `https` URLs, raw base64 image
strings, or base64 data URLs. For `image.edit`, the public mask convention is
black = editable and white = preserve.

## Image Analysis

```python
from easy_ai_clients import image

result = image.analyze(
    "Describe the visible objects.",
    "input.png",
    api="openai",
)

print(result["output"])
```

Return keys:

- `request_id`
- `cost_usd`
- `input_text`
- `output`

## Video Generation

```python
from easy_ai_clients import video

generated = video.generate(
    "A four-second cinematic shot of a paper airplane crossing a studio desk.",
    api="google",
    duration_seconds=4,
    resolution="720p",
)

from_image = video.image_to_video(
    "Slow push-in with natural motion.",
    "input.png",
    api="runway",
    duration=5,
)

edited = video.video_to_video(
    "Keep the framing but make the lighting warmer.",
    video="source.mp4",
    api="runway",
    duration=5,
)

custom_avatar = video.create_avatar(
    image="avatar.png",
    name="Launch Host",
    voice="clara",
    api="runway",
)

avatar = video.avatar_video(
    avatar_id=custom_avatar["avatar_id"],
    text="Welcome to the launch.",
    api="runway",
    duration_seconds=6,
)

with_audio = video.video_with_audio(
    video="source.mp4",
    prompt="Add natural room tone.",
    model="hedra-video-generation-model-id",
    api="hedra",
    sync=False,
)

talking_avatar = video.image_lipsync(
    image="avatar.png",
    audio="voice.wav",
    api="falai",
)
```

Common return keys include:

- `provider`
- `model`
- `status`
- `request_id`
- `video_url`
- `output_path`
- `cost_usd`
- `cost_is_estimated`
- `cost_source`
- `raw_response`

Supported video media inputs are local paths, public `http` / `https` URLs, and
data URLs. When `sync=False`, the dispatcher returns submitted queue/task
metadata; pass the same operation name to `video.get_status`,
`video.get_result`, or `video.download`.

## Provider-Native Kwargs

Extra keyword arguments are provider-native. The provider docs list models and
parameters that have been analyzed, but that metadata is documentation and
pricing/default reference, not a local acceptance list. New provider models or
parameters can be passed before this library documents them.

```python
from easy_ai_clients import image, text

text.generate(
    "Return a compact JSON object.",
    api="openai",
    text={"format": {"type": "json_object"}},
    max_output_tokens=80,
)

image.generate(
    "a serene lake at dawn",
    api="stability",
    aspect_ratio="16:9",
    output_format="png",
)
```

When a provider rejects a model or parameter, public operations return the
normal result shape with safe empty output plus an `error` object where possible.
Messages are sanitized before being exposed.

## Cost Updates

```python
from easy_ai_clients import audio, image, text, video

text_result = text.generate("ping", api="openrouter")
text_result = text.update_cost(text_result, api="openrouter")

image_result = image.generate("a small robot", api="openrouter")
image_result = image.update_cost("generate", image_result, api="openrouter")

transcript = audio.transcribe("speech.mp3", api="deepgram")
transcript = audio.update_cost("transcribe", transcript, api="deepgram")

video_result = video.generate("a short product clip", api="google")
print(video_result["cost_is_estimated"])
```

Cost helpers raise `NotImplementedError` when the selected provider does not
support post-hoc cost lookup. Documented pricing metadata is used when known;
unknown model or request costs are reported as `0.0` with
`cost_source="unavailable"` and a warning or lookup-error reason.
