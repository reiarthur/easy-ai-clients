# OpenAI Speech Synthesis

Snapshot date: 2026-04-24.

## Overview

OpenAI speech synthesis is available through the public dispatcher `easy_ai_clients.audio.generate(..., api="openai")`; the provider adapter exposes `generate(text, model="tts-1", voice="alloy", language_code="en", **kwargs)`.

- Signup/account: https://platform.openai.com/signup
- API key variable: `OPENAI_API_KEY`
- Speech endpoint docs: https://platform.openai.com/docs/api-reference/audio/createSpeech
- Text-to-speech guide: https://platform.openai.com/docs/guides/text-to-speech
- Model catalog: https://platform.openai.com/docs/models
- Pricing: https://platform.openai.com/docs/pricing

## Defaults And Cost Behavior

- Default model: `tts-1`
- Default voice: `alloy`
- Default language behavior: `language_code` defaults to `en` and is used for downstream Deepgram alignment, not forwarded to OpenAI.
- Lowest-cost default: `tts-1`, `alloy`, `mp3`, `speed=1.0`, no instructions.
- Native word timestamps are not returned by the OpenAI speech endpoint in this wrapper path, so the repository uses Deepgram alignment and includes that cost in `cost_usd`.

## Public Parameters

- `text`: required text input.
- `model`: one supported OpenAI speech model.
- `voice`: one supported OpenAI voice.
- `language_code`: non-empty locale used by the internal aligner; `None` falls back to English.
- `response_format`: `mp3`, `opus`, `aac`, `flac`, `wav`, `pcm`.
- `speed`: numeric range `0.25` to `4.0`.
- `instructions`: supported only for `gpt-4o-mini-tts` family models.
- `stream_format`: `audio` only in this wrapper. `sse` is rejected because it does not preserve the repository `AudioSegment` contract.
- `timeout_seconds`: request timeout.

Unknown kwargs raise `TypeError`; invalid values raise `ValueError`.

## Model Coverage

### Model: `tts-1`

Inherits the shared OpenAI parameter surface except `instructions`.

- Default voice if selected without overriding `voice`: `alloy`
- Supported voices: `alloy`, `ash`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, `shimmer`
- Language behavior: language is inferred by the model; `language_code` is used only by alignment.
- Validated: yes, model smoke passed.

### Model: `tts-1-1106`

Inherits the shared OpenAI parameter surface except `instructions`.

- Supported voices: classic voice set.
- Language behavior: same as `tts-1`.
- Validated: yes, model smoke passed.

### Model: `tts-1-hd`

Inherits the shared OpenAI parameter surface except `instructions`.

- Supported voices: classic voice set.
- Cost note: higher-cost HD model than the default.
- Validated: yes, model smoke passed.

### Model: `tts-1-hd-1106`

Inherits the shared OpenAI parameter surface except `instructions`.

- Supported voices: classic voice set.
- Cost note: higher-cost HD model than the default.
- Validated: yes, model smoke passed.

### Model: `gpt-4o-mini-tts`

Inherits the shared OpenAI parameter surface.

- Supported voices: classic voice set plus `ballad`, `verse`, `marin`, `cedar`.
- Supports `instructions`.
- Validated: yes, model smoke and `instructions` + `wav` + `speed` parameter cluster passed.

### Model: `gpt-4o-mini-tts-2025-03-20`

Inherits the shared OpenAI parameter surface.

- Supported voices: omni voice set.
- Supports `instructions`.
- Validated: yes, model smoke passed.

### Model: `gpt-4o-mini-tts-2025-12-15`

Inherits the shared OpenAI parameter surface.

- Supported voices: omni voice set.
- Supports `instructions`.
- Validated: yes, model smoke passed.

## Output Notes

The wrapper returns the standard synthesis bundle: `cost_usd`, `audio`, and `words`. Output bytes are decoded into `pydub.AudioSegment`, and word timings are recovered with Deepgram alignment.

## Example

~~~python
from easy_ai_clients import audio

result = audio.generate(
    "Hello from openai.",
    api="openai",
)
print(result["cost_usd"])
~~~

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.