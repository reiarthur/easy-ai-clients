# Speechmatics Speech Transcription

Snapshot date: 2026-04-24.

## Overview

Speechmatics transcription is available through the public dispatcher `easy_ai_clients.audio.transcribe(..., api="speechmatics")`; the provider adapter exposes `transcribe(audio_input, model="standard", **kwargs)`.

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

~~~python
from easy_ai_clients import audio

bundle = audio.transcribe(
    "audio.m4a",
    api="speechmatics",
)
print(bundle["text"])
~~~

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.