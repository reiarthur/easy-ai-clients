# Providers

This page is the entry point for the per-provider documentation pages. It
mirrors the operation tree of the public API and lists which environment
variable each provider needs.

The detailed per-provider notes (default models, accepted parameters,
pricing, validation status, known limitations) live alongside this file in
`docs/<modality>/<operation>/<provider>.md`.

For copyable dispatcher examples and normalized response structures, see
[`usage.md`](usage.md).

## Text — `easy_ai_clients.text`

| API | Env var | Notes |
| --- | --- | --- |
| [`anthropic`](text/anthropic.md) | `ANTHROPIC_API_KEY` | Messages API. |
| [`cohere`](text/cohere.md) | `COHERE_API_KEY` | Chat v2. |
| [`deepinfra`](text/deepinfra.md) | `DEEPINFRA_API_KEY` | OpenAI-compatible. |
| [`deepseek`](text/deepseek.md) | `DEEPSEEK_API_KEY` | DeepSeek chat with reasoning. |
| [`falai`](text/falai.md) | `FAL_KEY`; catalog uses `OPENROUTER_API_KEY` | Fal.ai LLM gateway. |
| [`fireworks`](text/fireworks.md) | `FIREWORKS_API_KEY` | Reasoning + speculation kwargs. |
| [`google`](text/google.md) | `GOOGLE_API_KEY` | Gemini `generateContent`. |
| [`groq`](text/groq.md) | `GROQ_API_KEY` | OpenAI-compatible chat. |
| [`huggingface`](text/huggingface.md) | `HUGGINGFACE_API_KEY` | Router / serverless inference. |
| [`mistral`](text/mistral.md) | `MISTRAL_API_KEY` | Chat completions. |
| [`openai`](text/openai.md) | `OPENAI_API_KEY` | Responses API + cost lookup. |
| [`openrouter`](text/openrouter.md) | `OPENROUTER_API_KEY` | Aggregator with `update_cost`. |
| [`together`](text/together.md) | `TOGETHER_API_KEY` | Chat completions + reasoning. |
| [`xai`](text/xai.md) | `XAI_API_KEY` | Grok chat. |

## Audio — `easy_ai_clients.audio`

### `audio.generate(...)` (text-to-speech)

| API | Env var | Notes |
| --- | --- | --- |
| [`deepinfra`](audio/generate/deepinfra.md) | `DEEPINFRA_API_KEY` | Multiple Kokoro/Sesame voices. |
| [`elevenlabs`](audio/generate/elevenlabs.md) | `ELEVENLABS_API_KEY` | Native word/character timings. |
| [`google`](audio/generate/google.md) | `GOOGLE_API_KEY` | Gemini speech. |
| [`mistral`](audio/generate/mistral.md) | `MISTRAL_API_KEY` | Voxtral / Le Chat speech. |
| [`openai`](audio/generate/openai.md) | `OPENAI_API_KEY` | `gpt-4o-mini-tts` + `tts-1`. |
| [`together`](audio/generate/together.md) | `TOGETHER_API_KEY` | OpenAI-compatible TTS. |
| [`xai`](audio/generate/xai.md) | `XAI_API_KEY` | Grok speech. |

### `audio.transcribe(...)` (speech-to-text)

| API | Env var | Notes |
| --- | --- | --- |
| [`deepgram`](audio/transcribe/deepgram.md) | `DEEPGRAM_API_KEY` (+ optional `DEEPGRAM_PROJECT_ID`) | Kept Nova, Enhanced, Base specialty, and Whisper models; supports `audio.update_cost`. |
| [`elevenlabs`](audio/transcribe/elevenlabs.md) | `ELEVENLABS_API_KEY` | Scribe v1/v2 with omitted-language detection. |
| [`falai`](audio/transcribe/falai.md) | `FAL_KEY` | Routes to ElevenLabs Scribe via Fal.ai Pricing API. |
| [`fireworks`](audio/transcribe/fireworks.md) | `FIREWORKS_API_KEY` | Whisper v3 and Whisper v3 Turbo. |
| [`speechmatics`](audio/transcribe/speechmatics.md) | `SPEECHMATICS_API_KEY` | Standard/enhanced batch with `language="auto"`. |
| [`together`](audio/transcribe/together.md) | `TOGETHER_API_KEY` | Whisper-large-v3 and Parakeet serverless models. |

## Image — `easy_ai_clients.image`

### `image.generate(...)` (text-to-image)

| API | Env var | Doc |
| --- | --- | --- |
| `bfl` | `BFL_API_KEY` | [`bfl`](image/generate/bfl.md) |
| `falai` | `FAL_KEY` | [`falai`](image/generate/falai.md) |
| `fireworks` | `FIREWORKS_API_KEY` | [`fireworks`](image/generate/fireworks.md) |
| `google` | `GOOGLE_API_KEY` | [`google`](image/generate/google.md) |
| `openai` | `OPENAI_API_KEY` | [`openai`](image/generate/openai.md) |
| `openrouter` | `OPENROUTER_API_KEY` | [`openrouter`](image/generate/openrouter.md) |
| `stability` | `STABILITY_API_KEY` | [`stability`](image/generate/stability.md) |
| `together` | `TOGETHER_API_KEY` | [`together`](image/generate/together.md) |
| `xai` | `XAI_API_KEY` | [`xai`](image/generate/xai.md) |

