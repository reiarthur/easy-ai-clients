# Together AI Speech Synthesis

Snapshot date: 2026-04-24.

## Overview

Together AI speech synthesis is available through the public dispatcher `easy_ai_clients.audio.generate(..., api="together")`; the provider adapter exposes `generate(text, model="hexgrad/Kokoro-82M", voice="af_alloy", language_code="en", **kwargs)`.

- Signup/account: https://api.together.ai/
- API key variable: `TOGETHER_API_KEY`
- TTS guide: https://docs.together.ai/docs/text-to-speech
- Audio speech reference: https://docs.together.ai/reference/audio-speech
- Serverless catalog/pricing: https://docs.together.ai/docs/serverless-models
- Voice discovery endpoint: `https://api.together.xyz/v1/voices`

## Defaults And Cost Behavior

- Default model: `hexgrad/Kokoro-82M`
- Default voice: `af_alloy`
- Default language behavior: `language_code` is forwarded as `language`.
- Lowest-cost default: Kokoro, raw PCM streaming, word alignment enabled.
- If caller changes `model` but leaves the module default voice, the wrapper auto-resolves to the documented default voice for the selected model.

## Public Parameters

- `text`, `model`, `voice`, `language_code`
- `response_format`: `mp3`, `wav`, `raw`, `mulaw`, `opus`, `aac`, `flac`
- `response_encoding`: `pcm_f32le`, `pcm_s16le`, `pcm_mulaw`, `pcm_alaw`
- `sample_rate`
- `bit_rate`
- `stream`
- `alignment`: `word` or `none`
- `segment`
- `timeout_seconds`

## Model Coverage

### Model: `hexgrad/Kokoro-82M`

Inherits the shared Together parameter surface.

- Default voice: `af_alloy`
- Validated: yes, model smoke and non-stream MP3 alignment parameter cluster passed.

### Model: `canopylabs/orpheus-3b-0.1-ft`

Inherits the shared Together parameter surface.

- Default voice: `tara`
- Validated: yes, model smoke passed.

### Model: `cartesia/sonic`

Inherits the shared Together parameter surface.

- Default voice: `laidback woman`
- Validated: yes, model smoke passed.

### Model: `cartesia/sonic-2`

Inherits the shared Together parameter surface.

- Default voice: `laidback woman`
- Validated: yes, model smoke passed.

### Model: `cartesia/sonic-3`

Inherits the shared Together parameter surface.

- Default voice: `laidback woman`
- Validated: yes, model smoke passed.

### Model: `deepgram/aura-2`

Inherits the shared Together parameter surface.

- Default voice: `aura-2-thalia-en`
- Validation status: blocked. The live endpoint returned `model_not_available` and required a dedicated endpoint.

### Model: `rime-labs/rime-mist-v2`

Inherits the shared Together parameter surface.

- Default voice: `astra`
- Validation status: blocked. The live endpoint required a dedicated endpoint.

### Model: `rime-labs/rime-arcana-v2`

Inherits the shared Together parameter surface.

- Default voice: `astra`
- Validation status: blocked. The live endpoint required a dedicated endpoint.

### Model: `rime-labs/rime-arcana-v3`

Inherits the shared Together parameter surface.

- Default voice: `astra`
- Validation status: blocked. The live endpoint required a dedicated endpoint.

### Model: `rime-labs/rime-arcana-v3-turbo`

Inherits the shared Together parameter surface.

- Default voice: `astra`
- Validation status: blocked. The live endpoint required a dedicated endpoint.

### Model: `minimax/speech-2.6-turbo`

Inherits the shared Together parameter surface.

- Default voice: `English_CalmWoman`
- Validation status: blocked. The live endpoint required a dedicated endpoint.

## Output Notes

Streaming mode uses Together word-alignment SSE events. Non-streaming mode uses Deepgram alignment. Raw PCM output is wrapped into WAV internally.

## Example

~~~python
from easy_ai_clients import audio

result = audio.generate(
    "Hello from together.",
    api="together",
)
print(result["cost_usd"])
~~~

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.