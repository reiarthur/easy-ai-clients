# fal.ai Speech Transcription

Snapshot date: 2026-04-24.

## Overview

fal.ai transcription is available through the public dispatcher `easy_ai_clients.audio.transcribe(..., api="falai")`; the provider adapter exposes `transcribe(audio_input, model="fal-ai/elevenlabs/speech-to-text/scribe-v2", **kwargs)`.

- Signup/account: https://fal.ai/
- API key variable: `FAL_KEY`
- Endpoint docs: https://fal.ai/models/fal-ai/elevenlabs/speech-to-text/api
- Pricing API: https://api.fal.ai/v1/models/pricing

## Defaults And Cost Behavior

- Default model: `fal-ai/elevenlabs/speech-to-text/scribe-v2`
- Lowest-cost behavior: small normalized audio data URL submitted to the queue endpoint with default Scribe settings.

## Public Parameters

- `audio_input`, `model`
- `language_code`
- `tag_audio_events`
- `diarize`
- `keyterms`
- `num_speakers`
- `language_mkd`
- `timeout_seconds`

## Model Coverage

### Model: `fal-ai/elevenlabs/speech-to-text`

Inherits the shared fal.ai parameter surface.

- Provider label: Scribe v1.
- Validated: yes, model smoke passed.

### Model: `fal-ai/elevenlabs/speech-to-text/scribe-v2`

Inherits the shared fal.ai parameter surface.

- Provider label: Scribe v2.
- Validated: yes, model smoke and diarize + audio events + keyterms cluster passed.

## Example

~~~python
from easy_ai_clients import audio

bundle = audio.transcribe(
    "audio.m4a",
    api="falai",
)
print(bundle["text"])
~~~

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.