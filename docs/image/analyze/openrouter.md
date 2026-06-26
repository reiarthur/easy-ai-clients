# OpenRouter Analyze API

## Overview

This module implements image-to-text analysis for OpenRouter through the
repository-wide normalized public contract.

Public function:

```python
image.analyze(prompt, image, model=None, *, api="openrouter", **kwargs)
```

For `api="openrouter"`, `model` is required. Pass the exact OpenRouter model ID
expected by the API, such as `qwen/qwen3.7-plus`.

The normalized success result contains:

- `request_id`
- `cost_usd`
- `cost_currency`
- `cost_is_estimated`
- `cost_source`
- `cost_details`
- `input_text`
- `output`

Dispatcher-level provider errors may also add `warnings` and `error`.

Public image inputs accept local file paths, raw base64 image strings, `data:`
URLs, and public HTTP(S) image URLs.

## Credentials

Required environment variable:

```text
OPENROUTER_API_KEY
```

## Local Model Snapshot

Snapshot date: `2026-06-26`

The model order below matches the approved local validation snapshot used for
this update. Prices are normalized to USD per 1,000,000 tokens for token-based
fields. `-` means the local snapshot did not contain that field.

| `model` | Display name | Input modalities | Output | Token cap | Structured cap | Context | Reasoning | Input | Output price | Cache read/write |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| `qwen/qwen3.7-plus` | Qwen: Qwen3.7 Plus | text, image | text | 32 | 96 | 1,000,000 | - | 0.32 | 1.28 | 0.064 / 0.4 |
| `minimax/minimax-m3` | MiniMax: MiniMax M3 | text, image, video | text | 64 | 128 | 1,048,576 | - | 0.3 | 1.2 | 0.06 / - |
| `google/gemini-3.1-flash-lite` | Google: Gemini 3.1 Flash Lite | text, image, video, file, audio | text | 64 | 128 | 1,048,576 | - | 0.25 | 1.5 | 0.025 / 0.083333 |
| `openai/gpt-5.4` | OpenAI: GPT-5.4 | text, image, file | text | 192 | 192 | 1,050,000 | `{"effort": "low"}` | 2.5 | 15 | 0.25 / - |
| `google/gemini-3.5-flash` | Google: Gemini 3.5 Flash | text, image, video, file, audio | text | 512 | 512 | 1,048,576 | - | 1.5 | 9 | 0.15 / 0.083333 |
| `openai/gpt-5.5` | OpenAI: GPT-5.5 | file, image, text | text | 192 | 192 | 1,050,000 | `{"effort": "low"}` | 5 | 30 | 0.5 / - |
| `anthropic/claude-sonnet-4.6` | Anthropic: Claude Sonnet 4.6 | text, image, file | text | 32 | 96 | 1,000,000 | - | 3 | 15 | 0.3 / 3.75 |
| `anthropic/claude-opus-4.8` | Anthropic: Claude Opus 4.8 | text, image, file | text | 32 | 96 | 1,000,000 | - | 5 | 25 | 0.5 / 6.25 |

## Request Shape

The wrapper posts an OpenAI-style chat-completions payload to OpenRouter:

```text
POST https://openrouter.ai/api/v1/chat/completions
```

The generated payload always includes:

- `model`
- `messages[0].role="user"`
- `messages[0].content[]` with one text part and one `image_url` part

The image is normalized to a data URL before it is sent.

## Accepted Kwargs

Operational kwarg:

| Kwarg | Behavior |
| --- | --- |
| `timeout_seconds` | HTTP timeout for the OpenRouter request. Defaults to `60`. |

Documented provider payload kwargs:

| Kwarg | Behavior |
| --- | --- |
| `max_tokens` | Forwarded as a top-level OpenRouter payload field. |
| `max_completion_tokens` | Forwarded as a top-level OpenRouter payload field. |
| `temperature` | Forwarded as a top-level OpenRouter payload field. |
| `top_p` | Forwarded as a top-level OpenRouter payload field. |
| `top_k` | Forwarded as a top-level OpenRouter payload field. |
| `frequency_penalty` | Forwarded as a top-level OpenRouter payload field. |
| `presence_penalty` | Forwarded as a top-level OpenRouter payload field. |
| `repetition_penalty` | Forwarded as a top-level OpenRouter payload field. |
| `seed` | Forwarded as a top-level OpenRouter payload field. |
| `stop` | Forwarded as a top-level OpenRouter payload field. |
| `stream` | Forwarded as a top-level OpenRouter payload field. The validated calls use `False`. |
| `response_format` | Forwarded as a top-level OpenRouter payload field. |
| `structured_outputs` | Forwarded as a top-level OpenRouter payload field. |
| `provider` | Forwarded as a top-level OpenRouter payload field. |
| `reasoning` | Forwarded as a top-level OpenRouter payload field. |
| `tools` | Forwarded as a top-level OpenRouter payload field. |
| `tool_choice` | Forwarded as a top-level OpenRouter payload field. |
| `transforms` | Forwarded as a top-level OpenRouter payload field. |

Additional provider-native kwargs are also forwarded as top-level payload fields
when their value is not `None`.

## Model Parameter Notes

The local snapshot uses these parameters for image analysis examples:

| Model | Direct cap | Structured cap | Suggested direct kwargs |
| --- | ---: | ---: | --- |
| `qwen/qwen3.7-plus` | 32 | 96 | `temperature=0`, `top_p=1` |
| `minimax/minimax-m3` | 64 | 128 | `temperature=0`, `top_p=1` |
| `google/gemini-3.1-flash-lite` | 64 | 128 | `temperature=0`, `top_p=1` |
| `openai/gpt-5.4` | 192 | 192 | `reasoning={"effort": "low"}` |
| `google/gemini-3.5-flash` | 512 | 512 | `temperature=0`, `top_p=1` |
| `openai/gpt-5.5` | 192 | 192 | `reasoning={"effort": "low"}` |
| `anthropic/claude-sonnet-4.6` | 32 | 96 | `temperature=0`, `top_p=1` |
| `anthropic/claude-opus-4.8` | 32 | 96 | - |

Structured fallback payloads can use `response_format` with a JSON schema and
`provider={"require_parameters": True}` when the caller needs strict JSON.

For GPT reasoning models, the local validation flow also allows retrying without
`reasoning` when the direct reasoning request returns an ambiguous answer.

## Python Example

```python
from easy_ai_clients import image

result = image.analyze(
    "Describe the important visual details.",
    "input.png",
    api="openrouter",
    model="qwen/qwen3.7-plus",
    max_tokens=32,
    temperature=0,
    top_p=1,
)

print(result["output"])
print(result["cost_usd"])
```

## Cost Behavior

For OpenRouter analyze calls, the wrapper uses the best cost value available at
the time of the request:

1. `usage.cost` from the chat-completions response, when present.
2. `total_cost` from `GET https://openrouter.ai/api/v1/generation?id=<request_id>`
   when the initial response has a `request_id`.
3. `0.0` with unavailable cost metadata when no cost value is available.

You can refresh a result later when it has a `request_id`:

```python
from easy_ai_clients import image

updated = image.update_cost("analyze", result, api="openrouter")
```

## Compatibility Notes

This page is not a live validation report.

The OpenRouter analyze wrapper does not enforce a local allowlist or local
model-compatibility gate. It forwards the selected `model` and accepted kwargs
to OpenRouter. OpenRouter or the routed provider can still reject a model,
account, parameter, image, quota, or billing state at request time.
