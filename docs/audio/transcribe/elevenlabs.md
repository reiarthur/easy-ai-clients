# ElevenLabs Speech Transcription

Snapshot date: 2026-05-15.

## Overview

Use ElevenLabs through `easy_ai_clients.audio.transcribe(..., api="elevenlabs")`.
The adapter exposes `transcribe(audio_input, model="scribe_v2", **kwargs)`.

- Provider homepage: https://elevenlabs.io/
- API key: `ELEVENLABS_API_KEY`
- Speech-to-text API: https://elevenlabs.io/docs/api-reference/speech-to-text/convert
- Speech-to-text overview: https://elevenlabs.io/docs/capabilities/speech-to-text
- Pricing: https://elevenlabs.io/pricing/api

## Defaults

- Default model: `scribe_v2`
- Supported models: `scribe_v1`, `scribe_v2`
- Language behavior with no concrete language: `language_code` is omitted. ElevenLabs predicts the language and returns provider language metadata such as `por`.
- Default request shape: normalized PCM upload, word timestamps, diarization enabled, audio event tagging enabled.
- Library audio preparation default: normalized WAV. Prepared encoded uploads use ElevenLabs `file_format="other"` instead of the PCM fast-path marker.

## Accepted Kwargs

| Parameter | Native name | Type/shape | Default | Allowed values/range | Notes | Affects cost |
| --- | --- | --- | --- | --- | --- | --- |
| `language_code` | `language_code` | string | omitted | ElevenLabs language code | Only supported by `scribe_v2`; omit for auto language prediction. | No |
| `diarize` | `diarize` | bool | `True` | bool | Speaker diarization. | No documented surcharge |
| `num_speakers` | `num_speakers` | int | omitted | provider-native | Optional speaker count hint. | No |
| `diarization_threshold` | `diarization_threshold` | float | omitted | `0.1` to `0.4` | Requires `diarize=True` and omitted `num_speakers`. | No |
| `timestamps_granularity` | `timestamps_granularity` | string | `"word"` | `word`, `character`, `none` | `word` keeps the richest normalized bundle. | No |
| `tag_audio_events` | `tag_audio_events` | bool | `True` | bool | Captures non-speech audio events. | No |
| `entity_detection` | `entity_detection` | bool/list | omitted | provider-native | Official table lists entity detection add-on pricing. | Yes |
| `entity_redaction` | `entity_redaction` | bool/list | omitted | provider-native | Sent only when requested. No separate surcharge is applied by this library. | No documented surcharge |
| `entity_redaction_mode` | `entity_redaction_mode` | string | omitted | `redacted`, `entity_type`, `enumerated_entity_type` | Requires provider-side support. | No documented surcharge |
| `keyterms` | `keyterms` | list[str] | omitted | provider-native | More than 100 keyterms uses the provider minimum billing duration. | Yes |
| `no_verbatim` | `no_verbatim` | bool | `False` | bool | Only supported by `scribe_v2`. | No |
| `detect_speaker_roles` | `detect_speaker_roles` | bool | `False` | bool | No surcharge is applied unless officially documented. | No documented surcharge |
| `enable_logging` | `enable_logging` | bool | `True` | bool | Sent as query parameter. | No |
| `language_mkd` | n/a | string or `False` | `"en"` | supported Markdown languages | Controls optional `mkd`. | No |
| `timeout_seconds` | n/a | float | `300` | positive seconds | Request timeout. | No |

Unknown kwargs raise `TypeError`.

## Model Notes

### `scribe_v1`

Validated with `language_code` omitted. It does not support `language_code` or `no_verbatim` through this adapter.

### `scribe_v2`

Default model. Supports `language_code`, keyterms, entity options, diarization controls, and `no_verbatim`.

## Cost Behavior

The `/v1/speech-to-text` response does not return per-call cost. The library computes a deterministic estimate from the official pricing table:

- `scribe_v1` and `scribe_v2`: US$0.22/hour.
- `entity_detection`: US$0.070/hour when requested.
- `keyterms`: US$0.050/hour when requested.

No guessed surcharge is applied for redaction, speaker roles, or diarization. Returned metadata uses `cost_source="official_pricing_table"` and `cost_is_estimated=True`.

## Prepared Audio and Upload Formats

```python
from easy_ai_clients.audio import prepare_transcription_audio, transcribe

prepared = prepare_transcription_audio("audio.mp3")
bundle = transcribe(prepared, api="elevenlabs", model="scribe_v2")
```

The ElevenLabs `file_format="pcm_s16le_16"` marker is only used for the default
normalized WAV/PCM path. If you prepare MP3, Ogg, FLAC, or another encoded
container, the adapter sends `file_format="other"` so the request matches the
actual upload. `language_code` remains omitted unless you pass it explicitly.

## Examples

```python
from easy_ai_clients import audio

bundle = audio.transcribe("audio.mp3", api="elevenlabs")
```

```python
bundle = audio.transcribe(
    "audio.mp3",
    api="elevenlabs",
    model="scribe_v1",
)
```
