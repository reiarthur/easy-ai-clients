# Usage Patterns

This guide documents the public dispatcher layer. Provider modules under
private `_apis` packages are implementation details and should not be imported
by applications.

## Imports

```python
from easy_ai_clients import account, audio, image, media, music, text, video, webhooks
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
from easy_ai_clients import account, audio, image, media, music, text, video, webhooks

text.available_apis()
audio.available_synthesize_apis()
audio.available_transcribe_apis()
audio.available_voice_apis()
image.available_generate_apis()
image.available_edit_apis()
image.available_remix_apis()
image.available_analyze_apis()
music.available_apis()
video.available_text_to_video_apis()
video.available_image_to_video_apis()
video.available_video_to_video_apis()
video.available_motion_control_apis()
video.available_avatar_video_apis()
video.available_video_with_audio_apis()
video.available_create_avatar_apis()
video.available_image_lipsync_apis()
video.available_video_lipsync_apis()
video.available_agent_video_apis()
video.available_translate_apis()
video.available_video_resource_apis()
media.available_apis()
webhooks.available_apis()
account.available_apis()
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

## Voice Helpers

Use voice helpers to inspect provider voice catalogs or create account-specific
voices before calling speech or avatar workflows.

```python
from easy_ai_clients import audio

voices = audio.list_voices(api="heygen", engine="starfish", limit=5)
voice_id = voices["data"]["voices"][0]["voice_id"]

details = audio.get_voice(voice_id, api="heygen")

designed = audio.design_voice(
    "Warm, clear product narrator.",
    api="elevenlabs",
)

cloned = audio.clone_voice(
    audio_input="speaker-sample.wav",
    voice_name="Launch Narrator",
    api="elevenlabs",
)
```

Return keys:

- `provider`
- `operation` when the adapter exposes it
- `data`
- `raw_response`
- optional `warnings` and `error` for unsupported helper operations

Providers that only expose a catalog, such as DeepInfra, Mistral, and Together,
return a normalized `unsupported_operation` result for `design_voice` and
`clone_voice`.

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
For Deepgram, the prepared payload is sent as one provider request per
`transcribe(...)` call; the adapter does not split or chunk audio before upload.
Segment long media before calling the library if you want multiple Deepgram
requests.

For Deepgram's newer diarization model selector, pass `diarize_model` without
also passing `diarize=True`. The adapter omits its default `diarize=true` when
`diarize_model` is present and rejects explicit `diarize` plus
`diarize_model` conflicts.

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
- `cost_usd`
- `cost_currency`
- `cost_is_estimated`
- `cost_source`
- `cost_details`
- `base64`
- `warnings`
- `request_id`

The legacy `cust_usd` key is preserved as an alias. New integrations should
prefer the standardized `cost_usd` metadata.

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
- `cost_currency`
- `cost_is_estimated`
- `cost_source`
- `cost_details`
- `input_text`
- `output`

## Music Generation

```python
from easy_ai_clients import music

generation = music.generate(
    lyrics="[Verse]\nThe morning opens wide\n[Chorus]\nWe keep the light alive",
    api="runware",
    model="ace_step_v1_5_xl_turbo",
    style="rock",
)

