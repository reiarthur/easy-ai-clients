# Error Handling

`easy-ai-clients` uses standard Python exceptions instead of a custom exception
hierarchy. Dispatchers validate the selected `api` before importing the private
provider adapter, and provider adapters validate credentials and supported
parameters before or during the outbound request.

## Common Exceptions

| Exception | Typical cause |
| --- | --- |
| `ValueError` | Missing or unknown `api`, unsupported provider model, invalid enumerated value, invalid numeric range, or unsupported parameter in adapters that raise `ValueError`. |
| `TypeError` | Unsupported keyword argument in adapters that reject unknown kwargs with `TypeError`. |
| `RuntimeError` | Missing credentials in some text/image paths, provider response normalization failure, or wrapped provider/network failure. |
| `OSError` / `EnvironmentError` | Missing credentials in audio and some provider helper paths. |
| `requests.HTTPError` / `httpx.HTTPStatusError` | Provider returned a non-success HTTP status and the adapter raised the HTTP exception directly. |
| `requests.ConnectionError` / `requests.Timeout` | Network failure or timeout after retries. |
| `NotImplementedError` | Helper called for a provider that does not implement it, such as `text.update_cost(api="anthropic")`. |

Exact exception classes can vary by modality because provider adapters use
different HTTP clients and normalization paths. Catch narrow exceptions around
the operation you call when you need custom recovery behavior.

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

## Unsupported Parameters

Provider-native kwargs are validated by the selected adapter when that adapter
has an explicit supported-parameter surface.

```python
from easy_ai_clients import text

try:
    text.generate("hi", api="openai", this_parameter_does_not_exist=True)
except (TypeError, ValueError) as exc:
    print("Rejected before or during request preparation:", exc)
```

Unsupported parameters are not silently ignored.

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

## Defensive Pattern

```python
from easy_ai_clients import text


def safe_generate(prompt: str, *, api: str, **kwargs):
    try:
        return text.generate(prompt, api=api, **kwargs)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc
    except (RuntimeError, OSError) as exc:
        raise SystemExit(f"Provider setup or runtime failure: {exc}") from exc
```

Do not catch broad exceptions unless you are at an application boundary where
the error is logged, redacted, and converted to a user-facing failure.
