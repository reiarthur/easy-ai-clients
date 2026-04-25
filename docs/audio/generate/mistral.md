# Mistral Voxtral Speech Synthesis

Snapshot date: 2026-04-24.

## Overview

Mistral speech synthesis is implemented in `synthesize/apis/mistral.py` through `generate(text, model="voxtral-mini-tts-2603", voice="default", language_code="en", **kwargs)`.

- Signup/account: https://console.mistral.ai/
- API key variable: `MISTRAL_API_KEY`
- Speech endpoint docs: https://docs.mistral.ai/api/endpoint/audio/speech
- Model card/catalog: https://docs.mistral.ai/models/model-cards/voxtral-tts-26-03
- Pricing: https://mistral.ai/pricing

## Defaults And Cost Behavior

- Default model: `voxtral-mini-tts-2603`
- Default voice: `default`
- Default language behavior: `language_code` is used for account voice selection and Deepgram alignment.
- `voice="default"` is not a provider voice id. It means the wrapper discovers the first saved Mistral account voice compatible with the requested language. If reference audio is supplied, reference audio is used instead.
- Lowest-cost default: Voxtral Mini TTS, saved account voice, `mp3`, no streaming.

## Public Parameters

- `text`, `model`, `voice`, `language_code`
- `reference_audio`, `reference_audio_path`, `reference_audio_base64`, `reference_audio_url`
- `response_format`: `pcm`, `wav`, `mp3`, `flac`, `opus`
- `stream`: rejected when `True` because the repository returns `AudioSegment`
- `timeout_seconds`

Unknown kwargs raise `TypeError`; invalid values raise `ValueError`.

## Voice Coverage

Mistral voices are account-dependent saved voice resources. The wrapper resolves `voice="default"` through the official voices endpoint and sends explicit values as `voice_id`. Same-request zero-shot cloning is available through the `reference_audio*` kwargs.

## Model Coverage

### Model: `voxtral-mini-tts-2603`

Inherits the shared Mistral parameter surface.

- Default model.
- Supports saved voice id or same-request `ref_audio`.
- Validated: yes, model smoke and reference-audio + FLAC parameter cluster passed.

### Model: `voxtral-mini-tts-latest`

Inherits the shared Mistral parameter surface.

- Alias/latest model path.
- Supports saved voice id or same-request `ref_audio`.
- Validated: yes, model smoke passed.

## Output Notes

Mistral does not provide native word timestamps in the validated endpoint path. The wrapper uses Deepgram alignment and includes the alignment cost in `cost_usd`.

## Example

```python
from synthesize.apis import mistral

result = mistral.generate(
    "Hello from Mistral.",
    model="voxtral-mini-tts-2603",
    voice="default",
)
```

## Restrictions And Blockers

If the account has no saved voices and no reference audio is provided, the wrapper raises a clear `ValueError` because Mistral requires either a voice id or reference audio.
