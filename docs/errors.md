# Error Handling

Public operations in `easy-ai-clients` prefer normalized failure dictionaries
over exceptions. When a dispatcher can preserve the operation shape, it returns
safe empty output plus an `error` object:

- `type`
- `message`
- `provider`
- `operation`
- `model`

Error messages are compacted and redacted so API keys, authorization headers,
tokens, and matching environment-secret values are not exposed.

## Common Exceptions

| Exception | Typical cause |
| --- | --- |
| `ValueError` | Local request assembly errors, incompatible local media arguments, or unsupported helper operation. |
| `TypeError` | Invalid helper/private-adapter call shape. |
| `RuntimeError` | Missing credentials in direct private adapter paths, provider response normalization failure, or wrapped provider/network failure. |
| `OSError` / `EnvironmentError` | Missing credentials in audio and some provider helper paths. |
| `requests.HTTPError` / `httpx.HTTPStatusError` | Provider returned a non-success HTTP status and the adapter raised the HTTP exception directly. |
| `requests.ConnectionError` / `requests.Timeout` | Network failure or timeout after retries. |
| `NotImplementedError` | Helper called for a provider that does not implement it, such as `text.update_cost(api="anthropic")`. |

Exact exception classes can still vary in helper methods and private adapters
because provider modules use different HTTP clients. Public dispatchers convert
those failures into dictionaries when possible.

## Public Failure Shapes

| Operation | Failure fields |
| --- | --- |
| `text.generate` | `output_text=""`, `cost_usd=0.0`, `cost_source="unavailable"`, `warnings`, `error` |
| `audio.generate` | `audio=None`, `words={}`, `cost_usd=0.0`, `warnings`, `error` |
| `audio.transcribe` | `text=""`, `cost_usd=0.0`, `cost_source="unavailable"`, `cost_lookup_error`, `warnings`, `error` |
| `image.generate/edit/remix` | `base64=""`, `cust_usd=0.0`, `warnings`, `error` |
| `image.analyze` | `output` contains the failure text, `cost_usd=0.0`, `warnings`, `error` |
| `video.*` | `status="failed"`, `video_url=None`, `cost_usd=0.0`, `cost_source="unavailable"`, `warnings`, `error` |

## Image Warnings

`image.generate`, `image.edit`, and `image.remix` preserve the public return
shape when a provider returns a structured failure that can be normalized:

```python
from easy_ai_clients import image

result = image.generate("a small app icon", api="openai")
if result["warnings"]:
    print("provider warning:", result["warnings"])
```

The returned dictionary still contains `cust_usd`, `base64`, `warnings`, and
`request_id`. When generation fails, `base64` may be empty and `warnings` should
be treated as the failure message.

`image.analyze` returns the normalized keys `request_id`, `cost_usd`,
`input_text`, and `output`. Some provider-side failures are represented in the
`output` string when the adapter can preserve the public return contract.

## Models and Provider Kwargs

Provider-native kwargs are forwarded whenever the wrapper can assemble a
request. The documented model and parameter tables are reference metadata for
defaults, examples, and pricing. They are not an acceptance gate.

```python
from easy_ai_clients import text

result = text.generate(
    "hi",
    api="openai",
    model="provider-new-model",
    provider_new_parameter=True,
)

if result.get("error"):
    print(result["error"]["message"])
```

If the provider accepts the model and kwargs, the call succeeds. If the provider
rejects them, the dispatcher returns a normalized error result. Local validation
is kept only for cases that prevent building a request, such as missing local
files, conflicting `path`/`url` arguments, or invalid internal payload shapes.

## Cost Helper Errors

Cost refresh helpers are implemented only for providers that expose compatible
request lookup or generation lookup behavior.

```python
from easy_ai_clients import text

result = text.generate("ping", api="openrouter")
result = text.update_cost(result, api="openrouter")

try:
    text.update_cost({}, api="anthropic")
except NotImplementedError:
    print("Anthropic does not implement text.update_cost.")
```

For images, pass the operation name explicitly:

```python
from easy_ai_clients import image

result = image.generate("a tiny robot", api="openrouter")
result = image.update_cost("generate", result, api="openrouter")
```

For transcription, only Deepgram currently implements post-hoc cost refresh:

```python
from easy_ai_clients import audio

result = audio.transcribe("meeting.mp3", api="deepgram")
result = audio.update_cost("transcribe", result, api="deepgram")

try:
    audio.update_cost("transcribe", result, api="fireworks")
except NotImplementedError:
    print("Fireworks does not implement transcription cost refresh.")
```

`audio.update_cost(...)` raises `ValueError` for unsupported operations; the
only supported operation is currently `"transcribe"`.

## Unknown Cost

When cost cannot be known from provider usage, pricing APIs, or documented
metadata, results use:

- `cost_usd=0.0`
- `cost_source="unavailable"`
- `cost_is_estimated` according to the operation contract
- `warnings` or `cost_lookup_error` with a sanitized reason when one is available

When a provider price table or pricing API is used, `cost_is_estimated=True`.
Deepgram exact usage lookup still returns `cost_source="usage_lookup"` and
`cost_is_estimated=False`.

## Defensive Pattern

```python
from easy_ai_clients import text


def safe_generate(prompt: str, *, api: str, **kwargs):
    result = text.generate(prompt, api=api, **kwargs)
    if result.get("error"):
        raise SystemExit(result["error"]["message"])
    return result
```

For helper methods and direct private adapters, catch narrow exceptions around
the call you make. Do not catch broad exceptions unless you are at an application
boundary where the error is logged, redacted, and converted to a user-facing
failure.
