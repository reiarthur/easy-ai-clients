# Operation Examples

This page gives copyable examples for every public category and subcategory.
Provider-specific pages in `docs/<category>/<subcategory>/<provider>.md`
document defaults, endpoint notes, cost behavior, and limitations.

All dispatchers require `api=...`. Extra keyword arguments are provider-native
and are forwarded whenever the wrapper can assemble a valid request.

## Text

```python
from easy_ai_clients import text

result = text.generate(
    "Write a one-line release note.",
    instruction="Use plain English.",
    api="openai",
    model="gpt-5-nano",
    max_output_tokens=80,
)
print(result["output_text"], result["cost_usd"])

models = text.list_models(api="openai")
```

## Audio generation

`audio.generate` covers speech synthesis and provider-specific non-speech audio
where implemented, such as ElevenLabs sound effects/music, Runway sound
generation, and Stable Audio.

```python
from easy_ai_clients import audio

speech = audio.generate(
    "The launch starts now.",
    api="openai",
    model="tts-1",
    voice="alloy",
)
speech["audio"].export("speech.mp3", format="mp3")

music = audio.generate(
    "Short upbeat product intro, no vocals.",
    api="elevenlabs",
    audio_type="music",
)
music["audio"].export("intro.mp3", format="mp3")
```

## Audio voices

```python
from easy_ai_clients import audio

voices = audio.list_voices(api="heygen", engine="starfish", limit=5)
voice_id = voices["data"]["voices"][0]["voice_id"]

details = audio.get_voice(voice_id, api="heygen")

designed = audio.design_voice(
    "Friendly Brazilian Portuguese narrator with clear diction.",
    api="elevenlabs",
)

cloned = audio.clone_voice(
    audio_input="speaker.wav",
    voice_name="Demo Narrator",
    api="elevenlabs",
)
```

Providers that only expose a catalog return a normalized
`unsupported_operation` result for `design_voice` and `clone_voice`.

## Audio transcription

```python
from easy_ai_clients import audio

prepared = audio.prepare_transcription_audio("meeting.mp3")

deepgram = audio.transcribe(prepared, api="deepgram", model="nova-3")
openai = audio.transcribe(prepared, api="openai", model="gpt-4o-mini-transcribe")

print(deepgram["text"])
print(openai["cost_source"])
```

## Music

```python
from easy_ai_clients import music

track = music.text_to_music(
    "Warm lo-fi loop with soft drums.",
    api="stability",
    duration_seconds=30,
    output_format="mp3",
)

alias_track = music.generate(
    "Upbeat 30-second product intro.",
    api="elevenlabs",
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

stems = music.stem_separation(
    "song.mp3",
    api="elevenlabs",
)

converted = music.voice_conversion(
    "vocal.wav",
    voice="voice-id",
    api="musicfy",
)
```

`music.generate(...)` is an alias for `music.text_to_music(...)`.

## Music async helpers and download

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

Direct music downloads require `output_path`.

## Images

```python
from easy_ai_clients import image

generated = image.generate(
    "A clean app icon of a blue compass.",
    api="openai",
)

edited = image.edit(
    "Replace the background with a white studio backdrop.",
    "input.png",
    mask="mask.png",
    api="stability",
)

remixed = image.remix(
    "Keep the product shape but make it watercolor.",
    ["input.png"],
    api="bfl",
)

analysis = image.analyze(
    "Describe the product and visible text.",
    "input.png",
    api="mistral",
)
```

Image generation/edit/remix results include both `cust_usd` and `cost_usd`.
New code should prefer `cost_usd`.

## Video generation

```python
from easy_ai_clients import video

text_clip = video.text_to_video(
    "Four-second product shot on a studio desk.",
    api="google",
    duration_seconds=4,
)

image_clip = video.image_to_video(
    "Slow push-in with natural motion.",
    image="product.png",
    api="runway",
    duration=5,
)

edited_clip = video.video_to_video(
    "Keep framing, make the lighting warmer.",
    video="source.mp4",
    api="runway",
    duration=5,
)

motion_clip = video.motion_control(
    image="character.png",
    video="motion-reference.mp4",
    api="falai",
    character_orientation="image",
    sync=False,
)

status = video.get_status("motion_control", motion_clip["request_id"], api="falai")
```

When `sync=False`, use `video.get_status`, `video.get_result`, or
`video.download` with the same operation name and provider. If the submitted
result includes provider refs such as `status_url`, `response_url`, `task_url`,
or `operation_url`, pass them back so the helper can use the provider-returned
URL before falling back to `request_id` URL construction.

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

Direct `video.download(..., video_url=...)` calls require `output_path`; the
dispatcher returns a normalized failure instead of silently returning `None`
when no local path is provided.

## Avatar and lip-sync video

```python
from easy_ai_clients import video

avatar = video.create_avatar(
    image="host.png",
    name="Launch Host",
    voice="clara",
    api="runway",
)

talking = video.avatar_video(
    avatar=avatar["avatar_id"],
    text="Welcome to the launch.",
    api="runway",
)

image_sync = video.image_lipsync(
    image="portrait.png",
    audio="voice.wav",
    api="heygen",
)

video_sync = video.video_lipsync(
    video="speaker.mp4",
    audio="voice.wav",
    api="falai",
)
```

## Video with audio, agents, and translation

```python
from easy_ai_clients import video

with_audio = video.video_with_audio(
    video="silent.mp4",
    prompt="Add soft ambient studio room tone.",
    api="together",
    sync=False,
)

agent = video.agent_video(
    "Create a concise onboarding video.",
    api="heygen",
    sync=False,
)

translation = video.translate(
    video="speaker.mp4",
    output_languages=["Spanish", "Portuguese"],
    api="heygen",
    sync=False,
)
```

## HeyGen resource helpers

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

Delete helpers such as `video.delete_video(..., api="heygen")` require
`confirm=True`.

## Media, webhooks, and account

```python
from easy_ai_clients import account, media, webhooks

me = account.get_current_user(api="heygen")

asset = media.upload_asset("intro.mp4", api="heygen")

endpoint = webhooks.create_endpoint(
    "https://example.com/heygen/webhook",
    api="heygen",
    event_types=["video.completed"],
)

webhooks.rotate_secret(endpoint["data"]["id"], api="heygen")
media.delete_asset(asset["data"]["asset_id"], api="heygen", confirm=True)
```
