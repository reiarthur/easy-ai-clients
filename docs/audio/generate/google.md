# Google Gemini Speech Synthesis

Snapshot date: 2026-04-24.

## Overview

Google Gemini speech synthesis is implemented in `synthesize/apis/google.py` through `generate(text, model="gemini-2.5-flash-preview-tts", voice="Aoede", language_code="en", **kwargs)`.

- Signup/account: https://aistudio.google.com/
- API key variable: `GOOGLE_API_KEY`
- Speech generation docs: https://ai.google.dev/gemini-api/docs/speech-generation
- Model docs: https://ai.google.dev/gemini-api/docs/models
- Pricing: https://ai.google.dev/gemini-api/docs/pricing

## Defaults And Cost Behavior

- Default model: `gemini-2.5-flash-preview-tts`
- Default voice: `Aoede`
- Default language behavior: `language_code` is used to prefix the prompt and to guide downstream alignment.
- Lowest-cost default: Gemini Flash TTS preview, single-speaker voice config, no multi-speaker controls.

## Public Parameters

- `text`, `model`, `voice`, `language_code`
- `multi_speaker_voice_config`
- `speaker_voice_configs`
- `timeout_seconds`

Google voice names are validated against the wrapper `VOICE_NAMES` set from the official Gemini TTS voice inventory. Unknown kwargs raise `TypeError`.

## Model Coverage

### Model: `gemini-2.5-flash-preview-tts`

Inherits the shared Google parameter surface.

- Default model and lowest-cost wrapper path.
- Supports single-speaker and multi-speaker voice config.
- Validated: yes, model smoke and multi-speaker config parameter cluster passed.

### Model: `gemini-2.5-pro-preview-tts`

Inherits the shared Google parameter surface.

- Higher-cost Pro preview path.
- Supports the same public voice controls.
- Validated: yes, model smoke passed.

### Model: `gemini-3.1-flash-tts-preview`

Inherits the shared Google parameter surface.

- Preview Flash TTS model returned by the live model catalog.
- Supports the same public voice controls.
- Validated: yes, model smoke passed.

## Output Notes

Gemini TTS returns inline audio bytes. The wrapper decodes them into `AudioSegment`, uses Deepgram alignment for word timings, and computes cost from `usageMetadata` when available.

## Example

```python
from synthesize.apis import google

result = google.generate(
    "Speaker A: Hello. Speaker B: Hi.",
    speaker_voice_configs=[
        {"speaker": "A", "voice": "Kore"},
        {"speaker": "B", "voice": "Puck"},
    ],
)
```
