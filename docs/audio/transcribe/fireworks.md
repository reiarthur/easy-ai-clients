# Fireworks AI Speech Transcription

Snapshot date: 2026-04-24.

## Overview

Fireworks transcription is available through the public dispatcher `easy_ai_clients.audio.transcribe(..., api="fireworks")`; the provider adapter exposes `transcribe(audio_input, model="whisper-v3-turbo", **kwargs)`.

- Signup/account: https://fireworks.ai/
- API key variable: `FIREWORKS_API_KEY`
- Audio transcription docs: https://docs.fireworks.ai/api-reference/audio-transcriptions
- Pricing: https://fireworks.ai/pricing

## Defaults And Cost Behavior

- Default model: `whisper-v3-turbo`
- Lowest-cost behavior: turbo endpoint, `verbose_json`, word timestamps, diarization enabled.

## Public Parameters

- `audio_input`, `model`
- `vad_model`
- `alignment_model`
- `language`
- `prompt`
- `temperature`
- `response_format`: must be `verbose_json`
- `timestamp_granularities`: must include `word`
- `diarize`
- `min_speakers`, `max_speakers`
- `preprocessing`
- `language_mkd`, `timeout_seconds`

## Model Coverage

### Model: `whisper-v3`

Inherits the shared Fireworks parameter surface.

- Endpoint: production audio transcription endpoint.
- Validated: yes, model smoke passed.

### Model: `whisper-v3-turbo`

Inherits the shared Fireworks parameter surface.

- Default model and lowest-cost wrapper path.
- Validated: yes, model smoke and VAD + alignment + preprocessing + speaker hints cluster passed.

## Example

~~~python
from easy_ai_clients import audio

bundle = audio.transcribe(
    "audio.m4a",
    api="fireworks",
)
print(bundle["text"])
~~~

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.