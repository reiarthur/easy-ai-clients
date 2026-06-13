# Provider Gap Audit

Audit scope: providers already present in the library and categories/subcategories
already exposed by the public dispatchers. Legacy, deprecated, or near-shutdown
APIs are excluded, including OpenAI Sora/Videos and Stability Stable Video
Diffusion.

| Provider | Category | Subcategory | Official endpoint/surface | Status | Pricing source | Implemented |
| --- | --- | --- | --- | --- | --- | --- |
| openai | audio | transcribe | `/v1/audio/transcriptions` | current | official per-minute table | yes |
| openai | video | text/image/video | Sora/Videos | deprecated, shutdown 2026-09-24 | excluded | no |
| groq | audio | generate | `/openai/v1/audio/speech` | current | unavailable | yes |
| groq | audio | transcribe | `/openai/v1/audio/transcriptions` | current | official hourly table | yes |
| groq | text | list_models | `/openai/v1/models` | current | not applicable | already implemented |
| deepgram | audio | generate | `/v1/speak` | current | official character table where known | yes |
| mistral | audio | transcribe | `/v1/audio/transcriptions` | current | unavailable | yes |
| mistral | audio | voices | `/v1/audio/voices` | current | not applicable | yes |
| mistral | image | analyze | chat/vision and OCR surface | current | unavailable | yes |
| google | audio | transcribe | Gemini `generateContent` audio understanding | current | unavailable | yes |
| deepinfra | audio | transcribe | OpenAI-compatible STT gateway | current | unavailable | yes |
| deepinfra | audio | voices | voice catalog surface | current | not applicable | yes |
| deepinfra | image | generate/edit/remix/analyze | image and vision APIs | current | unavailable | yes |
| elevenlabs | audio | generate | TTS and sound generation | current | headers/units only for non-speech | yes |
| elevenlabs | audio | voices | voices/design/clone APIs | current | not applicable | yes |
| huggingface | audio | transcribe | Inference Providers ASR | current | unavailable | yes |
| huggingface | image | generate/edit/remix/analyze | Inference Providers image tasks | current | unavailable | yes |
| huggingface | video | text_to_video | Inference Providers text-to-video | current | unavailable | yes |
| openrouter | audio | generate/transcribe | OpenRouter audio APIs | current | provider response usage when present | yes |
| together | audio | voices | `/v1/voices` | current | not applicable | yes |
| together | video | text/image/video/video_with_audio | `/v1/videos` | current | unavailable | yes |
| runway | image | generate/edit/remix | Runway image tasks | current | unavailable | yes |
| runway | audio | generate | Runway speech/sound tasks | current | credits converted at `$0.01` | yes |
| runway | video | video_with_audio | Runway audio/video task surface | current | credits converted at `$0.01` | yes |
| xai | audio | transcribe | xAI STT | current | official hourly table | yes |
| xai | video | text/image/video | `/v1/videos/generations`, `/v1/videos/edits` | current | official per-second table | yes |
| stability | audio | generate | Stable Audio text-to-audio | current | official per-generation table where known | yes |
| stability | video | video generation | Stable Video Diffusion | deprecated 2025-07-24 | excluded | no |
| deapi | music | generate | `/api/v1/client/txt2music` | current | price endpoint or status response | yes |
| elevenlabs | music | generate | `/v1/music` | current | local validated estimate | yes |
| google | music | generate | Lyria `generateContent` | preview | local validated table | yes |
| runware | music | generate | `/v1` audio inference | current | provider response when available | yes |
| anthropic | text | list_models | model catalog endpoint | current | not applicable | already implemented |
| cohere | text | list_models | model catalog endpoint | current | not applicable | already implemented |
| deepseek | text | list_models | OpenAI-compatible models endpoint | current | not applicable | already implemented |

## Documentation Coverage

Each implemented provider/subcategory above is linked from `docs/providers.md`.
Copyable examples for the public dispatcher layer live in
`docs/operation_examples.md`, while provider-specific pages stay under
`docs/<category>/<subcategory>/<provider>.md`. Audio voice helpers, HeyGen
video resources, media assets, webhooks, and account helpers have their own
provider pages even though they are lightweight helper categories.
