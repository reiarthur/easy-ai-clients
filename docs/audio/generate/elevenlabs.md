# ElevenLabs Speech Synthesis

Snapshot date: 2026-04-24.

## Overview

ElevenLabs speech synthesis is implemented in `synthesize/apis/elevenlabs.py` through `generate(text, model="eleven_flash_v2_5", voice="NndrHq4eUijN4wsQVtzW", language_code="en", **kwargs)`.

- Signup/account: https://elevenlabs.io/app/sign-up
- API key variable: `ELEVENLABS_API_KEY`
- TTS endpoint docs: https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps
- Model catalog API: https://elevenlabs.io/docs/api-reference/models/get-all
- Voice discovery API: https://elevenlabs.io/docs/api-reference/voices/search
- Pricing: https://elevenlabs.io/pricing/api

## Defaults And Cost Behavior

- Default model: `eleven_flash_v2_5`
- Default voice: `NndrHq4eUijN4wsQVtzW`
- Default language behavior: `language_code="en"` is forwarded only to models that support `language_code`.
- Lowest-cost default: Flash v2.5 with normal MP3 output, automatic text normalization, no premium extras.
- Word timing source: native ElevenLabs character alignment from `/with-timestamps`.

## Public Parameters

- `text`, `model`, `voice`, `language_code`
- Voice settings: `stability`, `similarity_boost`, `style`, `use_speaker_boost`, `speed`
- Text controls: `apply_text_normalization`, `apply_language_text_normalization`, `pronunciation_dictionary_locators`
- Determinism/context: `seed`, `previous_text`, `next_text`, `previous_request_ids`, `next_request_ids`
- Voice conversion behavior: `use_pvc_as_ivc`
- Request controls: `enable_logging`, `optimize_streaming_latency`, `output_format`, `timeout_seconds`

Supported `output_format` values are the ElevenLabs documented MP3, PCM, u-law, A-law, and Opus variants implemented in `OUTPUT_FORMATS`.

## Voice Coverage

Voices are account-dependent. The wrapper accepts any voice id supplied through `voice` and validates the resulting provider call. The default voice was validated on the active account.

## Model Coverage

### Model: `eleven_v3`

Inherits the shared ElevenLabs parameter surface.

- Supports `language_code`.
- Supports the default voice when the account allows it.
- Validated: yes, model smoke passed.

### Model: `eleven_multilingual_v2`

Inherits the shared ElevenLabs parameter surface.

- Supports `language_code`.
- Validated: yes, model smoke passed.

### Model: `eleven_multilingual_v1`

Inherits the shared ElevenLabs parameter surface.

- Supports `language_code`.
- Validated: yes, model smoke passed.

### Model: `eleven_flash_v2_5`

Inherits the shared ElevenLabs parameter surface.

- Default model and lowest-cost wrapper path.
- Supports `language_code`.
- Validated: yes, model smoke and `seed` + text normalization + compact MP3 parameter cluster passed.

### Model: `eleven_flash_v2`

Inherits the shared ElevenLabs parameter surface.

- Does not support non-English `language_code` in this wrapper.
- Validated: yes, model smoke passed.

### Model: `eleven_turbo_v2_5`

Inherits the shared ElevenLabs parameter surface.

- Supports `language_code`.
- Validated: yes, model smoke passed.

### Model: `eleven_turbo_v2`

Inherits the shared ElevenLabs parameter surface.

- Does not support non-English `language_code` in this wrapper.
- Validated: yes, model smoke passed.

### Model: `eleven_monolingual_v1`

Inherits the shared ElevenLabs parameter surface.

- English-only behavior; non-English `language_code` is rejected.
- Validated: yes, model smoke passed.

## Output Notes

The wrapper returns the standard synthesis bundle. Raw PCM, u-law, and A-law responses are wrapped into WAV internally so downstream decoding and timing projection stay stable.

## Example

```python
from synthesize.apis import elevenlabs

result = elevenlabs.generate(
    "Hello from ElevenLabs.",
    model="eleven_flash_v2_5",
    voice="NndrHq4eUijN4wsQVtzW",
    output_format="mp3_22050_32",
    seed=1234,
)
```

## Validation Notes

Every implemented ElevenLabs synthesis model passed live validation on 2026-04-24. Evidence is in `tests/artefatos_testes/2026-04-24_audio_api_standardization/`.