### `image.edit(...)` (prompt + mask editing)

| API | Env var | Doc |
| --- | --- | --- |
| `bfl` | `BFL_API_KEY` | [`bfl`](image/edit/bfl.md) |
| `falai` | `FAL_KEY` | [`falai`](image/edit/falai.md) |
| `fireworks` | `FIREWORKS_API_KEY` | [`fireworks`](image/edit/fireworks.md) |
| `google` | `GOOGLE_API_KEY` | [`google`](image/edit/google.md) |
| `openai` | `OPENAI_API_KEY` | [`openai`](image/edit/openai.md) |
| `openrouter` | `OPENROUTER_API_KEY` | [`openrouter`](image/edit/openrouter.md) |
| `stability` | `STABILITY_API_KEY` | [`stability`](image/edit/stability.md) |
| `together` | `TOGETHER_API_KEY` | [`together`](image/edit/together.md) |
| `xai` | `XAI_API_KEY` | [`xai`](image/edit/xai.md) |

For `edit`, the public mask convention is **black = editable, white =
preserve**. Each provider adapter converts that contract to whatever the
underlying API expects.

### `image.remix(...)` (reference-image guided)

| API | Env var | Doc |
| --- | --- | --- |
| `bfl` | `BFL_API_KEY` | [`bfl`](image/remix/bfl.md) |
| `falai` | `FAL_KEY` | [`falai`](image/remix/falai.md) |
| `fireworks` | `FIREWORKS_API_KEY` | [`fireworks`](image/remix/fireworks.md) |
| `google` | `GOOGLE_API_KEY` | [`google`](image/remix/google.md) |
| `openai` | `OPENAI_API_KEY` | [`openai`](image/remix/openai.md) |
| `openrouter` | `OPENROUTER_API_KEY` | [`openrouter`](image/remix/openrouter.md) |
| `stability` | `STABILITY_API_KEY` | [`stability`](image/remix/stability.md) |
| `together` | `TOGETHER_API_KEY` | [`together`](image/remix/together.md) |
| `xai` | `XAI_API_KEY` | [`xai`](image/remix/xai.md) |

### `image.analyze(...)` (vision)

| API | Env var | Doc |
| --- | --- | --- |
| `anthropic` | `ANTHROPIC_API_KEY` | [`anthropic`](image/analyze/anthropic.md) |
| `falai` | `FAL_KEY` | [`falai`](image/analyze/falai.md) |
| `fireworks` | `FIREWORKS_API_KEY` | [`fireworks`](image/analyze/fireworks.md) |
| `google` | `GOOGLE_API_KEY` | [`google`](image/analyze/google.md) |
| `groq` | `GROQ_API_KEY` | [`groq`](image/analyze/groq.md) |
| `openai` | `OPENAI_API_KEY` | [`openai`](image/analyze/openai.md) |
| `openrouter` | `OPENROUTER_API_KEY` | [`openrouter`](image/analyze/openrouter.md) |
| `together` | `TOGETHER_API_KEY` | [`together`](image/analyze/together.md) |
| `xai` | `XAI_API_KEY` | [`xai`](image/analyze/xai.md) |

## Video - `easy_ai_clients.video`

### `video.generate(...)` / `video.text_to_video(...)`

| API | Env var | Doc |
| --- | --- | --- |
| `falai` | `FAL_KEY` | [`falai`](video/text_to_video/falai.md) |
| `google` | `GOOGLE_API_KEY` | [`google`](video/text_to_video/google.md) |
| `runway` | `RUNWAYML_API_SECRET` | [`runway`](video/text_to_video/runway.md) |

### `video.image_to_video(...)`

| API | Env var | Doc |
| --- | --- | --- |
| `falai` | `FAL_KEY` | [`falai`](video/image_to_video/falai.md) |
| `google` | `GOOGLE_API_KEY` | [`google`](video/image_to_video/google.md) |
| `runway` | `RUNWAYML_API_SECRET` | [`runway`](video/image_to_video/runway.md) |

### `video.motion_control(...)`

| API | Env var | Doc |
| --- | --- | --- |
| `falai` | `FAL_KEY` | [`falai`](video/motion_control/falai.md) |
| `runway` | `RUNWAYML_API_SECRET` | [`runway`](video/motion_control/runway.md) |

### `video.image_lipsync(...)`

| API | Env var | Doc |
| --- | --- | --- |
| `falai` | `FAL_KEY` | [`falai`](video/image_lipsync/falai.md) |

### `video.video_lipsync(...)`

| API | Env var | Doc |
| --- | --- | --- |
| `falai` | `FAL_KEY` | [`falai`](video/video_lipsync/falai.md) |
