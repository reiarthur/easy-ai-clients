# OpenAI Text API Wrapper

## A. Overview
- The wrapper targets the native OpenAI Responses API.
- Raw generation endpoint: `POST https://api.openai.com/v1/responses`.
- Live catalog endpoint: `GET https://api.openai.com/v1/models`.
- The project abstracts credential loading, message construction, parameter validation, streaming accumulation, result normalization, and local cost estimation where available.
- Provider-native kwargs are forwarded directly after validation; unsupported kwargs fail before credentials are read.

## B. Account and access
- Create account / console: https://platform.openai.com/signup
- API key docs: https://platform.openai.com/api-keys
- Required environment variable: `OPENAI_API_KEY`.
- Access restrictions are provider-specific. The validation matrix records account, tier, route, overload, and not-callable blockers observed in this account.

## C. Official references
- https://platform.openai.com/docs/api-reference/responses/create
- https://platform.openai.com/docs/api-reference/models/list
- https://developers.openai.com/api/docs/models/all
- https://platform.openai.com/docs/pricing/

## D. Wrapper behavior summary
- Public function signature: `generate(input_text, instruction=None, model='gpt-5-nano', **kwargs)`.
- Current default model: `gpt-5-nano`.
- Default selection date: `2026-04-25`.
- Default selection source: live provider catalog, official pricing/model documentation, and real smoke validation in `validacao_text_apis_2026-04-25`.
- Tie-break reasoning: gpt-5-nano is the lowest-cost relevant Responses API text model validated as callable.
- Lowest-cost default policy: the wrapper sends only required text fields plus provider-required minimal output caps, when required. It does not enable tools, web/search, cache writes, structured output, premium service tiers, provider plugins, or explicit reasoning by default.
- Parameter validation policy: every kwarg must appear in the provider's documented parameter set for this wrapper context. Otherwise `UnsupportedParameterError` identifies provider/API, model, invalid parameter, supported parameters, and whether the parameter is known elsewhere.
- Streaming policy: `stream=True` is consumed internally; callers still receive the same normalized final dictionary.
- Public return contract: `request_id`, `cost_source`, `cost_usd`, `input_text`, optional `instruction`, and `output_text`, in that order.

## E. Parameter reference
### `background`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `conversation`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `include`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `input`
- What it is: OpenAI Responses input object or string. If supplied, it replaces the wrapper `input_text` payload field.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `instructions`
- What it is: OpenAI Responses instruction field. If supplied, it replaces the wrapper `instruction` field.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_output_tokens`
- What it is: OpenAI Responses output token cap. OpenAI validated a minimum of 16 for gpt-5-nano.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_tool_calls`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `metadata`
- What it is: Provider metadata object. It does not affect output but may affect storage/audit behavior.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `model`
- What it is: Provider model identifier. In this project it is exposed as the explicit `model` function argument; passing it again in kwargs is unnecessary.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `parallel_tool_calls`
- What it is: Tool parallelism control for providers that expose it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `previous_response_id`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `prompt_cache_key`
- What it is: Cache key for providers that expose prompt caching.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `prompt_cache_retention`
- What it is: OpenAI prompt cache retention policy.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `reasoning`
- What it is: Provider-native reasoning object. Omitted by default to avoid premium reasoning cost.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `safety_identifier`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `service_tier`
- What it is: Provider queue/pricing tier. Omitted by default to avoid premium routing.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `store`
- What it is: Provider response-storage flag. Omitted by default.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream`
- What it is: When true, the wrapper accumulates provider streaming internally and still returns the public result dict.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream_options`
- What it is: OpenAI-compatible streaming options, forwarded only when the provider accepts them.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `temperature`
- What it is: Sampling randomness. Lower values improve determinism; some reasoning/default models reject it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `text`
- What it is: OpenAI Responses text formatting object, including structured output format.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tool_choice`
- What it is: Provider-native tool-selection policy.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tools`
- What it is: Provider-native tool definitions. Omitted by default because tools can add latency, token use, and external charges.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_p`
- What it is: Nucleus sampling control. Use instead of, not always together with, temperature when the provider restricts sampling.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `truncation`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `user`
- What it is: Provider user identifier.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openai` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

