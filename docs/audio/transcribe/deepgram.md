# Deepgram Speech Transcription

Snapshot date: 2026-04-24.

## Overview

Deepgram transcription is available through the public dispatcher `easy_ai_clients.audio.transcribe(..., api="deepgram")`; the provider adapter exposes `transcribe(audio_input, model="nova-2", **kwargs)`.

- Signup/account: https://console.deepgram.com/signup
- API key variable: `DEEPGRAM_API_KEY`
- Optional project variable: `DEEPGRAM_PROJECT_ID`
- Listen API docs: https://developers.deepgram.com/reference/speech-to-text-api/listen
- Model/language docs: https://developers.deepgram.com/docs/models-languages-overview
- Pricing: https://deepgram.com/pricing

## Defaults And Cost Behavior

- Default model: `nova-2`
- Lowest-cost behavior: one normalized WAV upload per chunk, `smart_format`, `utterances`, `diarize`, and `punctuate` enabled to satisfy the repository bundle.
- Exact cost: the wrapper attempts Deepgram Management API request lookup when request ids and project access are available.

## Public Parameters

- `audio_input`: path, bytes, base64/data URL, or `pydub.AudioSegment`.
- `model`: any supported Deepgram prerecorded model alias listed below.
- `fallback_model`: defaults to `whisper-large`.
- `concurrency`
- Listen parameters: `language`, `paragraphs`, `filler_words`, `numerals`, `measurements`, `detect_entities`, `smart_format`, `utterances`, `diarize`, `punctuate`, `detect_language`, `callback`, `callback_method`, `extra`, `sentiment`, `summarize`, `tag`, `topics`, `custom_topic`, `custom_topic_mode`, `intents`, `custom_intent`, `custom_intent_mode`, `dictation`, `encoding`, `keyterm`, `keywords`, `multichannel`, `profanity_filter`, `redact`, `replace`, `search`, `version`, `mip_opt_out`, `utt_split`
- `language_mkd`

Unknown kwargs raise `TypeError`. `detect_entities=True` is rejected for Whisper models because live validation showed the Whisper backend rejects semantic tagging.

## Input And Output

Audio is normalized to 16 kHz mono PCM for upload. The wrapper returns the repository unified transcription bundle with text, words, segments, phrases, speakers, silences, metadata, request ids, and optional Markdown.

## Model Coverage

All models below inherit the shared Deepgram parameter surface unless noted. All were live validated on 2026-04-24.

### Model: `nova-3`

- Family: Nova 3.
- Validated: yes, model smoke and language + keyterm + search + redaction cluster passed.

### Model: `nova-3-general`

- Family: Nova 3.
- Validated: yes.

### Model: `nova-3-medical`

- Family: Nova 3 medical.
- Validated: yes.

### Model: `nova-2`

- Family: Nova 2.
- Default model.
- Validated: yes.

### Model: `nova-2-general`

- Family: Nova 2.
- Validated: yes.

### Model: `nova-2-meeting`

- Family: Nova 2.
- Validated: yes.

### Model: `nova-2-phonecall`

- Family: Nova 2.
- Validated: yes.

### Model: `nova-2-voicemail`

- Family: Nova 2.
- Validated: yes.

### Model: `nova-2-finance`

- Family: Nova 2.
- Validated: yes.

### Model: `nova-2-conversationalai`

- Family: Nova 2.
- Validated: yes.

### Model: `nova-2-video`

- Family: Nova 2.
- Validated: yes.

### Model: `nova-2-medical`

- Family: Nova 2.
- Validated: yes.

### Model: `nova-2-drivethru`

- Family: Nova 2.
- Validated: yes.

### Model: `nova-2-automotive`

- Family: Nova 2.
- Validated: yes.

### Model: `nova-2-atc`

- Family: Nova 2.
- Validated: yes.

### Model: `nova`

- Family: legacy Nova.
- Validated: yes.

### Model: `nova-general`

- Family: legacy Nova.
- Validated: yes.

### Model: `nova-phonecall`

- Family: legacy Nova.
- Validated: yes.

### Model: `enhanced`

- Family: Enhanced.
- Validated: yes.

### Model: `enhanced-general`

- Family: Enhanced.
- Validated: yes.

### Model: `enhanced-meeting`

- Family: Enhanced.
- Validated: yes.

### Model: `enhanced-phonecall`

- Family: Enhanced.
- Validated: yes.

### Model: `enhanced-finance`

- Family: Enhanced.
- Validated: yes.

### Model: `base`

- Family: Base.
- Validated: yes.

### Model: `base-general`

- Family: Base.
- Validated: yes.

### Model: `base-meeting`

- Family: Base.
- Validated: yes.

### Model: `base-phonecall`

- Family: Base.
- Validated: yes.

### Model: `base-voicemail`

- Family: Base.
- Validated: yes.

### Model: `base-finance`

- Family: Base.
- Validated: yes.

### Model: `base-conversationalai`

- Family: Base.
- Validated: yes.

### Model: `base-video`

- Family: Base.
- Validated: yes.

### Model: `whisper`

- Family: Whisper Cloud.
- Restriction: `detect_entities=True` is not supported.
- Validated: yes.

### Model: `whisper-tiny`

- Family: Whisper Cloud.
- Restriction: `detect_entities=True` is not supported.
- Validated: yes.

### Model: `whisper-base`

- Family: Whisper Cloud.
- Restriction: `detect_entities=True` is not supported.
- Validated: yes.

### Model: `whisper-small`

- Family: Whisper Cloud.
- Restriction: `detect_entities=True` is not supported.
- Validated: yes.

### Model: `whisper-medium`

- Family: Whisper Cloud.
- Restriction: `detect_entities=True` is not supported.
- Validated: yes.

### Model: `whisper-large`

- Family: Whisper Cloud.
- Restriction: `detect_entities=True` is not supported.
- Validated: yes.

## Example

~~~python
from easy_ai_clients import audio

bundle = audio.transcribe(
    "audio.m4a",
    api="deepgram",
)
print(bundle["text"])
~~~

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.