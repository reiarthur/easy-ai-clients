# Speechmatics Speech Transcription

Snapshot date: 2026-04-24.

## Overview

Speechmatics transcription is implemented in `transcribe/apis/speechmatics.py` through `transcribe(audio_input, model="standard", **kwargs)`.

- Signup/account: https://portal.speechmatics.com/
- API key variable: `SPEECHMATICS_API_KEY`
- Batch API docs: https://docs.speechmatics.com/api-ref/asr/transcription-jobs/create
- Pricing: https://www.speechmatics.com/pricing

## Defaults And Cost Behavior

- Default model: `standard`
- Lowest-cost behavior: standard operating point, speaker diarization enabled, no optional enrichment unless requested.
- Jobs are submitted and polled until completion.

## Public Parameters

- `audio_input`, `model`
- `language`
- `output_locale`
- `additional_vocab`
- `diarization`
- `channel_diarization_labels`
- `enable_entities`
- `audio_filtering_config`
- `transcript_filtering_config`
- `speaker_diarization_config`
- `speaker_sensitivity`
- `prefer_current_speaker`
- `speaker_identifiers`
- Top-level job configs: `notification_config`, `tracking`, `output_config`, `translation_config`, `language_identification_config`, `summarization_config`, `sentiment_analysis_config`, `topic_detection_config`, `auto_chapters_config`, `audio_events_config`
- `language_mkd`, `timeout_seconds`

## Model Coverage

### Model: `standard`

Inherits the shared Speechmatics parameter surface.

- Default operating point.
- Validated: yes, model smoke and entities + speaker config cluster passed.

### Model: `enhanced`

Inherits the shared Speechmatics parameter surface.

- Enhanced operating point.
- Validated: yes, model smoke passed.

## Example

```python
from transcribe.apis import speechmatics

bundle = speechmatics.transcribe(
    "audio.m4a",
    model="standard",
    language="pt",
    enable_entities=True,
    speaker_sensitivity=0.5,
)
```
