# Fireworks AI Speech Transcription

Snapshot date: 2026-04-24.

## Overview

Fireworks transcription is implemented in `transcribe/apis/fireworks.py` through `transcribe(audio_input, model="whisper-v3-turbo", **kwargs)`.

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

```python
from transcribe.apis import fireworks

bundle = fireworks.transcribe(
    "audio.m4a",
    language="pt",
    vad_model="silero",
    alignment_model="mms_fa",
)
```