generation = music.get_status(generation)
generation = music.download_result(generation)
```

Return keys:

- `provider`
- `model`
- `model_key`
- `status`
- `request_id`
- `output_path`
- `cost_usd`
- `cost_currency`
- `cost_source`
- `cost_is_estimated`
- `cost_details`
- `metadata`

`style` must be an exact preset id. Presets expose:

- `style_prompts.small`, `style_prompts.medium`, and `style_prompts.large`.
- `voice_presets.small`, `voice_presets.medium`, and `voice_presets.large`,
  each with `male` and `female`.
- `voice_presets.default_gender`.

Use `prompt` for direct musical direction. If both `style` and `prompt` are
passed, `prompt` replaces preset style and voice guidance after normal prompt
validation.

By default, generation starts with `large` style and `large` voice prompts.
When a provider raises `MusicInputLimitError`, the router retries preset prompt
sizes in this order before returning the normal repair error:

1. `style_prompts.large` + `voice_presets.large`
2. `style_prompts.large` + `voice_presets.medium`
3. `style_prompts.medium` + `voice_presets.medium`
4. `style_prompts.medium` + `voice_presets.small`
5. `style_prompts.small` + `voice_presets.small`

If all preset-size attempts exceed provider limits, the router retries
`large` + `large` once so the existing `MusicInputLimitError` repair data is
preserved.

ElevenLabs is the exception to the initial voice size: preset-based generation
uses `style_prompts.large` with `voice_presets.small` by default to keep direct
music prompts concise. Other APIs keep the default `large` + `large` start.

Duration is normalized per provider/model:

| API | Model key | Native model | Min | Max | Missing or invalid `duration` | Provider application |
| --- | --- | --- | ---: | ---: | --- | --- |
| `deapi` | `ace_step_v1_5_turbo` | `AceStep_1_5_Turbo` | `10s` | `300s` | Uses `60s` | Sent as `duration` |
| `deapi` | `ace_step_1_5_xl_turbo_int8` | `AceStep_1_5_XL_Turbo_INT8` | `10s` | `300s` | Uses `60s` | Sent as `duration` |
| `elevenlabs` | `eleven_music` | `music_v2` | `3s` | `600s` | Omits duration | Sent as `music_length_ms` |
| `elevenlabs` | `eleven_music_v2` | `music_v2` | `3s` | `600s` | Omits duration | Sent as `music_length_ms` |
| `elevenlabs` | `music_v2` | `music_v2` | `3s` | `600s` | Omits duration | Sent as `music_length_ms` |
| `google` | `lyria_3_clip_preview` | `lyria-3-clip-preview` | `30s` | `30s` | Ignores duration | Not sent |
| `google` | `lyria_3_pro_preview` | `lyria-3-pro-preview` | `15s` | `180s` | Omits duration | Added as prompt text |
| `runware` | `ace_step_v1_5_turbo` | `runware:ace-step@v1.5-turbo` | `30s` | `300s` | Uses `60s` | Sent as `duration` |
| `runware` | `ace_step_v1_5_xl_base` | `runware:ace-step@v1.5-xl-base` | `30s` | `300s` | Uses `60s` | Sent as `duration` |
| `runware` | `ace_step_v1_5_xl_sft` | `runware:ace-step@v1.5-xl-sft` | `30s` | `300s` | Uses `60s` | Sent as `duration` |
| `runware` | `ace_step_v1_5_xl_turbo` | `runware:ace-step@v1.5-xl-turbo` | `30s` | `300s` | Uses `60s` | Sent as `duration` |

Numeric `duration` values may be `int`, `float`, or numeric strings. Floats
are truncated to `int` and then clamped. `bool`, empty strings, non-numeric
text, lists, and objects are treated as missing values.

Use `gender="male"`, `gender="female"`, `gender="both"`, or
`voice_description="..."` for prompt-level vocal guidance. Public
`negative_prompt` is not supported for music.

When prompt or lyric input exceeds provider limits, `music.generate(...)`
raises `music.MusicInputLimitError` before generation:

| API | Field | Limit | Unit |
| --- | --- | ---: | --- |
| `deapi` | `caption` / prompt | `3000` | characters |
| `deapi` | `lyrics` | `3000` | characters |
| `elevenlabs` | final prompt with lyrics appended | `4100` | characters |
| `google` | final `contents` payload | `131072` | tokens via `countTokens` |
| `runware` | `positivePrompt` | `3000` | characters |
| `runware` | `settings.lyrics` | `3000` | characters |

The exception exposes `to_dict()` and `repair_prompts` so callers can ask a
text model to shorten only the fields that exceeded the limit.

The public result does not include raw provider responses, credentials, auth
headers, audio URLs, or large audio payloads.

Local helper functions do not call providers:

When `build_lyrics_prompt(...)` receives a valid `style`, it embeds the
preset `style_prompts.large` text as lyric-writing guidance instead of exposing
only the style ID.

When called as `build_lyrics_prompt(..., api="elevenlabs")`, the helper keeps
the same return shape but uses `voice_presets.small`, asks for short singable
lines, and avoids vocal-role tags such as `[Male Lead]`, `[Female Lead]`, and
`[Duet]`.

```python
options = music.get_generation_options(api="runware")
styles = music.get_style_presets(fields=["id", "description"])
lyrics_prompt = music.build_lyrics_prompt(
    "Brazilian Portuguese pop rock with a hopeful chorus.",
    duration=60,
    style="rock",
    gender="female",
    api="elevenlabs",
)
```

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

agent = video.agent_video(
    "Create a concise onboarding video.",
    api="heygen",
    sync=False,
)

translated = video.translate(
    video="speaker.mp4",
    output_languages=["Portuguese"],
    api="heygen",
    sync=False,
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
- safe provider async refs such as `status_url`, `response_url`, `result_url`,
  `task_url`, or `operation_url` when available

Supported video media inputs are local paths, public `http` / `https` URLs, and
data URLs. When `sync=False`, the dispatcher returns submitted queue/task
metadata; pass the same operation name to `video.get_status`,
`video.get_result`, or `video.download`.

Provider-returned async references are preserved for all async video operations
that expose them. Pass these refs back to helper calls when present; calls that
only provide `request_id`, `model`, and `api` continue to use the provider's
fallback URL construction.

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

For direct downloads with `video.download(..., video_url=...)`, provide an
`output_path`. Without one, the public dispatcher returns a normalized failure
instead of `None`. Providers without real async follow-up, such as the current
Hugging Face text-to-video wrapper, document `sync=False` as a signature
compatibility no-op and return a completed synchronous result.

## HeyGen Video Resources

HeyGen v3 exposes resource helpers for existing videos, lip-syncs,
translations, proofreads, avatars, avatar looks, brand kits, and Video Agent
sessions.

```python
from easy_ai_clients import video

