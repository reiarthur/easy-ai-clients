# Changelog

All notable changes to **easy-ai-clients** are documented in this file.
The project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.5.0 - 2026-05-11

### Changed

- Standardized the public Fal.ai provider identifier to `falai` for text,
  transcription, and image operations. The old short text identifier is no
  longer supported.
- Updated transcription results to include explicit cost metadata:
  `cost_usd`, `cost_source`, `cost_is_estimated`, and `cost_lookup_error`.
  Unknown transcription cost is now `None` instead of a fake `0.0`.
- Added `audio.update_cost("transcribe", result, api="deepgram")` for
  post-hoc Deepgram Management/Usage cost lookup.
- Corrected transcription pricing behavior for Deepgram, ElevenLabs, Fal.ai,
  Fireworks AI, Speechmatics, and Together AI using current official lookup
  APIs or pricing tables.
- Changed Speechmatics default transcription language behavior to
  `language="auto"` and Together default transcription language behavior to
  `language="auto"`.
- Removed Deepgram's hidden default fallback to `whisper-large`; fallback is
  now explicit via `fallback_model`.
- Reworked transcription provider docs, configuration, usage, error, and
  provider matrix documentation.

### Removed

- Removed public Rev AI transcription support because it did not meet the
  no-concrete-language Portuguese validation contract.
- Removed unsupported transcription models:
  `base`, `base-general`, `whisper-tiny`, and `whisper-base` from Deepgram;
  `deepgram/flux`, `deepgram/nova-3-en`, and `deepgram/nova-3-multi` from
  Together AI.

## 0.4.1 — 2026-04-25

### Changed

- Reworked `README.md` as a PyPI-safe long description with absolute GitHub
  links for repository files and directories.
- Added `docs/usage.md` with public dispatcher examples, normalized response
  structures, media input notes, streaming behavior, and cost update helpers.
- Updated configuration and error documentation to match the current
  dispatcher and provider-adapter behavior.
- Updated provider documentation examples to use the public
  `easy_ai_clients.text`, `easy_ai_clients.audio`, and `easy_ai_clients.image`
  dispatchers instead of private or removed provider import paths.
- Improved package metadata URLs and declared the README content type
  explicitly for PyPI rendering.

## 0.4.0 — 2026-04-25

This is the first fully working release of `easy-ai-clients`. The library was
rewritten from scratch around three operation-aware dispatchers and a private
provider tree. Earlier `0.x` releases on PyPI reserved the project name but
were not functional and have been superseded.

### Added

- `easy_ai_clients.text.generate(input_text, instruction=None, model=None, *, api, **kwargs)`
  unified dispatcher across 14 text/chat providers: `anthropic`, `cohere`,
  `deepinfra`, `deepseek`, Fal.ai, `fireworks`, `google`, `groq`, `huggingface`,
  `mistral`, `openai`, `openrouter`, `together`, `xai`.
- `easy_ai_clients.audio.generate(text, model=None, voice=None, language_code="en", *, api, **kwargs)`
  for speech synthesis with `deepinfra`, `elevenlabs`, `google`, `mistral`,
  `openai`, `together`, `xai`.
- `easy_ai_clients.audio.transcribe(audio_input, model=None, *, api, **kwargs)`
  for speech transcription with `deepgram`, `elevenlabs`, `falai`, `fireworks`,
  Rev AI, `speechmatics`, `together`.
- `easy_ai_clients.image.generate / edit / remix / analyze(...)` dispatchers
  covering `bfl`, `falai`, `fireworks`, `google`, `openai`, `openrouter`,
  `stability`, `together`, `xai` (`anthropic` and `groq` for `analyze`).
- Programmatic discovery helpers: `text.available_apis()`,
  `audio.available_synthesize_apis()`, `audio.available_transcribe_apis()`,
  `image.available_generate_apis()`, `image.available_edit_apis()`,
  `image.available_remix_apis()`, `image.available_analyze_apis()`.
- `text.list_models(api=...)` and `text.update_cost(result, api=...)` for
  providers that support live catalogs and post-hoc cost lookups (currently
  `openai` and `openrouter`).
- `image.update_cost(operation, result, api=...)` for providers that support
  cost refinement after the original call (currently `openrouter`).
- Public package marker (`py.typed`) and an explicit Python `>= 3.11` baseline.
- Documentation under [`docs/`](docs/) for configuration, providers, and
  errors, plus a refreshed `README.md` and `CHANGELOG.md`.

### Changed

- The library no longer auto-loads a `.env` file from the package directory;
  callers are expected to set environment variables explicitly or use
  `python-dotenv` themselves. This matches the behaviour documented in
  [`docs/configuration.md`](docs/configuration.md).
- Internal provider modules are private (the package directories use a leading
  underscore). Only the operation dispatchers and the package-level submodules
  are part of the public API.

### Removed

- Direct imports of provider modules such as
  `easy_ai_clients.text.apis.openai` are no longer supported.
- The `0.3.0` and earlier code paths were removed entirely; nothing from those
  releases is preserved beyond the public package name.
