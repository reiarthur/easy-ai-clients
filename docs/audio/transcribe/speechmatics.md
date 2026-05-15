# Speechmatics Speech Transcription

Snapshot date: 2026-05-15.

## Overview

Use Speechmatics through `easy_ai_clients.audio.transcribe(..., api="speechmatics")`.
The adapter exposes `transcribe(audio_input, model="standard", **kwargs)`.

- Provider homepage: https://www.speechmatics.com/
- Portal: https://portal.speechmatics.com/
- API key: `SPEECHMATICS_API_KEY`
- Documentation: https://docs.speechmatics.com/
- Batch job API: https://docs.speechmatics.com/api-ref/asr/transcription-jobs/create
- Batch input formats: https://docs.speechmatics.com/speech-to-text/batch/input
- Python SDK examples: https://docs.speechmatics.com/sdk/python-sdk
- Pricing: https://www.speechmatics.com/pricing
- Pricing CSV referenced by pricing page: https://assets.ctfassets.net/yze1aysi0225/16iPaLPpkieCFFWh54jfrA/df1761507f16eeb934a14dbc0d315de3/Pricing_April_2025-updated-December.csv

## Defaults

- Default model: `standard`
- Supported models: `standard`, `enhanced`
- Language behavior with no concrete language: the adapter sends `language="auto"`, the official batch language identification mode.
- Default request shape: batch transcription job with speaker diarization enabled and no enrichment add-ons unless requested.
- Library audio preparation default: normalized WAV. This remains the safe default because Speechmatics documents 16-bit 16 kHz mono WAV as the optimal speed format.

## Accepted Kwargs

| Parameter | Native name | Type/shape | Default | Allowed values/range | Notes | Affects cost |
| --- | --- | --- | --- | --- | --- | --- |
| `language` | `language` | string | `"auto"` | Speechmatics language code or `auto` | Keep omitted for auto detection. | No |
| `diarization` | `diarization` | string | `"speaker"` | provider-native | Speaker diarization mode. | No documented surcharge |
| `output_locale` | `output_locale` | string | omitted | provider-native | Transcription config field. | No |
| `additional_vocab` | `additional_vocab` | list/mapping | omitted | provider-native | Transcription config field. | No documented surcharge |
| `channel_diarization_labels` | same | list | omitted | provider-native | Transcription config field. | No |
| `enable_entities` | `enable_entities` | bool | `False` | bool | Entity extraction. | No documented surcharge |
| `audio_filtering_config` | same | mapping | omitted | provider-native | Transcription config field. | No documented surcharge |
| `transcript_filtering_config` | same | mapping | omitted | provider-native | Transcription config field. | No documented surcharge |
| `speaker_diarization_config` | same | mapping | omitted | provider-native | May also be built from speaker kwargs. | No |
| `speaker_sensitivity` | nested | float | omitted | provider-native | Added to `speaker_diarization_config`. | No |
| `prefer_current_speaker` | nested | bool | omitted | bool | Added to `speaker_diarization_config`. | No |
| `speaker_identifiers` | same | list/mapping | omitted | provider-native | Transcription config field. | No |
| `notification_config`, `tracking`, `output_config` | same | mapping | omitted | provider-native | Top-level job configs. | No |
| `translation_config` | same | mapping | omitted | provider-native | Official add-on. | Yes |
| `summarization_config` | same | mapping | omitted | provider-native | Official add-on. | Yes |
| `auto_chapters_config` | same | mapping | omitted | provider-native | Official add-on. | Yes |
| `sentiment_analysis_config` | same | mapping | omitted | provider-native | Official add-on. | Yes |
| `topic_detection_config` | same | mapping | omitted | provider-native | Official add-on. | Yes |
| `language_identification_config` | same | mapping | omitted | provider-native | Optional language ID config. | No documented surcharge |
| `audio_events_config` | same | mapping | omitted | provider-native | Audio events. | No documented surcharge |
| `language_mkd` | n/a | string or `False` | `"en"` | supported Markdown languages | Controls optional `mkd`. | No |
| `timeout_seconds` | n/a | float | `300` | positive seconds | Submit timeout. | No |

Unknown kwargs raise `TypeError`.

## Model Notes

### `standard`

Default operating point. Official batch price: US$0.45/hour.

### `enhanced`

Enhanced batch operating point. Official batch price: US$0.75/hour.

## Cost Behavior

Speechmatics job/transcript responses do not return final per-call cost. The adapter calculates from the official batch pricing table and returns `cost_source="official_pricing_table"` and `cost_is_estimated=True`.

Add-on prices applied when corresponding configs are supplied:

- Translation: US$0.65/hour.
- Summaries: US$0.12/hour.
- Chapters: US$0.40/hour.
- Sentiment: US$0.12/hour.
- Topics: US$0.20/hour.

No undocumented add-ons are charged.

## Prepared Audio and Upload Formats

```python
from easy_ai_clients.audio import prepare_transcription_audio, transcribe

prepared = prepare_transcription_audio("audio.mp3")
bundle = transcribe(prepared, api="speechmatics", model="enhanced")
```

Prepared audio is accepted by the adapter and sent as the uploaded `data_file`.
The global default stays normalized WAV. Speechmatics documents additional batch
file types such as MP3, AAC, Ogg, M4A, MP4, and FLAC, but this release does not
change the adapter default away from WAV. `language="auto"` and
`language_identification_config` behavior are unchanged.

## Examples

```python
from easy_ai_clients import audio

bundle = audio.transcribe("audio.mp3", api="speechmatics")
```

```python
bundle = audio.transcribe(
    "audio.mp3",
    api="speechmatics",
    model="enhanced",
)
```