videos = video.list_videos(api="heygen", limit=10)
languages = video.list_translation_languages(api="heygen")

proofread = video.create_proofread(
    video="speaker.mp4",
    output_languages=["Portuguese"],
    title="Portuguese review",
    api="heygen",
)

video.generate_proofread(proofread["data"]["id"], api="heygen")
```

Delete helpers such as `video.delete_video(..., api="heygen")` and
`video.delete_avatar_look(..., api="heygen")` require `confirm=True`.

## Media, Webhooks, and Account

The helper modules currently expose HeyGen v3 workflows and are structured for
future providers.

```python
from easy_ai_clients import account, media, webhooks

me = account.get_current_user(api="heygen")
print(me["data"])

asset = media.upload_asset("intro.mp4", api="heygen")
asset_id = asset["data"]["asset_id"]

endpoint = webhooks.create_endpoint(
    "https://example.com/heygen/webhook",
    api="heygen",
    event_types=["video.completed", "video.failed"],
)

webhooks.rotate_secret(endpoint["data"]["id"], api="heygen")
events = webhooks.list_events(api="heygen", limit=20)

media.delete_asset(asset_id, api="heygen", confirm=True)
```

These helpers return `provider`, `data`, and `raw_response`. Destructive delete
helpers require explicit `confirm=True`.

## Provider-Native Kwargs

Extra keyword arguments are provider-native. The provider docs list models and
parameters that have been analyzed, but that metadata is documentation and
pricing/default reference, not a local acceptance list. New provider models or
parameters can be passed before this library documents them.

The music dispatcher is the exception to this broad forwarding behavior:
`easy_ai_clients.music` uses an explicit validated provider/model matrix and
rejects unsupported models, unknown styles, removed public kwargs, and
public `negative_prompt` usage before provider dispatch.

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
from easy_ai_clients import audio, image, music, text, video

text_result = text.generate("ping", api="openrouter")
text_result = text.update_cost(text_result, api="openrouter")

image_result = image.generate("a small robot", api="openrouter")
image_result = image.update_cost("generate", image_result, api="openrouter")

transcript = audio.transcribe("speech.mp3", api="deepgram")
transcript = audio.update_cost("transcribe", transcript, api="deepgram")

song = music.generate("short lyrics for a chorus", api="runware", prompt="upbeat pop rock")
print(song["cost_source"])

video_result = video.generate("a short product clip", api="google")
print(video_result["cost_is_estimated"])
```

Cost helpers raise `NotImplementedError` when the selected provider does not
support post-hoc cost lookup. Documented pricing metadata is used when known;
unknown model or request costs are reported as `0.0` with
`cost_source="unavailable"` and a warning or lookup-error reason.

## More Documentation

- [Provider matrix](providers.md)
- [Operation examples](operation_examples.md)
- [Configuration](configuration.md)
- [Error handling](errors.md)
