# xAI Speech Synthesis

Snapshot date: 2026-04-24.

## Overview

xAI speech synthesis is implemented in `synthesize/apis/xai.py` through `generate(text, model="text-to-speech", voice="eve", language_code="en", **kwargs)`.

- Signup/account: https://console.x.ai/
- API key variable: `XAI_API_KEY`
- API reference: https://docs.x.ai/docs/api-reference
- Model/pricing docs: https://docs.x.ai/docs/models

## Defaults And Cost Behavior

- Default model: `text-to-speech`
- Default voice: `eve`
- Default language behavior: `language_code` is forwarded as `language`; `None` falls back to English.
- Lowest-cost default: xAI TTS REST surface, MP3 output, no custom sample rate or bit rate.

## Public Parameters

- `text`, `model`, `voice`, `language_code`
- `codec`: `mp3`, `wav`, `pcm`, `mulaw`, `ulaw`, `alaw`
- `sample_rate`: `8000`, `16000`, `22050`, `24000`, `44100`, `48000`
- `bit_rate`: valid only with `codec="mp3"`
- `text_normalization`
- `timeout_seconds`

The wrapper accepts the standardized `model` parameter but xAI exposes a single TTS REST surface in this implementation. Unsupported model values are rejected.

## Model Coverage

### Model: `text-to-speech`

Inherits the full xAI parameter surface.

- Supported voices: `ara`, `eve`, `leo`, `rex`, `sal`
- Supported language values are the wrapper `LANGUAGES` set, including `auto` and common BCP-47 base language codes.
- Validated: yes, model smoke and WAV + sample rate + text normalization parameter cluster passed.

## Output Notes

Compressed output is decoded directly. PCM, mu-law, and A-law are wrapped into WAV internally before alignment and final output construction.

## Example

```python
from synthesize.apis import xai

result = xai.generate(
    "Hello from xAI.",
    voice="eve",
    codec="wav",
    sample_rate=24000,
)
```
