# Rev AI Speech Transcription

Snapshot date: 2026-04-24.

## Overview

Rev AI transcription is available through the public dispatcher `easy_ai_clients.audio.transcribe(..., api="revai")`; the provider adapter exposes `transcribe(audio_input, model="machine", **kwargs)`.

- Signup/account: https://www.rev.ai/
- API key variable: `REVAI_API_KEY`
- Async transcription reference: https://docs.rev.ai/api/asynchronous/reference
- Transcriber options: https://docs.rev.ai/api/asynchronous/transcribers
- Pricing: https://www.rev.ai/pricing

## Defaults And Cost Behavior

- Default model: `machine`
- Lowest-cost implemented model: `low_cost`, but it is English-only and not used as the default because the repository validates multilingual behavior through `machine`.
- Async jobs are submitted and polled until completion.

## Public Parameters

- `audio_input`, `model`
- `language`
- `skip_diarization`
- `skip_punctuation`
- `skip_postprocessing`
- `remove_disfluencies`
- `filter_profanity`
- `speaker_channel_count`
- `speakers_count`
- `diarization_type`: `standard`, `premium`
- `custom_vocabulary_id`
- `delete_after_seconds`
- `metadata`
- `notification_config`
- `language_mkd`, `timeout_seconds`

## Model Coverage

### Model: `machine`

Inherits the shared Rev AI parameter surface.

- Default model.
- Supports English and foreign-language jobs through Rev AI's async API.
- Validated: yes, model smoke and async job options cluster passed.

### Model: `low_cost`

Inherits the shared Rev AI parameter surface with an English-only language restriction.

- Lowest-cost Rev AI transcriber.
- Non-English `language` values are rejected before submission.
- Validated: yes, English model smoke passed.

### Model: `fusion`

Inherits the shared Rev AI parameter surface with an English-only language restriction in this wrapper.

- Whisper Fusion transcriber path.
- Validated: yes, English model smoke passed.

### Model: `human`

Not implemented.

- Reason: different turnaround, cost, and asynchronous product contract; not compatible with this repository's low-cost live validation contract.

## Example

~~~python
from easy_ai_clients import audio

bundle = audio.transcribe(
    "audio.m4a",
    api="revai",
)
print(bundle["text"])
~~~

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.