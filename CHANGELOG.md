# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] — 2026-04-19

### Fixed — provedores de texto auditados contra documentação oficial
- **OpenAI:** removido `gpt-5.4-mini` (ID inexistente na documentação oficial). `gpt-5-mini` mantido.
- **Mistral:** corrigido ID `mistral-medium-2508+1` (sufixo `+1` anômalo) para `mistral-medium-3-2508` (ID oficial da família Mistral Medium 3.1).
- **OpenRouter:** removido sufixo `:nitro` de `openai/gpt-oss-20b:nitro`. O ID canônico documentado é `openai/gpt-oss-20b`. Se precisar de roteamento acelerado, o OpenRouter oferece isso via parâmetros de provider routing (consulte a documentação atual do OpenRouter).
- **Anthropic:** catálogo atualizado para os modelos atuais documentados em abril de 2026. `default_model` agora é `claude-opus-4-7`. Catálogo completo: `claude-opus-4-7` (default), `claude-sonnet-4-6`, `claude-haiku-4-5`, e `claude-sonnet-4-5` (mantido como legacy).

### Added — modelos novos confirmados em documentação oficial
- **Anthropic:** adicionados `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5` ao registry e à tabela de precificação.
- **Perplexity:** adicionados `sonar`, `sonar-reasoning-pro`, `sonar-deep-research` além de `sonar-pro` (default), com pricing oficial em `PRICING_TABLE`.
- **DeepSeek:** adicionado `deepseek-reasoner` (DeepSeek-V3.2 em modo thinking) ao registry e ao pricing, com as mesmas taxas do `deepseek-chat`.

### Escopo da auditoria
Esta versão cobriu os providers de texto priorizados (OpenAI, Anthropic, Google, OpenRouter, xAI, Mistral, DeepSeek, Cohere, Perplexity). Os providers de imagem, áudio, vídeo e os demais de texto (Groq, Together, Fireworks, DeepInfra, HuggingFace) não foram re-auditados nesta versão — seus adapters e modelos permanecem inalterados e serão revisados em uma versão futura. Usuários que dependem desses providers devem confirmar manualmente os IDs de modelo contra a documentação oficial de cada fornecedor antes de uso em produção.

---

## [0.2.0] — 2026-04-18

### Changed
- **Project renamed from `multisynth` to `easy-ai-clients`.** The PyPI package is now published as `easy-ai-clients`; the Python import name is `easy_ai_clients`. Update imports from `multisynth.*` to `easy_ai_clients.*`.
- The stateful client class `Multisynth` was renamed to `EasyAiClient`.
- The base exception `MultisynthError` was renamed to `EasyAiClientError`.
- Internal portuguese alias `NovaIntegracaoError` continues to exist for backward compatibility.

### Added
- `easy_ai_clients.image.compose` / `compose_async` — **new image composition operation** that combines a base image with a reference image using a prompt. Typical prompts: *"render the person of image 1 in the pose of image 2"*, *"image 1 in the style of image 2"*. Providers: `google`, `bfl`.
- `ImageCompositionRequest` — new public Pydantic model for the compose operation.
- `client.image.compose` / `compose_async` — stateful-client wrappers for the new operation.
- New text providers: `deepinfra` (`DEEPINFRA_API_KEY`) and `huggingface` (`HUGGINGFACE_API_KEY`).
- New provider aliases: `deep-infra`, `hugging-face`, `hf`.
- Expanded provider catalog exposes `("image", "compose", "google")` and `("image", "compose", "bfl")` specs.

### Migration
```python
# Before (0.1.x)
from multisynth import Multisynth
from multisynth.exceptions import MultisynthError

# After (0.2.0)
from easy_ai_clients import EasyAiClient
from easy_ai_clients.exceptions import EasyAiClientError
```

---

## [0.1.0] — 2026-04-16

### Added

#### Text generation
- `multisynth.text.generate` / `generate_async` — synchronous and async text generation with a single provider call.
- `multisynth.text.batch_generate` / `batch_generate_async` — run multiple requests to the same provider concurrently.
- Providers: `openai`, `groq`, `together`, `fireworks`, `deepseek`, `openrouter`, `xai`, `mistral`, `anthropic`, `google`, `cohere`, `perplexity`.
- Support for sampling controls (`temperature`, `top_p`, `seed`), tool use, structured output (`response_format`), reasoning (`reasoning_effort`, `thinking`), and multimodal inputs (`input_images`).

#### Audio — transcription
- `multisynth.audio.transcribe` / `transcribe_async` — transcribe audio to text with word-level timings and speaker diarization.
- Result includes `.text`, `.words` (`WordTiming`), `.speaker_segments` (`SpeakerSegment`), and `.metadata`.
- Providers: `deepgram`, `assemblyai`, `speechmatics`, `revai`.

#### Audio — speech synthesis
- `multisynth.audio.synthesize` / `synthesize_async` — synthesize spoken audio from text.
- Result includes `.audio_base64`, `.words`, and `.metadata`.
- Providers: `cartesia`, `azure`, `hume`, `elevenlabs`, `murf`.

#### Audio — music generation
- `multisynth.audio.compose` / `compose_async` — generate instrumental music from a text prompt with optional duration control.
- Result includes `.audio_base64` and `.metadata`.
- Providers: `google`, `elevenlabs`, `stability`, `beatoven`, `loudly`.

#### Image generation
- `multisynth.image.generate` / `generate_async` — generate an image from a text prompt.
- Providers: `openai`, `google`, `bfl`, `ideogram`, `stability`, `hedra`.

#### Image transformation
- `multisynth.image.transform` / `transform_async` — transform an input image guided by a prompt, with optional `strength` and `negative_prompt`.
- Providers: `openai`, `google`, `bfl`, `ideogram`, `stability`.

#### Image editing
- `multisynth.image.edit` / `edit_async` — edit an image with an optional mask for inpainting.
- Providers: `openai`, `google`, `bfl`, `ideogram`, `stability`.

#### Video generation
- `multisynth.video.generate` / `generate_async` — generate a video from a prompt, image, or audio. Routes automatically to the `without_audio` or `with_audio` registry depending on whether `audio` is supplied.
- Video files are written directly to `output_path` on the local filesystem.
- Providers (without audio): `runway`, `luma`, `fal`, `hedra`.
- Providers (with audio): `google`, `heygen`, `did`, `hedra`.

#### Lip sync
- `multisynth.video.lipsync` / `lipsync_async` — animate a still image or avatar portrait with a supplied audio track.
- Providers: `heygen`, `did`, `hedra`.

#### Stateful client
- `multisynth.Multisynth` — optional stateful client that shares credentials and request defaults (`timeout_seconds`, `job_timeout_seconds`, `max_retries`) across all modality helpers.

#### Core infrastructure
- Typed exception hierarchy (`MultisynthError`, `ConfigurationError`, `MissingCredentialError`, and nine specialised subclasses).
- Lazy credential resolution: explicit `credentials={...}` first, then environment variables.
- Flexible provider alias system (e.g., `"gemini"` → `"google"`, `"flux"` → `"bfl"`, `"runwayml"` → `"runway"`).
- Unified async HTTP client with configurable retry and exponential backoff.
- Polling helper for long-running provider jobs.
- Pricing calculation for text generation (where pricing data is available).
- Pydantic v2 models for all public request and result types.
- `py.typed` marker for PEP 561 type-checking support.
- Full test suite covering all modalities with fake adapters and integration-style configuration tests.
