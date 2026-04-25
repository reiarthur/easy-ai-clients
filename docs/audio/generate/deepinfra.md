# DeepInfra Speech Synthesis

Snapshot date: 2026-04-24.

## Overview

DeepInfra speech synthesis is implemented in `synthesize/apis/deepinfra.py` through `generate(text, model="hexgrad/Kokoro-82M", voice="af_bella", language_code="en", **kwargs)`.

- Signup/account: https://deepinfra.com/
- API key variable: `DEEPINFRA_API_KEY`
- TTS catalog: https://deepinfra.com/models/text-to-speech
- Live catalog endpoint: https://api.deepinfra.com/models/list
- Schema docs: https://docs.deepinfra.com/api-reference/model-schema
- Pricing: model pages on https://deepinfra.com/

## Defaults And Cost Behavior

- Default model: `hexgrad/Kokoro-82M`
- Default voice: `af_bella`
- Default language behavior: `language_code` is used by downstream alignment and model-specific defaults.
- Lowest-cost default: Kokoro through DeepInfra OpenAI-compatible speech endpoint, MP3 output, default service tier.
- DeepInfra catalogs are dynamic; the wrapper includes the live TTS models validated on the snapshot date.

## Public Parameters

- `text`, `model`, `voice`, `language_code`
- OpenAI-compatible gateway fields: `response_format`, `service_tier`, `speed`
- Gateway extension: `extra_body`
- Model-specific fields accepted as kwargs and merged into `extra_body`: `language`, `instruct`, `voice_id`, `language_id`, `exaggeration`, `cfg`, `temperature`, `seed`, `top_p`, `min_p`, `repetition_penalty`, `top_k`, `preset_voice`, `output_format`, `speaker_rate`, `speaking_rate`, `sample_rate`, `return_timestamps`, `max_tokens`, `speaker_audio`, `speaker_transcript`, `max_audio_length_ms`
- `timeout_seconds`

Unknown kwargs raise `TypeError`.

## Model Coverage

### Model: `hexgrad/Kokoro-82M`

Inherits the shared DeepInfra parameter surface.

- Default voice: `af_bella`
- Validated: yes, model smoke passed.

### Model: `Qwen/Qwen3-TTS`

Inherits the shared DeepInfra parameter surface.

- Default voice: `Vivian`
- Validated: yes, model smoke and service tier + speed + extra body parameter cluster passed.

### Model: `Qwen/Qwen3-TTS-VoiceDesign`

Inherits the shared DeepInfra parameter surface.

- Default voice prompt: `uma voz feminina brasileira serena, acolhedora e natural`
- Validated: yes, model smoke passed.

### Model: `ResembleAI/chatterbox`

Inherits the shared DeepInfra parameter surface.

- Default voice: `default`
- Validated: yes, model smoke passed.

### Model: `ResembleAI/chatterbox-turbo`

Inherits the shared DeepInfra parameter surface.

- Default voice: `default`
- Validated: yes, model smoke passed.

### Model: `ResembleAI/chatterbox-multilingual`

Inherits the shared DeepInfra parameter surface.

- Default voice: `default`
- Model-specific default: `language_id` follows `language_code` and defaults to `en`.
- Validated: yes, model smoke passed.

### Model: `Zyphra/Zonos-v0.1-hybrid`

Inherits the shared DeepInfra parameter surface.

- Default voice: `random`
- Reference-audio controls are model-specific and may require account assets.
- Validated: yes, model smoke passed.

### Model: `Zyphra/Zonos-v0.1-transformer`

Inherits the shared DeepInfra parameter surface.

- Default voice: `random`
- Reference-audio controls are model-specific and may require account assets.
- Validated: yes, model smoke passed.

### Model: `bosonai/HiggsAudioV2.5`

Inherits the shared DeepInfra parameter surface.

- Default voice: `belinda`
- Model-specific output note: the live endpoint returned raw PCM-like bytes for this model, so the wrapper wraps the response into WAV at 24 kHz before alignment.
- Validated: yes, model smoke passed.

### Model: `canopylabs/orpheus-3b-0.1-ft`

Inherits the shared DeepInfra parameter surface.

- Default voice: `tara`
- Validated: yes, model smoke passed.

### Model: `inworld-ai/inworld-tts-1.5-max`

Inherits the shared DeepInfra parameter surface.

- Default voice: `Ashley`
- Validated: yes, model smoke passed.

### Model: `inworld-ai/inworld-tts-1.5-mini`

Inherits the shared DeepInfra parameter surface.

- Default voice: `Ashley`
- Validated: yes, model smoke passed.

### Model: `sesame/csm-1b`

Inherits the shared DeepInfra parameter surface.

- Default voice: `none`
- Speaker-audio cloning controls are model-specific and may require reference audio for best quality.
- Validated: yes, model smoke passed.

## Output Notes

All DeepInfra synthesis paths use Deepgram alignment for public word timings. Dynamic model schemas should be rechecked before relying on advanced `extra_body` fields in production.

## Example

```python
from synthesize.apis import deepinfra

result = deepinfra.generate(
    "Hello from DeepInfra.",
    model="Qwen/Qwen3-TTS",
    voice="Vivian",
    language="Auto",
)
```
