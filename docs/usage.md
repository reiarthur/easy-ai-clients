# Usage Patterns

This guide documents the public dispatcher layer. Provider modules under
private `_apis` packages are implementation details and should not be imported
by applications.

## Imports

```python
from easy_ai_clients import audio, image, text
```

Direct submodule imports are also supported:

```python
from easy_ai_clients.text import generate as text_generate
from easy_ai_clients.audio import generate as speech_generate
from easy_ai_clients.audio import transcribe
from easy_ai_clients.image import analyze
```

## Provider Selection

Every operation requires `api=`. Use the discovery helpers to inspect supported
provider identifiers:

```python
from easy_ai_clients import audio, image, text

text.available_apis()
audio.available_synthesize_apis()
audio.available_transcribe_apis()
image.available_generate_apis()
image.available_edit_apis()
image.available_remix_apis()
image.available_analyze_apis()
```

## Text Generation

```python
from easy_ai_clients import text

result = text.generate(
    "Write a concise status update.",
    instruction="Use plain English.",
    api="openai",
    model="gpt-5-nano",
    max_output_tokens=80,
)

print(result["output_text"])
```

Return keys:

- `request_id`
- `cost_source`
- `cost_usd`
- `input_text`
- optional `instruction`
- `output_text`

`text.list_models(api=...)` and `text.update_cost(result, api=...)` are
available only for providers that implement those helper functions.

## Text Streaming

For providers that support streaming, pass `stream=True` as a provider-native
kwarg. The adapter consumes the stream internally and returns the same final
dictionary contract as a non-streaming call.

```python
from easy_ai_clients import text

result = text.generate("Reply with OK.", api="openai", stream=True)
print(result["output_text"])
```

## Speech Synthesis

```python
from easy_ai_clients import audio

result = audio.generate(
    "Hello from easy-ai-clients.",
    api="openai",
    model="tts-1",
    voice="alloy",
    language_code="en",
)

result["audio"].export("speech.mp3", format="mp3")
```

Return keys:

- `cost_usd`
- `audio`, a `pydub.AudioSegment`
- `words`, a list of timing records when available

Some synthesis providers use alignment calls to recover word timings. Configure
the credentials documented for the selected provider path.

## Speech Transcription

```python
from easy_ai_clients import audio

bundle = audio.transcribe(
    "speech.mp3",
    api="deepgram",
    language="en",
)

print(bundle["text"])
```

Supported input forms depend on the selected adapter, but public preprocessing
supports local paths, supported URLs, bytes, base64 strings, data URLs, and
`pydub.AudioSegment` objects.

Common return keys include:

- `text`
- `words`
- `segments`
- `speakers`
- `silences`
- `metadata`
- `request_id`
- `cost_usd`
- optional `mkd`

## Image Generation, Editing, and Remixing

```python
from easy_ai_clients import image

generated = image.generate(
    "a minimal app icon with a blue compass",
    api="openai",
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
```

Return keys for these operations:

- `cust_usd`
- `base64`
- `warnings`
- `request_id`

The cost key is currently spelled `cust_usd` for this public contract.

Image inputs can be local paths, public `http` / `https` URLs, raw base64 image
strings, or base64 data URLs. For `image.edit`, the public mask convention is
black = editable and white = preserve.

## Image Analysis

```python
from easy_ai_clients import image

result = image.analyze(
    "Describe the visible objects.",
    "input.png",
    api="openai",
)

print(result["output"])
```

Return keys:

- `request_id`
- `cost_usd`
- `input_text`
- `output`

## Provider-Native Kwargs

Extra keyword arguments are provider-native. Use the provider docs for accepted
names and values:

```python
from easy_ai_clients import image, text

text.generate(
    "Return a compact JSON object.",
    api="openai",
    text={"format": {"type": "json_object"}},
    max_output_tokens=80,
)

image.generate(
    "a serene lake at dawn",
    api="stability",
    aspect_ratio="16:9",
    output_format="png",
)
```

Adapters reject unsupported kwargs when they have an explicit validation
surface. Image generation/edit/remix operations may return provider-side errors
inside `warnings` to preserve the normalized return shape.

## Cost Updates

```python
from easy_ai_clients import image, text

text_result = text.generate("ping", api="openrouter")
text_result = text.update_cost(text_result, api="openrouter")

image_result = image.generate("a small robot", api="openrouter")
image_result = image.update_cost("generate", image_result, api="openrouter")
```

Cost helpers raise `NotImplementedError` when the selected provider does not
support post-hoc cost lookup.