## F. Model coverage
- Catalog snapshot date: `2026-04-25`.
- Relevant text/chat model count after scope filtering: `75` from raw catalog count `132`.
- Status values below come from real text-in/text-out calls unless the row is a parameter-cluster row.

| Model ID | Family | Validation result | Support status / blocker |
|---|---|---|---|
| gpt-5-nano | gpt | passed | validated |
| gpt-4-0613 | gpt | passed | validated |
| gpt-4 | gpt | passed | validated |
| gpt-3.5-turbo | gpt | passed | validated |
| gpt-5.5-pro-2026-04-23 | gpt | passed | validated |
| gpt-5.5 | gpt | passed | validated |
| gpt-5.5-2026-04-23 | gpt | passed | validated |
| gpt-5.5-pro | gpt | passed | validated |
| babbage-002 | babbage | failed | catalog_listed_but_not_callable_in_endpoint |
| gpt-3.5-turbo-1106 | gpt | passed | validated |
| gpt-3.5-turbo-0125 | gpt | passed | validated |
| gpt-4-turbo | gpt | passed | validated |
| gpt-4-turbo-2024-04-09 | gpt | passed | validated |
| gpt-4o | gpt | passed | validated |
| gpt-4o-2024-05-13 | gpt | passed | validated |
| gpt-4o-mini-2024-07-18 | gpt | passed | validated |
| gpt-4o-mini | gpt | passed | validated |
| gpt-4o-2024-08-06 | gpt | passed | validated |
| o1-2024-12-17 | o1 | passed | validated |
| o1 | o1 | passed | validated |
| o3-mini | o3 | passed | validated |
| o3-mini-2025-01-31 | o3 | passed | validated |
| gpt-4o-2024-11-20 | gpt | passed | validated |
| gpt-4o-mini-search-preview-2025-03-11 | gpt | failed | catalog_listed_but_not_callable_in_endpoint |
| gpt-4o-mini-search-preview | gpt | failed | catalog_listed_but_not_callable_in_endpoint |
| o1-pro-2025-03-19 | o1 | passed | validated |
| o1-pro | o1 | passed | validated |
| o3-2025-04-16 | o3 | passed | validated |
| o4-mini-2025-04-16 | o4 | passed | validated |
| o3 | o3 | passed | validated |
| o4-mini | o4 | passed | validated |
| gpt-4.1-2025-04-14 | gpt | passed | validated |
| gpt-4.1 | gpt | passed | validated |
| gpt-4.1-mini-2025-04-14 | gpt | passed | validated |
| gpt-4.1-mini | gpt | passed | validated |
| gpt-4.1-nano-2025-04-14 | gpt | passed | validated |
| gpt-4.1-nano | gpt | passed | validated |
| o3-pro | o3 | passed | validated |
| o3-pro-2025-06-10 | o3 | passed | validated |
| gpt-5-chat-latest | gpt | passed | validated |
| gpt-5-2025-08-07 | gpt | passed | validated |
| gpt-5 | gpt | passed | validated |
| gpt-5-mini-2025-08-07 | gpt | passed | validated |
| gpt-5-mini | gpt | passed | validated |
| gpt-5-nano-2025-08-07 | gpt | passed | validated |
| gpt-5-codex | gpt | failed | provider_internal_error |
| gpt-5-pro-2025-10-06 | gpt | passed | validated |
| gpt-5-pro | gpt | passed | validated |
| gpt-5-search-api | gpt | failed | provider_internal_error |
| gpt-5-search-api-2025-10-14 | gpt | failed | provider_internal_error |
| gpt-5.1-chat-latest | gpt | passed | validated |
| gpt-5.1-2025-11-13 | gpt | passed | validated |
| gpt-5.1 | gpt | passed | validated |
| gpt-5.1-codex | gpt | passed | validated |
| gpt-5.1-codex-mini | gpt | passed | validated |
| gpt-5.1-codex-max | gpt | passed | validated |
| gpt-5.2-2025-12-11 | gpt | passed | validated |
| gpt-5.2 | gpt | passed | validated |
| gpt-5.2-pro-2025-12-11 | gpt | passed | validated |
| gpt-5.2-pro | gpt | passed | validated |
| gpt-5.2-chat-latest | gpt | passed | validated |
| gpt-5.2-codex | gpt | passed | validated |
| gpt-5.3-codex | gpt | passed | validated |
| gpt-4o-search-preview | gpt | failed | catalog_listed_but_not_callable_in_endpoint |
| gpt-4o-search-preview-2025-03-11 | gpt | failed | catalog_listed_but_not_callable_in_endpoint |
| gpt-5.3-chat-latest | gpt | failed | provider_internal_error |
| gpt-5.4-2026-03-05 | gpt | passed | validated |
| gpt-5.4-pro | gpt | passed | validated |
| gpt-5.4-pro-2026-03-05 | gpt | passed | validated |
| gpt-5.4 | gpt | passed | validated |
| gpt-5.4-nano-2026-03-17 | gpt | passed | validated |
| gpt-5.4-nano | gpt | passed | validated |
| gpt-5.4-mini-2026-03-17 | gpt | passed | validated |
| gpt-5.4-mini | gpt | passed | validated |
| gpt-3.5-turbo-16k | gpt | failed | catalog_listed_but_not_callable_in_endpoint |

