# ElevenLabs Speech Transcription

Snapshot date: 2026-04-24.

## Overview

ElevenLabs transcription is implemented in `transcribe/apis/elevenlabs.py` through `transcribe(audio_input, model="scribe_v2", **kwargs)`.

- Signup/account: https://elevenlabs.io/app/sign-up
- API key variable: `ELEVENLABS_API_KEY`
- STT endpoint docs: https://elevenlabs.io/docs/api-reference/speech-to-text/convert
- STT overview: https://elevenlabs.io/docs/capabilities/speech-to-text
- Pricing: https://elevenlabs.io/pricing/api

## Defaults And Cost Behavior

- Default model: `scribe_v2`
- Lowest-cost behavior: single normalized PCM upload, word timestamps, diarization enabled, audio event tagging enabled.
- Extra-cost features such as large keyterm sets, entity extraction, and redaction are opt-in kwargs.

## Public Parameters

- `audio_input`, `model`
- `language_code` (only `scribe_v2`)
- `diarize`, `num_speakers`, `diarization_threshold`
- `timestamps_granularity`: `word`, `character`, `none`
- `tag_audio_events`
- `entity_detection`, `entity_redaction`, `entity_redaction_mode`
- `keyterms`
- `no_verbatim` (only `scribe_v2`)
- `detect_speaker_roles`
- `enable_logging`
- `language_mkd`, `timeout_seconds`

## Model Coverage

### Model: `scribe_v1`

Inherits the shared ElevenLabs transcription surface except `language_code` and `no_verbatim`.

- Input format: normalized PCM uploaded as multipart form data.
- Validated: yes, model smoke passed.

### Model: `scribe_v2`

Inherits the full ElevenLabs transcription surface.

- Default model.
- Supports `language_code`, keyterms, entities, redaction, diarization controls, and `no_verbatim`.
- Validated: yes, model smoke and language + diarization + keyterms + entities cluster passed.

## Example

```python
from transcribe.apis import elevenlabs

bundle = elevenlabs.transcribe(
    "audio.m4a",
    model="scribe_v2",
    language_code="pt",
    num_speakers=1,
    keyterms=["Meus"],
)
```
