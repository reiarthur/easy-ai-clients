# easy-ai-clients

[![PyPI version](https://img.shields.io/pypi/v/easy-ai-clients.svg)](https://pypi.org/project/easy-ai-clients/)
[![Python versions](https://img.shields.io/pypi/pyversions/easy-ai-clients.svg)](https://pypi.org/project/easy-ai-clients/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/reiarthur/easy-ai-clients/blob/main/LICENSE)

`easy-ai-clients` is a Python library that exposes one stable interface for
text, audio, image, and video AI operations across multiple providers. Each
public operation is selected with an explicit `api=` argument, so application
code can switch providers without importing provider-specific modules.

The package is a library, not a hosted service. It makes outbound provider API
calls only when you call one of the dispatchers.

## Install

```bash
pip install easy-ai-clients
```

Requirements:

- Python `>=3.11`
- Provider credentials for only the providers you call
- `ffmpeg` support through `imageio-ffmpeg` / `pydub` for non-WAV audio inputs

Runtime dependencies are installed by `pip`: `requests`, `httpx`, `Pillow`,
`pydub`, `imageio-ffmpeg`, `python-dotenv`, and `audioop-lts` on Python
`>=3.13`.

## Quickstart

```python
import base64

from dotenv import load_dotenv
from easy_ai_clients import audio, image, text, video

load_dotenv()

text_result = text.generate(
    "Summarize Don Quixote in two sentences.",
    instruction="Use plain English.",
    api="openai",
)
print(text_result["output_text"], "USD:", text_result["cost_usd"])

speech = audio.generate(
    "Hello from easy-ai-clients.",
    voice="alloy",
    language_code="en",
    api="openai",
)
speech["audio"].export("hello.mp3", format="mp3")

transcript = audio.transcribe("hello.mp3", api="deepgram")
print(transcript["text"])

generated = image.generate("a clean product icon of a paper airplane", api="openai")
with open("paper-airplane.png", "wb") as image_file:
    image_file.write(base64.b64decode(generated["base64"]))

analysis = image.analyze(
    "Describe this image in one sentence.",
    "paper-airplane.png",
    api="openai",
)
print(analysis["output"])

clip = video.generate(
    "A smooth dolly shot through a bright paper airplane workshop.",
    api="google",
    duration_seconds=4,
)
print(clip["video_url"], "USD:", clip["cost_usd"])
```

## Public API

Import the public dispatchers from the top-level package:

```python
from easy_ai_clients import audio, image, text, video
```

or from each submodule:

```python
from easy_ai_clients.text import generate as text_generate
from easy_ai_clients.audio import generate as speech_generate
from easy_ai_clients.audio import prepare_transcription_audio
from easy_ai_clients.audio import transcribe
from easy_ai_clients.image import analyze
```

Supported operations:

| Module | Function | Purpose | Providers |
| --- | --- | --- | --- |
| `text` | `generate` | Text-in / text-out generation | `anthropic`, `cohere`, `deepinfra`, `deepseek`, `falai`, `fireworks`, `google`, `groq`, `huggingface`, `mistral`, `openai`, `openrouter`, `together`, `xai` |
| `text` | `list_models` | Provider model catalog helper where implemented | `falai`, `openai`, `openrouter` |
| `text` | `update_cost` | Post-hoc cost refresh where implemented | `openai`, `openrouter` |
| `audio` | `generate` | Text-to-speech synthesis | `deepinfra`, `elevenlabs`, `google`, `mistral`, `openai`, `together`, `xai` |
| `audio` | `prepare_transcription_audio` | Reusable speech-to-text upload preparation | common transcription preprocessing |
| `audio` | `transcribe` | Speech-to-text transcription | `deepgram`, `elevenlabs`, `falai`, `fireworks`, `speechmatics`, `together` |
| `audio` | `update_cost` | Post-hoc transcription cost refresh where implemented | `deepgram` |
| `image` | `generate` | Text-to-image generation | `bfl`, `falai`, `fireworks`, `google`, `openai`, `openrouter`, `stability`, `together`, `xai` |
| `image` | `edit` | Prompt-guided image editing | `bfl`, `falai`, `fireworks`, `google`, `openai`, `openrouter`, `stability`, `together`, `xai` |
| `image` | `remix` | Reference-image guided generation | `bfl`, `falai`, `fireworks`, `google`, `openai`, `openrouter`, `stability`, `together`, `xai` |
| `image` | `analyze` | Vision and multimodal analysis | `anthropic`, `falai`, `fireworks`, `google`, `groq`, `openai`, `openrouter`, `together`, `xai` |
| `image` | `update_cost` | Post-hoc cost refresh where implemented | `openrouter` |
| `video` | `generate` / `text_to_video` | Prompt-only video generation | `falai`, `google`, `hedra`, `runway` |
| `video` | `image_to_video` | Prompt + image video generation | `falai`, `google`, `hedra`, `runway` |
| `video` | `video_to_video` | Source-video guided generation/editing | `falai`, `google`, `hedra`, `runway` |
| `video` | `motion_control` | Character or motion-reference video generation | `falai`, `hedra`, `runway` |
| `video` | `avatar_video` | Avatar or talking-video generation from speech | `falai`, `hedra`, `runway` |
| `video` | `video_with_audio` | Generate/add audio for a source video | `hedra` |
| `video` | `create_avatar` | Create a provider avatar/persona | `runway` |
| `video` | `image_lipsync` | Image/avatar + audio lip-sync video | `falai` |
| `video` | `video_lipsync` | Source-video + audio lip-sync video | `falai` |
| `video` | `get_status`, `get_result`, `download` | Async request helpers for video operations | matching operation provider |

See the
[provider matrix](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/providers.md)
for per-provider documentation links.

## Selecting Providers

Every dispatcher requires `api=`. The value must match a supported provider
identifier for that operation.

```python
from easy_ai_clients import audio, image, text, video

print(text.available_apis())
print(audio.available_synthesize_apis())
print(audio.available_transcribe_apis())
print(image.available_generate_apis())
print(image.available_edit_apis())
print(image.available_remix_apis())
print(image.available_analyze_apis())
print(video.available_text_to_video_apis())
print(video.available_image_to_video_apis())
print(video.available_video_to_video_apis())
print(video.available_motion_control_apis())
print(video.available_avatar_video_apis())
print(video.available_video_with_audio_apis())
print(video.available_create_avatar_apis())
print(video.available_image_lipsync_apis())
print(video.available_video_lipsync_apis())
```

Provider modules under private `_apis` packages are implementation details.
Applications should call the public dispatchers shown above.

## Configuration

Credentials are read from environment variables at provider-call time. Configure
only the providers your application will call.

```bash
export OPENAI_API_KEY="sk-..."
export DEEPGRAM_API_KEY="..."
```

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:DEEPGRAM_API_KEY = "..."
```

The recommended pattern is to manage secrets in your application environment or
load a local `.env` file explicitly before calling the library:

```python
from dotenv import load_dotenv

load_dotenv()
```

Some current provider helpers also attempt to load a `.env` file from the
current working directory before resolving credentials. Do not rely on that as
your portability contract; loading environment variables explicitly keeps tests,
scripts, and deployments predictable.

Credential references:

- [`.env.example`](https://github.com/reiarthur/easy-ai-clients/blob/main/.env.example)
- [Configuration guide](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/configuration.md)

## Usage Patterns

### Text

```python
from easy_ai_clients import text

result = text.generate(
    "Write a release note headline.",
    instruction="Return one short sentence.",
    model="gpt-5-nano",
    api="openai",
    max_output_tokens=80,
)

print(result["output_text"])
```

`stream=True` is supported by text providers that expose streaming. The stream
is consumed internally and the dispatcher still returns the same normalized
dictionary.

### Audio

```python
from easy_ai_clients import audio

speech = audio.generate(
    "This is a short narration.",
    model="tts-1",
    voice="alloy",
    api="openai",
)
speech["audio"].export("narration.mp3", format="mp3")

bundle = audio.transcribe("narration.mp3", api="deepgram")
print(bundle["text"])

bundle = audio.update_cost("transcribe", bundle, api="deepgram")
```

Transcription inputs may be local paths, supported URLs, bytes, base64 strings,
data URLs, or `pydub.AudioSegment` objects when the selected provider adapter
supports that input form.

Transcription prepares normalized WAV by default for safety and backwards
compatibility. To avoid repeated local decode/export while trying multiple
providers or models, prepare once:

```python
from easy_ai_clients.audio import prepare_transcription_audio, transcribe

prepared = prepare_transcription_audio("audio.mp3")

fireworks = transcribe(prepared, api="fireworks", model="whisper-v3-turbo", preprocessing="none")
deepgram = transcribe(prepared, api="deepgram", model="nova-3")
elevenlabs = transcribe(prepared, api="elevenlabs", model="scribe_v2", tag_audio_events=False)
```

Compressed upload formats are opt-in:

```python
prepared = prepare_transcription_audio(
    "audio.mp3",
    upload_format="ogg",
    codec="libopus",
    bitrate="24k",
)
result = transcribe(prepared, api="deepgram", model="nova-3")
```

Compressed uploads can reduce payload size, but provider decoding and runtime
can differ. Validate the format for the selected provider/model. Automatic
language defaults remain unchanged.

### Images

```python
from easy_ai_clients import image

generated = image.generate(
    "a minimal app icon with a blue compass",
    api="openai",
    size="1024x1024",
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

description = image.analyze(
    "List the visible objects.",
    "input.png",
    api="openai",
)
```

Image inputs can be local file paths, public `http` / `https` URLs, raw base64
image strings, or base64 data URLs. For `image.edit`, the public mask convention
is black = editable and white = preserve.

### Video

```python
from easy_ai_clients import video

generated = video.generate(
    "A clean product video of a blue compass app icon rotating on glass.",
    api="google",
    duration_seconds=4,
    resolution="720p",
)

from_image = video.image_to_video(
    "Subtle camera push-in with soft daylight.",
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

submitted = video.motion_control(
    image="character.png",
    video="motion-reference.mp4",
    api="falai",
    character_orientation="image",
    duration_seconds=5,
    sync=False,
)
status = video.get_status("motion_control", submitted["request_id"], api="falai")
```

Video media inputs accept local file paths, public `http` / `https` URLs, or
data URLs. `sync=False` returns provider request IDs and queue/task metadata;
use `video.get_status`, `video.get_result`, or `video.download` with the same
operation and provider.

## Return Contracts

| Operation | Normalized result |
| --- | --- |
| `text.generate(...)` | `request_id`, `cost_source`, `cost_usd`, `input_text`, optional `instruction`, `output_text`; failures add `error` and usually `warnings` |
| `audio.generate(...)` | `cost_usd`, `audio` as `pydub.AudioSegment`, `words`; failures use `audio=None`, `words={}`, and add `error` |
| `audio.transcribe(...)` | `text`, optional `words` / `segments` / `silences`, speaker metadata, `provider_metadata`, `request_id`, `cost_usd`, `cost_source`, `cost_is_estimated`, `cost_lookup_error`, optional `mkd`; failures add `error` |
| `image.generate(...)`, `image.edit(...)`, `image.remix(...)` | `cust_usd`, `base64`, `warnings`, `request_id`; failures use `base64=""` and add `error` |
| `image.analyze(...)` | `request_id`, `cost_usd`, `input_text`, `output`; failures add `error` |
| `video.generate(...)`, `video.text_to_video(...)`, `video.image_to_video(...)`, `video.video_to_video(...)`, `video.motion_control(...)`, `video.avatar_video(...)`, `video.video_with_audio(...)`, `video.create_avatar(...)`, `video.image_lipsync(...)`, `video.video_lipsync(...)` | `provider`, `model`, `status`, `request_id`, `video_url`, `output_path`, `cost_usd`, `cost_is_estimated`, `cost_source`, `raw_response`; failures use `status="failed"` and add `error` |

The image generation/edit/remix cost key is intentionally `cust_usd` for the
current public contract.

## Provider Parameters

Extra keyword arguments are provider-native and are forwarded by the selected
adapter whenever the wrapper can still assemble a request. Model names in the
docs are documented models used for defaults, pricing, and examples; they are
not a local acceptance list. If the provider accepts a newer model or kwarg, the
call can succeed before this library documents it.

```python
from easy_ai_clients import image, text

text.generate(
    "Return JSON with one key named status.",
    api="openai",
    model="gpt-5-nano",
    max_output_tokens=80,
    text={"format": {"type": "json_object"}},
)

image.generate(
    "a serene lake at dawn",
    api="stability",
    model="stable-image-ultra",
    aspect_ratio="16:9",
    output_format="png",
)
```

If a model or kwarg is wrong, the provider response is normalized into the
operation's public result shape with an `error` object where possible.

## Costs

Cost values are best-effort normalized USD values:

- Some providers return exact usage or request cost.
- Some adapters compute cost from usage fields and local pricing tables.
- Some router/provider costs can be refined after the call.
- Video adapters currently report estimated cost from documented provider
  pricing tables when metadata exists.
- fal.ai video adapters can use the official pricing estimate API when callers
  pass `billing_unit_quantity` or `unit_quantity` explicitly.
- Unknown cost is `0.0` with `cost_source="unavailable"` and a warning or
  `cost_lookup_error` explaining that pricing metadata is not documented.

```python
from easy_ai_clients import audio, image, text, video

text_result = text.generate("ping", api="openrouter")
text_result = text.update_cost(text_result, api="openrouter")

image_result = image.generate("a tiny robot", api="openrouter")
image_result = image.update_cost("generate", image_result, api="openrouter")

transcript = audio.transcribe("meeting.mp3", api="deepgram")
transcript = audio.update_cost("transcribe", transcript, api="deepgram")

video_result = video.generate("a four-second product shot", api="google")
print(video_result["cost_is_estimated"])
```

## Errors

Public operations return normalized failure dictionaries when they can preserve
the operation shape. The added `error` object contains `type`, `message`,
`provider`, `operation`, and `model`; messages are redacted to avoid leaking API
keys or authorization headers. Helper functions such as `list_models`,
`update_cost`, and some direct private adapter calls can still raise standard
Python exceptions.

Common helper/private-adapter exceptions:

- `ValueError`: missing required local media, incompatible local wrapper input,
  or unsupported helper operation.
- `RuntimeError` / `OSError`: missing credentials or provider failures that are
  not called through a public dispatcher.
- `requests` / `httpx` exceptions: transport or HTTP status failures in helper
  paths.
- `NotImplementedError`: helper methods such as cost updates are called for a
  provider that does not implement them.

See the
[error handling guide](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/errors.md)
for more detail.

## More Documentation

- [Configuration](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/configuration.md)
- [Usage patterns](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/usage.md)
- [Provider matrix](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/providers.md)
- [Error handling](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/errors.md)
- [Full docs directory](https://github.com/reiarthur/easy-ai-clients/tree/main/docs)
- [Changelog](https://github.com/reiarthur/easy-ai-clients/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/reiarthur/easy-ai-clients/blob/main/CONTRIBUTING.md)

## License

MIT. See
[LICENSE](https://github.com/reiarthur/easy-ai-clients/blob/main/LICENSE).