## G. Parameter-surface grouping
- Core text/chat surface: `model`, wrapper-built prompt fields, output caps, sampling, stop sequences, and streaming.
- Tool surface: `tools`, `tool_choice`, provider-specific tool config, and parallel tool options; omitted by default.
- Structured-output surface: `response_format`, OpenAI `text`, or Gemini `generationConfig.responseSchema`; omitted by default.
- Reasoning/thinking surface: provider-native `reasoning`, `reasoning_effort`, or `thinking`; omitted by default unless the caller passes it.
- Routing/tier/cache surface: router/provider/tier/cache controls; omitted by default except OpenRouter/fal usage accounting.

## H. Wrapper-to-provider mapping
- `input_text` and `instruction` are converted to provider-native prompt fields unless the caller supplies the corresponding native structure.
- All kwargs are validated first, then forwarded using their native names.
- `stream=True` switches to SSE accumulation and then normalizes the final response.
- No optional paid features are injected for lowest-cost behavior.
- Cost is computed from provider usage/cost fields when available, otherwise from local fallback pricing tables for known models.

## I. Python examples
### Minimal cheapest call
```python
from text.apis import openai

result = openai.generate("Reply with OK.")
print(result["output_text"])
```

### Explicit instruction
```python
result = openai.generate(
    "Summarize this in one sentence.",
    instruction="Use plain English.",
)
```

### Explicit model
```python
result = openai.generate(
    "Reply with OK.",
    model="gpt-5-nano",
)
```

### Full options for the primary surface
```python
result = openai.generate("Reply with JSON.", model="gpt-4.1-nano", max_output_tokens=64, temperature=0, text={"format": {"type": "json_object"}})
```

## J. Pricing section
- Pricing snapshot date: `2026-04-25`.
- Pricing source: see the official references above and the validation artifact `validacao_text_apis_2026-04-25/catalog_openai.json`.
- Pricing can change without a code change, especially for routers and model aliases.
- The wrapper omits premium tiers, tools, web/search, cache writes, and explicit reasoning by default to avoid surprise charges.

## K. Validation note
- Real validation artifact: `tests/artefatos_testes/validacao_text_apis_2026-04-25/validation_matrix.md`.
- Provider result counts in the final matrix: `{'passed': 69, 'failed': 10}`.
- Failure blocker counts: `{'catalog_listed_but_not_callable_in_endpoint': 6, 'provider_internal_error': 4}`.
- Failed rows are not claimed as supported; they are documented as provider, route, account, or model restrictions observed during validation.
