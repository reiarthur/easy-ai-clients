# Together AI Speech Transcription

Snapshot date: 2026-05-15.

## Overview

Use Together AI through `easy_ai_clients.audio.transcribe(..., api="together")`.
The adapter exposes `transcribe(audio_input, model="openai/whisper-large-v3", **kwargs)`.

- Provider homepage: https://www.together.ai/
- API: https://api.together.ai/
- API key: `TOGETHER_API_KEY`
- Audio transcription reference: https://docs.together.ai/reference/audio-transcriptions
- Serverless models: https://docs.together.ai/docs/serverless/models
- Billing and usage: https://docs.together.ai/docs/billing-usage-limits

## Defaults

- Default model: `openai/whisper-large-v3`
- Supported models: `openai/whisper-large-v3`, `nvidia/parakeet-tdt-0.6b-v3`
- Language behavior with no concrete language: the adapter sends `language="auto"`.
- Default request shape: `verbose_json`, word and segment timestamps. Diarization defaults to the model capability.
- Library audio preparation default: normalized WAV. Prepared payloads can use other supported upload formats when you opt in.

Removed from the public surface: `deepgram/flux`, `deepgram/nova-3-en`, and `deepgram/nova-3-multi`, because the serverless endpoint returned `model_not_available` and required dedicated endpoints.

## Accepted Kwargs

| Parameter | Native name | Type/shape | Default | Allowed values/range | Notes | Affects cost |
| --- | --- | --- | --- | --- | --- | --- |
| `language` | `language` | string | `"auto"` | provider language value | Keep omitted for auto detection. | No |
| `prompt` | `prompt` | string | omitted | provider-native | Optional prompt/context. | No |
| `response_format` | `response_format` | string | `verbose_json` | `json`, `verbose_json`; `verbose_json` required | Other formats are rejected to preserve the bundle. | No |
| `temperature` | `temperature` | float | omitted | `0.0` to `1.0` | Forwarded. | No |
| `timestamp_granularities` | `timestamp_granularities` | list/string | `["word", "segment"]` | `word`, `segment`; must include `word` | Sent as repeated form fields. | No |
| `diarize` | `diarize` | bool | model capability | bool | Rejected for Parakeet on the validated endpoint. | No documented surcharge |
| `min_speakers`, `max_speakers` | same | int | omitted | provider-native | Speaker count hints when diarization is supported. | No |
| `language_mkd` | n/a | string or `False` | `"en"` | supported Markdown languages | Controls optional `mkd`. | No |
| `timeout_seconds` | n/a | float | `300` | positive seconds | Request timeout. | No |

Unknown kwargs raise `TypeError`.

## Model Notes

### `openai/whisper-large-v3`

Default model. Supports diarization on the validated endpoint. Public serverless pricing lists US$0.0015 per audio minute.

### `nvidia/parakeet-tdt-0.6b-v3`

Passed transcription accuracy validation, but returned unreliable language metadata in the audit. The validated endpoint does not support diarization for this model; `diarize=True` is rejected. Public serverless pricing lists US$0.0015 per audio minute.

## Cost Behavior

Together transcription responses do not return final cost. The adapter first tries the authenticated `/v1/models` catalog for `pricing.transcribe.price_per_minute`:

- Catalog success: `cost_source="pricing_api"`.
- Catalog failure: fallback to the documented per-minute table with `cost_source="official_pricing_table"` and `cost_lookup_error` explaining the lookup issue.

Both paths are deterministic estimates, so `cost_is_estimated=True`.

## Prepared Audio and Upload Formats

```python
from easy_ai_clients.audio import prepare_transcription_audio, transcribe

prepared = prepare_transcription_audio("audio.mp3")
bundle = transcribe(prepared, api="together", model="openai/whisper-large-v3")
```

Together documents uploads or public URLs for `.wav`, `.mp3`, `.m4a`, `.webm`,
`.flac`, `.ogg`, `.opus`, and `.aac`. The library default remains normalized
WAV, while `prepare_transcription_audio(..., upload_format="mp3" | "flac" |
"ogg")` lets callers validate compressed payloads per model. The
`language="auto"` default and Parakeet diarization behavior are unchanged.

## Examples

```python
from easy_ai_clients import audio

bundle = audio.transcribe("audio.mp3", api="together")
```

```python
bundle = audio.transcribe(
    "audio.mp3",
    api="together",
    model="nvidia/parakeet-tdt-0.6b-v3",
)
```
