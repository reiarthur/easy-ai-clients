# Fireworks AI Speech Transcription

Snapshot date: 2026-05-15.

## Overview

Use Fireworks AI through `easy_ai_clients.audio.transcribe(..., api="fireworks")`.
The adapter exposes `transcribe(audio_input, model="whisper-v3-turbo", **kwargs)`.

- Provider homepage: https://fireworks.ai/
- API key: `FIREWORKS_API_KEY`
- Audio transcription API: https://docs.fireworks.ai/api-reference/audio-transcriptions
- Whisper v3 model page: https://fireworks.ai/models/fireworks/whisper-v3
- Whisper v3 Turbo model page: https://fireworks.ai/models/fireworks/whisper-v3-turbo
- Pricing: https://fireworks.ai/pricing

## Defaults

- Default model: `whisper-v3-turbo`
- Supported models: `whisper-v3`, `whisper-v3-turbo`
- Language behavior with no concrete language: `language` is omitted and Fireworks detects the language.
- Default request shape: `verbose_json`, word and segment timestamps, diarization enabled.
- Library audio preparation default: normalized WAV. This is separate from Fireworks' provider-native `preprocessing` parameter.

## Accepted Kwargs

| Parameter | Native name | Type/shape | Default | Allowed values/range | Notes | Affects cost |
| --- | --- | --- | --- | --- | --- | --- |
| `language` | `language` | string | omitted | provider language code | Omit for auto detection. | No |
| `prompt` | `prompt` | string | omitted | provider-native | Optional prompt/context. | No |
| `temperature` | `temperature` | float | omitted | `>= 0.0` | Forwarded. | No |
| `response_format` | `response_format` | string | `verbose_json` | `verbose_json` required | Other formats are rejected to preserve normalized words and segments. | No |
| `timestamp_granularities` | `timestamp_granularities` | list/string | `["word", "segment"]` | `word`, `segment`; must include `word` | Sent as repeated form fields. | No |
| `diarize` | `diarize` | bool | `True` | bool | Speaker diarization. No local surcharge multiplier is applied. | No documented surcharge |
| `min_speakers`, `max_speakers` | same | int | omitted | provider-native | Speaker count hints. | No |
| `vad_model` | `vad_model` | string | omitted | `silero`, `whisperx-pyannet` | Optional VAD model. | No documented surcharge |
| `alignment_model` | `alignment_model` | string | omitted | `mms_fa`, `tdnn_ffn` | Optional alignment model. | No documented surcharge |
| `preprocessing` | `preprocessing` | string | omitted | `none`, `dynamic`, `soft_dynamic`, `bass_dynamic` | Optional preprocessing. | No documented surcharge |
| `language_mkd` | n/a | string or `False` | `"en"` | supported Markdown languages | Controls optional `mkd`. | No |
| `timeout_seconds` | n/a | float | `300` | positive seconds | Request timeout. | No |

Unknown kwargs raise `TypeError`.

## Model Notes

### `whisper-v3`

Production Whisper v3 endpoint. Official model page lists US$0.0015 per audio minute, billed per second.

### `whisper-v3-turbo`

Default model. Official model page lists US$0.0009 per audio minute, billed per second.

## Cost Behavior

The transcription response does not return final cost or usage. The adapter calculates from the official per-minute model prices and returns `cost_source="official_pricing_table"` and `cost_is_estimated=True`.

No undocumented diarization multiplier is applied.

## Prepared Audio and Upload Formats

```python
from easy_ai_clients.audio import prepare_transcription_audio, transcribe

prepared = prepare_transcription_audio("audio.mp3")
bundle = transcribe(
    prepared,
    api="fireworks",
    model="whisper-v3-turbo",
    preprocessing="none",
)
```

Fireworks documents common formats such as MP3, FLAC, and WAV, and states that
it resamples/downmixes/reformats audio internally to 16 kHz mono PCM16. The
library's `prepare_transcription_audio(...)` controls local decode/export; the
provider-native `preprocessing` kwarg controls Fireworks' own preprocessing
mode and is forwarded unchanged.

## Examples

```python
from easy_ai_clients import audio

bundle = audio.transcribe("audio.mp3", api="fireworks")
```

```python
bundle = audio.transcribe(
    "audio.mp3",
    api="fireworks",
    model="whisper-v3",
)
```
