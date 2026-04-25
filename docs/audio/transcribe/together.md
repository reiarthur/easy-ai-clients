# Together AI Speech Transcription

Snapshot date: 2026-04-24.

## Overview

Together transcription is available through the public dispatcher `easy_ai_clients.audio.transcribe(..., api="together")`; the provider adapter exposes `transcribe(audio_input, model="openai/whisper-large-v3", **kwargs)`.

- Signup/account: https://api.together.ai/
- API key variable: `TOGETHER_API_KEY`
- STT guide: https://docs.together.ai/docs/speech-to-text
- Transcription reference: https://docs.together.ai/reference/audio-transcriptions
- Serverless catalog/pricing: https://docs.together.ai/docs/serverless-models

## Defaults And Cost Behavior

- Default model: `openai/whisper-large-v3`
- Lowest-cost behavior: serverless transcription, `verbose_json`, word and segment timestamps, diarization enabled only where the model supports it.

## Public Parameters

- `audio_input`, `model`
- `language`
- `prompt`
- `response_format`: must be `verbose_json`
- `temperature`
- `timestamp_granularities`: must include `word`
- `diarize`
- `min_speakers`, `max_speakers`
- `language_mkd`, `timeout_seconds`

## Model Coverage

### Model: `openai/whisper-large-v3`

Inherits the shared Together parameter surface.

- Default model.
- Supports diarization in the validated endpoint path.
- Validated: yes, model smoke and temperature + speaker hints cluster passed.

### Model: `nvidia/parakeet-tdt-0.6b-v3`

Inherits the shared Together parameter surface except diarization.

- `diarize=True` is rejected because live endpoint validation showed this model does not support diarization.
- Validated: yes, model smoke passed with diarization disabled.

### Model: `deepgram/flux`

Inherits the shared Together parameter surface.

- Validation status: blocked. The live endpoint returned `model_not_available` and required a dedicated endpoint.

### Model: `deepgram/nova-3-en`

Inherits the shared Together parameter surface.

- Validation status: blocked. The live endpoint required a dedicated endpoint.

### Model: `deepgram/nova-3-multi`

Inherits the shared Together parameter surface.

- Validation status: blocked. The live endpoint required a dedicated endpoint.

## Example

~~~python
from easy_ai_clients import audio

bundle = audio.transcribe(
    "audio.m4a",
    api="together",
)
print(bundle["text"])
~~~

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.