# Error handling

`easy-ai-clients` keeps the error model simple and predictable: it reuses
standard Python exceptions instead of introducing a parallel hierarchy.
Errors are raised eagerly whenever possible — typically before a network
request is sent — so misconfigurations surface fast.

## Exception types

| Exception | When |
| --- | --- |
| `ValueError` | Invalid `api` selector, unsupported parameter, invalid choice for an enumerated parameter, invalid numeric range, or unsupported model identifier. |
| `TypeError` | Unsupported keyword argument forwarded to a provider that explicitly rejects unknown kwargs. |
| `EnvironmentError` / `RuntimeError` | Missing or empty environment variable for the selected provider's credential. |
| `requests.HTTPError` / `httpx.HTTPStatusError` | Provider responded with a non-success HTTP status. The body is included in the error message (truncated) for fast triage. |
| `requests.ConnectionError` / `requests.Timeout` | Transient network failure after exhausted retries. |
| `NotImplementedError` | A dispatcher helper is called for a provider that does not implement that operation (e.g. `text.list_models(api="anthropic")`). |

## Image operations: `warnings` field

Image operations (`image.generate`, `image.edit`, `image.remix`) embed
provider-side errors inside the public result instead of raising, when the
provider returns a structured error payload. Inspect the `warnings` field:

```python
result = image.generate("...", api="openai")
if result["warnings"]:
    print("provider message:", result["warnings"])
```

This convention preserves the canonical return shape
(`cust_usd`, `base64`, `warnings`, `request_id`) regardless of whether the
generation succeeded.

`image.analyze` collapses similar provider-side errors into the `output`
string so the call still returns the canonical shape
(`request_id`, `cost_usd`, `input_text`, `output`).

## Catching unsupported parameters

Every provider validates incoming kwargs against the parameter set it actually
supports. A typo or an option from another provider will raise immediately:

```python
try:
    text.generate("hi", api="openai", reasoning_effort="minimal")
except ValueError as exc:
    print(exc)
# Unsupported parameter for openai responses: 'reasoning_effort'. Model: 'gpt-5-nano'.
# Supported parameters for this context: ...
```

For text providers, the error explains whether the offending parameter is
known on a different provider surface.

## Defensive programming pattern

```python
from easy_ai_clients import text

def safe_generate(prompt, *, api, **kwargs):
    try:
        return text.generate(prompt, api=api, **kwargs)
    except ValueError as exc:
        # Bad parameter or unknown api/model.
        raise SystemExit(f"Configuration error: {exc}") from exc
    except RuntimeError as exc:
        # Missing credentials or provider HTTP failure.
        raise SystemExit(f"Provider failure: {exc}") from exc
```

## Streaming errors

When `stream=True` is passed to a text provider, streaming events are
accumulated internally and the dispatcher still returns the same dictionary.
Any HTTP error during stream consumption is raised as a `RuntimeError` with
the response status and a truncated body fragment.
