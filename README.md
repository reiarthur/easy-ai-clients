# easy-ai-clients

[![PyPI version](https://img.shields.io/pypi/v/easy-ai-clients.svg)](https://pypi.org/project/easy-ai-clients/)
[![Python versions](https://img.shields.io/pypi/pyversions/easy-ai-clients.svg)](https://pypi.org/project/easy-ai-clients/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/reiarthur/easy-ai-clients/blob/main/LICENSE)

`easy-ai-clients` is a Python library that exposes one stable interface for
text, audio, and image AI operations across multiple providers. Each public
operation is selected with an explicit `api=` argument, so application code can
switch providers without importing provider-specific modules.

The package is a library, not a hosted service. It makes outbound provider API
calls only when you call one of the dispatchers.

## Install

```bash
pip install easy-ai-clients
```

Requirements:

- Python `>=3.11`
- Provider credentials for only the providers you call
- `ffmpeg` support through `imageio-ffmpeg` / `pydub` for non-WAV audio inputs

Runtime dependencies are installed by `pip`: `requests`, `httpx`, `Pillow`,
`pydub`, `imageio-ffmpeg`, `python-dotenv`, and `audioop-lts` on Python
`>=3.13`.

## Quickstart

```python
import base64

from dotenv import load_dotenv
from easy_ai_clients import audio, image, text

load_dotenv()

text_result = text.generate(
    "Summarize Don Quixote in two sentences.",
    instruction="Use plain English.",
    api="openai",
)
print(text_result["output_text"], "USD:", text_result["cost_usd"])

speech = audio.generate(
    "Hello from easy-ai-clients.",
    voice="alloy",
    language_code="en",
    api="openai",
)
speech["audio"].export("hello.mp3", format="mp3")

transcript = audio.transcribe("hello.mp3", api="deepgram")
print(transcript["text"])

generated = image.generate("a clean product icon of a paper airplane", api="openai")
with open("paper-airplane.png", "wb") as image_file:
    image_file.write(base64.b64decode(generated["base64"]))

analysis = image.analyze(
    "Describe this image in one sentence.",
    "paper-airplane.png",
    api="openai",
)
print(analysis["output"])
```

## Public API

Import the public dispatchers from the top-level package:

```python
from easy_ai_clients import audio, image, text
```

or from each submodule:

```python
from easy_ai_clients.text import generate as text_generate
from easy_ai_clients.audio import generate as speech_generate
from easy_ai_clients.audio import transcribe
from easy_ai_clients.image import analyze
```

Supported operations:

| Module | Function | Purpose | Providers |
| --- | --- | --- | --- |
| `text` | `generate` | Text-in / text-out generation | `anthropic`, `cohere`, `deepinfra`, `deepseek`, `falai`, `fireworks`, `google`, `groq`, `huggingface`, `mistral`, `openai`, `openrouter`, `together`, `xai` |
| `text` | `list_models` | Provider model catalog helper where implemented | `falai`, `openai`, `openrouter` |
| `text` | `update_cost` | Post-hoc cost refresh where implemented | `openai`, `openrouter` |
| `audio` | `generate` | Text-to-speech synthesis | `deepinfra`, `elevenlabs`, `google`, `mistral`, `openai`, `together`, `xai` |
| `audio` | `transcribe` | Speech-to-text transcription | `deepgram`, `elevenlabs`, `falai`, `fireworks`, `speechmatics`, `together` |
| `audio` | `update_cost` | Post-hoc transcription cost refresh where implemented | `deepgram` |
| `image` | `generate` | Text-to-image generation | `bfl`, `falai`, `fireworks`, `google`, `openai`, `openrouter`, `stability`, `together`, `xai` |
| `image` | `edit` | Prompt-guided image editing | `bfl`, `falai`, `fireworks`, `google`, `openai`, `openrouter`, `stability`, `together`, `xai` |
| `image` | `remix` | Reference-image guided generation | `bfl`, `falai`, `fireworks`, `google`, `openai`, `openrouter`, `stability`, `together`, `xai` |
| `image` | `analyze` | Vision and multimodal analysis | `anthropic`, `falai`, `fireworks`, `google`, `groq`, `openai`, `openrouter`, `together`, `xai` |
| `image` | `update_cost` | Post-hoc cost refresh where implemented | `openrouter` |

See the
[provider matrix](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/providers.md)
for per-provider documentation links.

## Selecting Providers

Every dispatcher requires `api=`. The value must match a supported provider
identifier for that operation.

```python
from easy_ai_clients import audio, image, text

print(text.available_apis())
print(audio.available_synthesize_apis())
print(audio.available_transcribe_apis())
print(image.available_generate_apis())
print(image.available_edit_apis())
print(image.available_remix_apis())
print(image.available_analyze_apis())
```

Provider modules under private `_apis` packages are implementation details.
Applications should call the public dispatchers shown above.

## Configuration

Credentials are read from environment variables at provider-call time. Configure
only the providers your application will call.

```bash
export OPENAI_API_KEY="sk-..."
export DEEPGRAM_API_KEY="..."
```

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:DEEPGRAM_API_KEY = "..."
```

The recommended pattern is to manage secrets in your application environment or
load a local `.env` file explicitly before calling the library:

```python
from dotenv import load_dotenv

load_dotenv()
```

Some current provider helpers also attempt to load a `.env` file from the
current working directory before resolving credentials. Do not rely on that as
your portability contract; loading environment variables explicitly keeps tests,
scripts, and deployments predictable.

Credential references:

- [`.env.example`](https://github.com/reiarthur/easy-ai-clients/blob/main/.env.example)
- [Configuration guide](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/configuration.md)

## Usage Patterns

### Text

```python
from easy_ai_clients import text

result = text.generate(
    "Write a release note headline.",
    instruction="Return one short sentence.",
    model="gpt-5-nano",
    api="openai",
    max_output_tokens=80,
)

print(result["output_text"])
```

`stream=True` is supported by text providers that expose streaming. The stream
is consumed internally and the dispatcher still returns the same normalized
dictionary.

### Audio

```python
from easy_ai_clients import audio

speech = audio.generate(
    "This is a short narration.",
    model="tts-1",
    voice="alloy",
    api="openai",
)
speech["audio"].export("narration.mp3", format="mp3")

bundle = audio.transcribe("narration.mp3", api="deepgram")
print(bundle["text"])

bundle = audio.update_cost("transcribe", bundle, api="deepgram")
```

Transcription inputs may be local paths, supported URLs, bytes, base64 strings,
data URLs, or `pydub.AudioSegment` objects when the selected provider adapter
supports that input form.

### Images

```python
from easy_ai_clients import image

generated = image.generate(
    "a minimal app icon with a blue compass",
    api="openai",
    size="1024x1024",
)

edited = image.edit(
    "replace the background with a white studio backdrop",
    "input.png",
    api="openai",
)

remixed = image.remix(
    "keep the subject but use watercolor style",
    ["input.png"],
    api="openai",
)

description = image.analyze(
    "List the visible objects.",
    "input.png",
    api="openai",
)
```

Image inputs can be local file paths, public `http` / `https` URLs, raw base64
image strings, or base64 data URLs. For `image.edit`, the public mask convention
is black = editable and white = preserve.

## Return Contracts

| Operation | Normalized result |
| --- | --- |
| `text.generate(...)` | `request_id`, `cost_source`, `cost_usd`, `input_text`, optional `instruction`, `output_text` |
| `audio.generate(...)` | `cost_usd`, `audio` as `pydub.AudioSegment`, `words` |
| `audio.transcribe(...)` | `text`, optional `words` / `segments` / `silences`, speaker metadata, `provider_metadata`, `request_id`, `cost_usd`, `cost_source`, `cost_is_estimated`, `cost_lookup_error`, optional `mkd` |
| `image.generate(...)`, `image.edit(...)`, `image.remix(...)` | `cust_usd`, `base64`, `warnings`, `request_id` |
| `image.analyze(...)` | `request_id`, `cost_usd`, `input_text`, `output` |

The image generation/edit/remix cost key is intentionally `cust_usd` for the
current public contract.

## Provider Parameters

Extra keyword arguments are provider-native. They are validated or forwarded by
the selected adapter:

```python
from easy_ai_clients import image, text

text.generate(
    "Return JSON with one key named status.",
    api="openai",
    model="gpt-5-nano",
    max_output_tokens=80,
    text={"format": {"type": "json_object"}},
)

image.generate(
    "a serene lake at dawn",
    api="stability",
    model="stable-image-ultra",
    aspect_ratio="16:9",
    output_format="png",
)
```

Unsupported kwargs raise before the provider call when the adapter has an
explicit supported-parameter surface. Image generation/edit/remix operations may
return provider-side failures in the `warnings` field when a provider supplies a
structured error payload.

## Costs

Cost values are best-effort normalized USD values:

- Some providers return exact usage or request cost.
- Some adapters compute cost from usage fields and local pricing tables.
- Some router/provider costs can be refined after the call.
- For transcription, unknown cost is `None`, not `0.0`; inspect
  `cost_source`, `cost_is_estimated`, and `cost_lookup_error`.

```python
from easy_ai_clients import audio, image, text

text_result = text.generate("ping", api="openrouter")
text_result = text.update_cost(text_result, api="openrouter")

image_result = image.generate("a tiny robot", api="openrouter")
image_result = image.update_cost("generate", image_result, api="openrouter")

transcript = audio.transcribe("meeting.mp3", api="deepgram")
transcript = audio.update_cost("transcribe", transcript, api="deepgram")
```

## Errors

The package uses standard Python exceptions instead of a custom hierarchy.
Common cases:

- `ValueError`: unknown `api`, unsupported model, unsupported parameter, or
  invalid parameter value.
- `TypeError`: unsupported keyword argument in adapters that reject unknown
  kwargs with `TypeError`.
- `RuntimeError` / `OSError`: missing credentials or provider failures.
- `requests` / `httpx` exceptions: transport or HTTP status failures where the
  adapter does not normalize them into a result field.
- `NotImplementedError`: helper methods such as cost updates are called for a
  provider that does not implement them.

See the
[error handling guide](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/errors.md)
for more detail.

## More Documentation

- [Configuration](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/configuration.md)
- [Usage patterns](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/usage.md)
- [Provider matrix](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/providers.md)
- [Error handling](https://github.com/reiarthur/easy-ai-clients/blob/main/docs/errors.md)
- [Full docs directory](https://github.com/reiarthur/easy-ai-clients/tree/main/docs)
- [Changelog](https://github.com/reiarthur/easy-ai-clients/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/reiarthur/easy-ai-clients/blob/main/CONTRIBUTING.md)

## License

MIT. See
[LICENSE](https://github.com/reiarthur/easy-ai-clients/blob/main/LICENSE).
