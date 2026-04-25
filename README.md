# easy-ai-clients

[![PyPI version](https://img.shields.io/pypi/v/easy-ai-clients.svg)](https://pypi.org/project/easy-ai-clients/)
[![Python versions](https://img.shields.io/pypi/pyversions/easy-ai-clients.svg)](https://pypi.org/project/easy-ai-clients/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A unified, batteries-included Python client for **text**, **audio**, and
**image** AI APIs across many providers. Every operation has a single function
that takes the same parameters and an explicit `api=` argument selecting the
underlying provider — so you can swap providers without rewriting your code.

## Supported operations

| Module | Function | Purpose | Providers |
| --- | --- | --- | --- |
| `text` | `generate` | Text-in / text-out generation | `anthropic`, `cohere`, `deepinfra`, `deepseek`, `fal`, `fireworks`, `google`, `groq`, `huggingface`, `mistral`, `openai`, `openrouter`, `together`, `xai` |
| `audio` | `generate` | Text-to-speech synthesis | `deepinfra`, `elevenlabs`, `google`, `mistral`, `openai`, `together`, `xai` |
| `audio` | `transcribe` | Speech-to-text transcription | `deepgram`, `elevenlabs`, `falai`, `fireworks`, `revai`, `speechmatics`, `together` |
| `image` | `generate` | Text-to-image generation | `bfl`, `falai`, `fireworks`, `google`, `openai`, `openrouter`, `stability`, `together`, `xai` |
| `image` | `edit` | Prompt + mask editing | `bfl`, `falai`, `fireworks`, `google`, `openai`, `openrouter`, `stability`, `together`, `xai` |
| `image` | `remix` | Reference-image guided generation | `bfl`, `falai`, `fireworks`, `google`, `openai`, `openrouter`, `stability`, `together`, `xai` |
| `image` | `analyze` | Vision/multimodal analysis | `anthropic`, `falai`, `fireworks`, `google`, `groq`, `openai`, `openrouter`, `together`, `xai` |

The full provider/model matrix and per-provider parameters are in
[`docs/providers.md`](docs/providers.md).

## Requirements

- Python `>= 3.11`
- Runtime dependencies are installed automatically by `pip`:
  `requests`, `httpx`, `Pillow`, `pydub`, `imageio-ffmpeg`, `python-dotenv`,
  and `audioop-lts` on Python `>= 3.13`.

## Install

```bash
pip install easy-ai-clients
```

## Checking the version

```python
import easy_ai_clients
print(easy_ai_clients.__version__)
```

## Configuration

`easy-ai-clients` does **not** auto-load `.env` from the package directory.
The recommended way is to set environment variables in your shell or load a
`.env` file explicitly with [`python-dotenv`](https://pypi.org/project/python-dotenv/):

```python
from dotenv import load_dotenv
load_dotenv()
```

Each provider only needs the credentials for the API you intend to call. See
[`.env.example`](.env.example) for the full list of recognised variables and
[`docs/configuration.md`](docs/configuration.md) for the credential resolution
flow.

## Quickstart

```python
from dotenv import load_dotenv
from easy_ai_clients import text, audio, image

load_dotenv()

# Text generation
result = text.generate(
    "Summarise the plot of Don Quixote in two sentences.",
    instruction="Answer in Brazilian Portuguese.",
    api="openai",
)
print(result["output_text"], "USD:", result["cost_usd"])

# Speech synthesis
speech = audio.generate(
    "Hello world from easy-ai-clients!",
    voice="alloy",
    language_code="en",
    api="openai",
)
speech["audio"].export("hello.mp3", format="mp3")

# Speech transcription
transcript = audio.transcribe("hello.mp3", api="deepgram")
print(transcript["text"])

# Image generation
import base64
img = image.generate("a corgi astronaut on the moon", api="openai")
with open("corgi.png", "wb") as fh:
    fh.write(base64.b64decode(img["base64"]))

# Image editing
edited = image.edit(
    "make it night with neon lights",
    "corgi.png",
    api="openai",
)

# Image remix (reference-image guided)
remix = image.remix(
    "studio ghibli style",
    ["corgi.png"],
    api="openai",
)

# Vision analysis
description = image.analyze(
    "Describe this image in one sentence.",
    "corgi.png",
    api="openai",
)
print(description["output"])
```

You can also import dispatchers directly:

```python
from easy_ai_clients.text import generate as text_generate
from easy_ai_clients.audio import transcribe
from easy_ai_clients.image import analyze
```

## Selecting an API

Every dispatcher accepts an `api` keyword argument. The string must match the
file name (without `.py`) of an internal provider module shipped with the
library. Inspect them programmatically:

```python
from easy_ai_clients import text, audio, image

text.available_apis()
audio.available_synthesize_apis()
audio.available_transcribe_apis()
image.available_generate_apis()
image.available_edit_apis()
image.available_remix_apis()
image.available_analyze_apis()
```

## Public return contracts

| Operation | Returns |
| --- | --- |
| `text.generate(...)` | `{"request_id", "cost_source", "cost_usd", "input_text", "instruction"?, "output_text"}` |
| `audio.generate(...)` | `{"cost_usd", "audio": pydub.AudioSegment, "words": [...]}` |
| `audio.transcribe(...)` | Normalised bundle with `text`, `words`, `segments`, `speakers`, `silences`, `cost_usd`, `request_id`, optional `mkd` markdown |
| `image.generate / edit / remix(...)` | `{"cust_usd", "base64", "warnings", "request_id"}` |
| `image.analyze(...)` | `{"request_id", "cost_usd", "input_text", "output"}` |

## Forwarding provider-native parameters

All dispatchers accept extra keyword arguments and forward them verbatim to the
underlying provider. Unsupported parameters are rejected with a clear error
message before any network call is made:

```python
text.generate(
    "ping",
    api="openai",
    model="gpt-5-mini",
    reasoning="minimal",
    temperature=0.2,
    max_output_tokens=80,
)

image.generate(
    "a serene lake at dawn",
    api="stability",
    model="stable-image-ultra",
    aspect_ratio="16:9",
    output_format="png",
)
```

## Error handling

Errors raise standard Python exceptions. Image operations also surface
provider-side problems via the `warnings` field in the public result instead
of raising, when the provider responds with a structured error.

```python
try:
    result = text.generate("hi", api="openai", thisparamdoesnotexist=True)
except ValueError as exc:
    print("rejected before sending:", exc)

try:
    result = text.generate("hi", api="openai")
except RuntimeError as exc:
    print("provider/network failure:", exc)
```

A complete reference is in [`docs/errors.md`](docs/errors.md).

## Additional documentation

- [`docs/configuration.md`](docs/configuration.md) — credentials and environment
  variables.
- [`docs/providers.md`](docs/providers.md) — provider-by-provider parameters and
  models.
- [`docs/errors.md`](docs/errors.md) — exception model and provider-specific
  failures.

## Contributing

Issues and pull requests are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md)
for the local development workflow.

## License

MIT — see [`LICENSE`](LICENSE).
