# easy-ai-clients

[![PyPI version](https://img.shields.io/pypi/v/easy-ai-clients.svg)](https://pypi.org/project/easy-ai-clients/)
[![Python versions](https://img.shields.io/pypi/pyversions/easy-ai-clients.svg)](https://pypi.org/project/easy-ai-clients/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/reiarthur/easy-ai-clients/blob/main/LICENSE)

`easy-ai-clients` is a Python library that exposes one stable interface for
text, audio, music, image, and video AI operations across multiple providers.
Each public operation is selected with an explicit `api=` argument, so
application code can switch providers without importing provider-specific
modules.

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
from easy_ai_clients import account, audio, image, media, music, text, video, webhooks

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

track = music.text_to_music(
    "Warm lo-fi product intro with soft drums.",
    api="stability",
    duration_seconds=30,
)
print(track["audio_url"], "USD:", track["cost_usd"])

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
from easy_ai_clients import account, audio, image, media, music, text, video, webhooks
```

or from each submodule:

```python
from easy_ai_clients.text import generate as text_generate
from easy_ai_clients.audio import generate as speech_generate
from easy_ai_clients.audio import prepare_transcription_audio
from easy_ai_clients.audio import transcribe
from easy_ai_clients.image import analyze
from easy_ai_clients.music import text_to_music
```

Supported operations:

| Module | Function | Purpose | Providers |
| --- | --- | --- | --- |
| `text` | `generate` | Text-in / text-out generation | `anthropic`, `cohere`, `deepinfra`, `deepseek`, `falai`, `fireworks`, `google`, `groq`, `huggingface`, `mistral`, `openai`, `openrouter`, `together`, `xai` |
| `text` | `list_models` | Provider model catalog helper where implemented | current text providers with catalog support |
| `text` | `update_cost` | Post-hoc cost refresh where implemented | `openai`, `openrouter` |
| `audio` | `generate` | Speech, music, and sound synthesis | `deepgram`, `deepinfra`, `elevenlabs`, `google`, `groq`, `heygen`, `mistral`, `openai`, `openrouter`, `runway`, `stability`, `together`, `xai` |
| `audio` | `list_voices`, `get_voice`, `design_voice`, `clone_voice` | Voice catalog, design, and cloning helpers | `deepinfra`, `elevenlabs`, `heygen`, `mistral`, `together` |
| `audio` | `prepare_transcription_audio` | Reusable speech-to-text upload preparation | common transcription preprocessing |
| `audio` | `transcribe` | Speech-to-text transcription | `deepinfra`, `deepgram`, `elevenlabs`, `falai`, `fireworks`, `google`, `groq`, `huggingface`, `mistral`, `openai`, `openrouter`, `speechmatics`, `together`, `xai` |
| `audio` | `update_cost` | Post-hoc transcription cost refresh where implemented | `deepgram` |
| `music` | `generate` / `text_to_music` | Generate music from a prompt, tags, loop request, soundtrack request, or auto-lyrics request | `beatoven`, `cloudflare`, `deapi`, `elevenlabs`, `falai`, `generatesongs`, `google`, `jen`, `minimax`, `modelslab`, `musicful`, `musicfy`, `musicgpt`, `novita`, `replicate`, `runware`, `scenario`, `segmind`, `sonauto`, `soundverse`, `stability`, `topmediai` |
| `music` | `lyrics_to_song` | Generate a song from lyrics or a structural song plan | `cloudflare`, `deapi`, `elevenlabs`, `falai`, `generatesongs`, `google`, `minimax`, `musicful`, `musicgpt`, `novita`, `replicate`, `runware`, `segmind`, `sonauto`, `soundverse`, `topmediai`, `wavespeedai` |
| `music` | `media_to_music` | Generate music guided by image, video, or visual media | `elevenlabs`, `google`, `musicgpt` |
| `music` | `audio_to_music` | Generate, transform, cover, remix, or vary music guided by audio | `deapi`, `falai`, `generatesongs`, `minimax`, `modelslab`, `musicfy`, `musicgpt`, `replicate`, `runware`, `scenario`, `sonauto`, `soundverse`, `stability`, `topmediai`, `wavespeedai` |
| `music` | `edit` | Continue, extend, inpaint, outpaint, or repair music | `falai`, `jen`, `musicgpt`, `replicate`, `runware`, `scenario`, `sonauto`, `soundverse`, `stability`, `topmediai` |
| `music` | `stem_separation` | Extract or retrieve stems | `beatoven`, `elevenlabs`, `soundverse` |
| `music` | `voice_conversion` | Convert singing voice, cover voice, or vocal identity inside a music pipeline | `generatesongs`, `musicfy`, `musicgpt`, `soundverse`, `topmediai` |
| `music` | `get_status`, `get_result`, `download`, `update_cost` | Async status/result, download, and cost helpers where implemented | matching operation provider |
| `image` | `generate` | Text-to-image generation | `bfl`, `deepinfra`, `falai`, `fireworks`, `google`, `huggingface`, `openai`, `openrouter`, `runway`, `stability`, `together`, `xai` |
| `image` | `edit` | Prompt-guided image editing | `bfl`, `deepinfra`, `falai`, `fireworks`, `google`, `huggingface`, `openai`, `openrouter`, `runway`, `stability`, `together`, `xai` |
| `image` | `remix` | Reference-image guided generation | `bfl`, `deepinfra`, `falai`, `fireworks`, `google`, `huggingface`, `openai`, `openrouter`, `runway`, `stability`, `together`, `xai` |
| `image` | `analyze` | Vision and multimodal analysis | `anthropic`, `deepinfra`, `falai`, `fireworks`, `google`, `groq`, `huggingface`, `mistral`, `openai`, `openrouter`, `together`, `xai` |
| `image` | `update_cost` | Post-hoc cost refresh where implemented | `openrouter` |
| `video` | `generate` / `text_to_video` | Prompt-only video generation | `falai`, `google`, `hedra`, `heygen`, `huggingface`, `runway`, `together`, `xai` |
| `video` | `image_to_video` | Prompt + image video generation | `falai`, `google`, `hedra`, `heygen`, `runway`, `together`, `xai` |
| `video` | `video_to_video` | Source-video guided generation/editing | `falai`, `google`, `hedra`, `runway`, `together`, `xai` |
| `video` | `motion_control` | Character or motion-reference video generation | `falai`, `hedra`, `runway` |
| `video` | `avatar_video` | Avatar or talking-video generation from speech | `falai`, `hedra`, `heygen`, `runway` |
| `video` | `video_with_audio` | Generate/add audio for a source video | `hedra`, `runway`, `together` |
| `video` | `create_avatar` | Create a provider avatar/persona | `heygen`, `runway` |
| `video` | `image_lipsync` | Image/avatar + audio lip-sync video | `falai`, `heygen` |
| `video` | `video_lipsync` | Source-video + audio lip-sync video | `falai`, `heygen` |
| `video` | `agent_video`, `translate` | Video Agent and video translation workflows | `heygen` |
| `video` | resource helpers | Videos, lipsyncs, translations, proofreads, avatars, looks, brand kits, and agent sessions | `heygen` |
| `video` | `get_status`, `get_result`, `download` | Async request helpers for video operations | matching operation provider |
| `media` | `upload_asset`, `delete_asset` | Provider asset upload and deletion | `heygen` |
| `webhooks` | endpoint and event helpers | Provider webhook endpoint management | `heygen` |
| `account` | `get_current_user` | Account and balance lookup | `heygen` |

See the
[provider matrix](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/providers.md)
for per-provider documentation links, including operation-specific
[`docs/music`](https://github.com/reiarthur/easy-ai-clients/tree/main/docs/music)
pages.

## Selecting Providers

Every dispatcher requires `api=`. The value must match a supported provider
identifier for that operation.

```python
from easy_ai_clients import account, audio, image, media, music, text, video, webhooks

print(text.available_apis())
print(audio.available_synthesize_apis())
print(audio.available_transcribe_apis())
print(audio.available_voice_apis())
print(music.available_apis())
print(music.available_text_to_music_apis())
print(music.available_lyrics_to_song_apis())
print(music.available_media_to_music_apis())
print(music.available_audio_to_music_apis())
print(music.available_edit_apis())
print(music.available_stem_separation_apis())
print(music.available_voice_conversion_apis())
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
print(video.available_agent_video_apis())
print(video.available_translate_apis())
print(video.available_video_resource_apis())
print(media.available_apis())
print(webhooks.available_apis())
print(account.available_apis())
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

voices = audio.list_voices(api="elevenlabs")
designed = audio.design_voice(
    "Warm, calm product narrator.",
    api="elevenlabs",
)

bundle = audio.transcribe("narration.mp3", api="deepgram")
print(bundle["text"])

bundle = audio.update_cost("transcribe", bundle, api="deepgram")
```

Transcription inputs may be local paths, supported URLs, bytes, base64 strings,
data URLs, or `pydub.AudioSegment` objects when the selected provider adapter
supports that input form.

Deepgram transcription sends one provider request per `audio.transcribe(...)`
call, reusing prepared bytes directly when provided. The library does not
split or chunk Deepgram audio before upload; segment long media before calling
the library when your workflow needs multiple requests.

To select Deepgram's diarization model, pass `diarize_model` by itself. The
adapter omits its default `diarize=true` when `diarize_model` is provided, and
explicit `diarize` plus `diarize_model` calls are rejected.

```python
from easy_ai_clients.audio import transcribe

result = transcribe(
    "audio.mp3",
    api="deepgram",
    model="nova-3-general",
    diarize_model="latest",
    filler_words=False,
)
```

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

### Music

```python
from easy_ai_clients import music

intro = music.text_to_music(
    "Warm lo-fi loop with soft drums.",
    api="stability",
    duration_seconds=30,
    output_format="mp3",
)

song = music.lyrics_to_song(
    "[Verse]\nWalking under city lights\n[Chorus]\nWe keep moving on",
    prompt="Modern pop ballad with warm vocals.",
    api="minimax",
)

visual_score = music.media_to_music(
    "cover.png",
    prompt="Create a cinematic orchestral theme.",
    api="google",
)

remix = music.audio_to_music(
    "reference.wav",
    prompt="Turn this into a polished pop track.",
    api="musicgpt",
)

extended = music.edit(
    "song.mp3",
    prompt="Extend the ending by 20 seconds.",
    api="sonauto",
)

stems = music.stem_separation("song.mp3", api="elevenlabs")

converted = music.voice_conversion(
    "vocal.wav",
    voice="voice-id",
    api="musicfy",
)
```

`music.generate(...)` is an alias for `music.text_to_music(...)`.

Music calls return normalized dictionaries with stable fields such as
`provider`, `operation`, `model`, `status`, `request_id`, `audio_url`,
`music_url`, `output_path`, `audio`, `stems`, `cost_usd`, `cost_currency`,
`cost_is_estimated`, `cost_source`, `cost_details`, `provider_metadata`,
`raw_response`, and `warnings`. `music_url` aliases `audio_url`.

Some music providers submit async jobs. Use `music.get_status(...)`,
`music.get_result(...)`, or `music.download(...)` with the same operation and
provider. If a provider module does not implement a helper, the helper may
raise `NotImplementedError`.

```python
from easy_ai_clients import music

status = music.get_status("text_to_music", "request-id", api="falai")

result = music.get_result(
    "text_to_music",
    "request-id",
    output_path="song.mp3",
    api="falai",
)

downloaded = music.download(
    "text_to_music",
    audio_url="https://example.com/song.mp3",
    output_path="song.mp3",
    api="google",
)
```

Direct music downloads require `output_path`. The wrapper does not save files
implicitly.

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

agent = video.agent_video("Create a concise onboarding video.", api="heygen", sync=False)
translated = video.translate(
    video="speaker.mp4",
    output_languages=["Portuguese"],
    api="heygen",
    sync=False,
)
```

Video media inputs accept local file paths, public `http` / `https` URLs, or
data URLs. `sync=False` returns provider request IDs and queue/task metadata;
use `video.get_status`, `video.get_result`, or `video.download` with the same
operation and provider.

Async video results preserve safe provider references such as `status_url`,
`response_url`, `result_url`, `task_url`, and `operation_url` when the provider
returns them. Pass those values back to the helper calls when present; the older
`request_id` + `model` + `api` flow remains supported as a fallback.

```python
from easy_ai_clients import video

submitted = video.image_to_video(
    "Slow cinematic camera push-in.",
    "input.png",
    api="falai",
    model="fal-ai/ltx-2-19b/distilled/image-to-video",
    sync=False,
)

status = video.get_status(
    "image_to_video",
    submitted["request_id"],
    api="falai",
    model=submitted["model"],
    status_url=submitted.get("status_url"),
)

result = video.get_result(
    "image_to_video",
    submitted["request_id"],
    api="falai",
    model=submitted["model"],
    response_url=submitted.get("response_url"),
)
```

For direct `video.download(..., video_url=...)`, pass `output_path`; omitting it
returns a normalized failure instead of silently returning `None`.

### Helper Modules

```python
from easy_ai_clients import account, media, webhooks

me = account.get_current_user(api="heygen")
asset = media.upload_asset("intro.mp4", api="heygen")

endpoint = webhooks.create_endpoint(
    "https://example.com/heygen/webhook",
    api="heygen",
    event_types=["video.completed"],
)

media.delete_asset(asset["data"]["asset_id"], api="heygen", confirm=True)
```

HeyGen delete helpers require `confirm=True` so cleanup stays explicit.

## Return Contracts

| Operation | Normalized result |
| --- | --- |
| `text.generate(...)` | `request_id`, `cost_source`, `cost_usd`, `input_text`, optional `instruction`, `output_text`; failures add `error` and usually `warnings` |
| `audio.generate(...)` | `cost_usd`, `audio` as `pydub.AudioSegment`, `words`; failures use `audio=None`, `words={}`, and add `error` |
| `audio.list_voices(...)`, `audio.get_voice(...)`, `audio.design_voice(...)`, `audio.clone_voice(...)` | `provider`, optional `operation`, `data`, `raw_response`; unsupported helper operations add `warnings` and `error.type="unsupported_operation"` |
| `audio.transcribe(...)` | `text`, optional `words` / `segments` / `silences`, speaker metadata, `provider_metadata`, `request_id`, `cost_usd`, `cost_source`, `cost_is_estimated`, `cost_lookup_error`, optional `mkd`; failures add `error` |
| `music.generate(...)`, `music.text_to_music(...)`, `music.lyrics_to_song(...)`, `music.media_to_music(...)`, `music.audio_to_music(...)`, `music.edit(...)`, `music.voice_conversion(...)` | `provider`, `operation`, `model`, `status`, `request_id`, `audio_url`, `music_url`, `output_path`, `audio`, `cost_usd`, `cost_currency`, `cost_is_estimated`, `cost_source`, `cost_details`, `provider_metadata`, `raw_response`, `warnings`; failures add `error` |
| `music.stem_separation(...)` | Same music fields, with `stems` as the main structured output |
| `music.get_status(...)`, `music.get_result(...)`, `music.download(...)`, `music.update_cost(...)` | Async status/result, direct download, and cost helper results where implemented; unsupported helpers may raise `NotImplementedError` |
| `image.generate(...)`, `image.edit(...)`, `image.remix(...)` | `cust_usd`, `cost_usd`, `cost_currency`, `cost_is_estimated`, `cost_source`, `cost_details`, `base64`, `warnings`, `request_id`; failures use `base64=""` and add `error` |
| `image.analyze(...)` | `request_id`, `cost_usd`, `cost_currency`, `cost_is_estimated`, `cost_source`, `cost_details`, `input_text`, `output`; failures add `error` |
| `video.generate(...)`, `video.text_to_video(...)`, `video.image_to_video(...)`, `video.video_to_video(...)`, `video.motion_control(...)`, `video.avatar_video(...)`, `video.video_with_audio(...)`, `video.create_avatar(...)`, `video.image_lipsync(...)`, `video.video_lipsync(...)` | `provider`, `model`, `status`, `request_id`, `video_url`, `output_path`, `cost_usd`, `cost_is_estimated`, `cost_source`, `raw_response`, plus safe async refs such as `status_url`, `response_url`, `task_url`, or `operation_url` when available; failures use `status="failed"` and add `error` |
| `video` resource helpers, `media`, `webhooks`, `account` | `provider`, `data`, `raw_response`; destructive delete helpers require `confirm=True` |

The legacy image generation/edit/remix cost key `cust_usd` is preserved as an
alias while new code can use the standardized `cost_usd` metadata.

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
- Deepgram transcription first tries exact Management/Usage lookup by request
  ID, then estimates Nova-3 models from official pricing when lookup is
  unavailable.
- Video adapters currently report estimated cost from documented provider
  pricing tables when metadata exists.
- fal.ai video adapters can use the official pricing estimate API when callers
  pass `billing_unit_quantity` or `unit_quantity` explicitly.
- Music adapters normalize unknown cost as `cost_usd=0.0`,
  `cost_currency="USD"`, `cost_is_estimated=False`,
  `cost_source="unavailable"`, and `cost_details={}`.
- Unknown cost is `0.0` with `cost_source="unavailable"` and a warning or
  `cost_lookup_error` explaining that pricing metadata is not documented.

```python
from easy_ai_clients import audio, image, music, text, video

text_result = text.generate("ping", api="openrouter")
text_result = text.update_cost(text_result, api="openrouter")

image_result = image.generate("a tiny robot", api="openrouter")
image_result = image.update_cost("generate", image_result, api="openrouter")

transcript = audio.transcribe("meeting.mp3", api="deepgram")
transcript = audio.update_cost("transcribe", transcript, api="deepgram")

video_result = video.generate("a four-second product shot", api="google")
print(video_result["cost_is_estimated"])

music_result = music.text_to_music("a short product jingle", api="stability")
print(music_result["cost_source"])
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
- [Operation examples](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/operation_examples.md)
- [Error handling](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/errors.md)
- [Full docs directory](https://github.com/reiarthur/easy-ai-clients/tree/main/docs)
- [Changelog](https://github.com/reiarthur/easy-ai-clients/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/reiarthur/easy-ai-clients/blob/main/CONTRIBUTING.md)

## License

MIT. See
[LICENSE](https://github.com/reiarthur/easy-ai-clients/blob/main/LICENSE).
