# Deepgram Speech Transcription

Snapshot date: 2026-05-11.

## Overview

Use Deepgram through `easy_ai_clients.audio.transcribe(..., api="deepgram")`.
The adapter exposes `transcribe(audio_input, model="nova-2", **kwargs)`.

- Provider homepage: https://deepgram.com/
- Console: https://console.deepgram.com/
- API key: `DEEPGRAM_API_KEY`
- Optional cost lookup project: `DEEPGRAM_PROJECT_ID`
- Listen API: https://developers.deepgram.com/reference/speech-to-text-api/listen
- Models and languages: https://developers.deepgram.com/docs/models-languages-overview/
- Usage lookup: https://developers.deepgram.com/docs/using-logs-usage
- Pricing: https://deepgram.com/pricing

## Defaults

- Default model: `nova-2`
- Language behavior with no concrete language: the adapter omits `language` and sends `detect_language=true`.
- Default request shape: `smart_format=true`, `utterances=true`, `diarize=true`, `punctuate=true`, plus normalized WAV chunks.
- Fallback behavior: no fallback model is used by default. Pass `fallback_model="..."` explicitly if you want a second model attempted after the requested model fails. Result metadata records `requested_model`, `actual_model`, and `fallback_model`.

## Supported Models

`nova-3`, `nova-3-general`, `nova-3-medical`, `nova-2`, `nova-2-general`, `nova-2-meeting`, `nova-2-phonecall`, `nova-2-voicemail`, `nova-2-finance`, `nova-2-conversationalai`, `nova-2-video`, `nova-2-medical`, `nova-2-drivethru`, `nova-2-automotive`, `nova-2-atc`, `nova`, `nova-general`, `nova-phonecall`, `enhanced`, `enhanced-general`, `enhanced-meeting`, `enhanced-phonecall`, `enhanced-finance`, `base-meeting`, `base-phonecall`, `base-voicemail`, `base-finance`, `base-conversationalai`, `base-video`, `whisper`, `whisper-small`, `whisper-medium`, `whisper-large`.

Removed from the public surface: `base`, `base-general`, `whisper-tiny`, and `whisper-base`.

## Accepted Kwargs

| Parameter | Native name | Type/shape | Default | Allowed values/range | Notes | Affects cost |
| --- | --- | --- | --- | --- | --- | --- |
| `language` | `language` | string | omitted | Deepgram language code | If omitted, `detect_language=true` is sent. | No |
| `detect_language` | `detect_language` | bool | `true` when `language` omitted | bool | May be overridden through kwargs. | No |
| `fallback_model` | n/a | string | `None` | supported Deepgram model | Explicit fallback only; no hidden fallback is used. | Yes, if used |
| `concurrency` | n/a | int | Nova cap | positive int | Capped by model family and chunk count. | No |
| `paragraphs` | `paragraphs` | bool | `True` | bool | Enables paragraph metadata. | No |
| `filler_words` | `filler_words` | bool | `True` | bool | Preserves filler words. | No |
| `numerals` | `numerals` | bool | `True` | bool | Formats numerals. | No |
| `measurements` | `measurements` | bool | `True` | bool | Formats measurements. | No |
| `detect_entities` | `detect_entities` | bool or `None` | English non-Whisper only | bool | Rejected for Whisper models. | No documented surcharge |
| `smart_format` | `smart_format` | bool | `True` | bool | Forwarded to Listen query. | No |
| `utterances` | `utterances` | bool | `True` | bool | Required for strong bundle segmentation. | No |
| `diarize` | `diarize` | bool | `True` | bool | Speaker diarization. | Yes for Nova-3 table estimate |
| `punctuate` | `punctuate` | bool | `True` | bool | Punctuation. | No |
| `callback` | `callback` | string | omitted | URL | Forwarded. | No |
| `callback_method` | `callback_method` | string | omitted | `POST`, `PUT` | Forwarded. | No |
| `extra` | `extra` | mapping/string | omitted | provider-native | Forwarded. | No |
| `sentiment` | `sentiment` | bool | omitted | bool | Forwarded. | No documented surcharge |
| `summarize` | `summarize` | bool/string | omitted | provider-native | Forwarded. | No documented surcharge |
| `tag` | `tag` | string/list | omitted | provider-native | Forwarded. | No |
| `topics`, `custom_topic`, `custom_topic_mode` | same | bool/string/list | omitted | `custom_topic_mode`: `extended`, `strict` | Forwarded. | No documented surcharge |
| `intents`, `custom_intent`, `custom_intent_mode` | same | bool/string/list | omitted | `custom_intent_mode`: `extended`, `strict` | Forwarded. | No documented surcharge |
| `dictation`, `encoding`, `keyterm`, `keywords`, `multichannel`, `profanity_filter`, `redact`, `replace`, `search`, `version`, `mip_opt_out`, `utt_split` | same | provider-native | omitted | Deepgram Listen values | Forwarded after validation where applicable. | No documented surcharge |
| `language_mkd` | n/a | string or `False` | `"en"` | `en`, `zh`, `hi`, `es`, `fr`, `ar`, `bn`, `pt`, `ru`, `ur`, `False` | Markdown language for `mkd`. | No |

Unknown kwargs raise `TypeError`.

## Model Notes

- `nova-3` and `nova-3-general`: multilingual Nova-3 estimate uses the public multilingual prerecorded rate.
- `nova-3-medical`: public docs list it as a medical model; the cost estimate uses the monolingual Nova-3 prerecorded rate.
- `nova-2*`, `nova*`, `enhanced*`, `base-*`, and `whisper*`: exact cost requires Deepgram usage lookup because public pricing is not separated enough for deterministic local pricing.
- Whisper models reject `detect_entities=True`.

## Cost Behavior

Deepgram transcription responses do not include final cost. The adapter preserves request IDs and tries the Management/Usage request lookup.

Returned cost fields:

- Exact lookup success: `cost_usd=<exact total>`, `cost_source="usage_lookup"`, `cost_is_estimated=False`, `cost_lookup_error=None`.
- Lookup failure for Nova-3 models: deterministic public pricing estimate, `cost_source="official_pricing_table"`, `cost_is_estimated=True`, and `cost_lookup_error` explains the failed lookup.
- Lookup failure for older families: `cost_usd=None`, `cost_source="unavailable"`, `cost_is_estimated=False`, and `cost_lookup_error` explains why.

The lookup needs an API key with `usage:read`. Set `DEEPGRAM_PROJECT_ID` to avoid project discovery, or let the adapter list projects when the key has access.

## Examples

```python
from easy_ai_clients import audio

bundle = audio.transcribe("audio.mp3", api="deepgram")
print(bundle["text"])
```

```python
bundle = audio.transcribe(
    "audio.mp3",
    api="deepgram",
    model="nova-3-general",
)
```

```python
bundle = audio.transcribe("audio.mp3", api="deepgram")
bundle = audio.update_cost("transcribe", bundle, api="deepgram")
```
