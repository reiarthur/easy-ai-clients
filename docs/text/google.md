# Google Gemini Text API Wrapper

## A. Overview
- The wrapper targets the native Gemini GenerateContent API.
- Raw generation endpoint: `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`.
- Live catalog endpoint: `GET https://generativelanguage.googleapis.com/v1beta/models`.
- The project abstracts credential loading, message construction, parameter validation, streaming accumulation, result normalization, and local cost estimation where available.
- Provider-native kwargs are forwarded directly after validation; unsupported kwargs fail before credentials are read.

## B. Account and access
- Create account / console: https://aistudio.google.com/app/apikey
- API key docs: https://ai.google.dev/gemini-api/docs/api-key
- Required environment variable: `GOOGLE_API_KEY`.
- Access restrictions are provider-specific. The validation matrix records account, tier, route, overload, and not-callable blockers observed in this account.

## C. Official references
- https://ai.google.dev/api/generate-content
- https://ai.google.dev/api/models
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/model-versioning

## D. Wrapper behavior summary
- Public function signature: `generate(input_text, instruction=None, model='gemini-2.5-flash-lite', **kwargs)`.
- Current default model: `gemini-2.5-flash-lite`.
- Default selection date: `2026-04-25`.
- Default selection source: live provider catalog, official pricing/model documentation, and real smoke validation in `validacao_text_apis_2026-04-25`.
- Tie-break reasoning: gemini-2.5-flash-lite is the lowest-cost stable Gemini text model validated; Gemini 2.0 variants were cataloged but unavailable to this account.
- Lowest-cost default policy: the wrapper sends only required text fields plus provider-required minimal output caps, when required. It does not enable tools, web/search, cache writes, structured output, premium service tiers, provider plugins, or explicit reasoning by default.
- Parameter validation policy: every kwarg must appear in the provider's documented parameter set for this wrapper context. Otherwise `UnsupportedParameterError` identifies provider/API, model, invalid parameter, supported parameters, and whether the parameter is known elsewhere.
- Streaming policy: `stream=True` is consumed internally; callers still receive the same normalized final dictionary.
- Public return contract: `request_id`, `cost_source`, `cost_usd`, `input_text`, optional `instruction`, and `output_text`, in that order.

## E. Parameter reference
### `cachedContent`
- What it is: Gemini cache reference. Omitted by default because cache creation/use changes billing.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `contents`
- What it is: Gemini content list. If supplied, it replaces the wrapper-built user content.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `generationConfig`
- What it is: Gemini generation options such as `maxOutputTokens`, `temperature`, `topP`, `topK`, and `thinkingConfig`.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `model`
- What it is: Provider model identifier. In this project it is exposed as the explicit `model` function argument; passing it again in kwargs is unnecessary.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `safetySettings`
- What it is: Gemini safety settings.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `serviceTier`
- What it is: Gemini service tier. Omitted by default.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `store`
- What it is: Provider response-storage flag. Omitted by default.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream`
- What it is: When true, the wrapper accumulates provider streaming internally and still returns the public result dict.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `systemInstruction`
- What it is: Gemini system instruction object. If supplied, it replaces the wrapper-built instruction.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `toolConfig`
- What it is: Gemini tool configuration.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tools`
- What it is: Provider-native tool definitions. Omitted by default because tools can add latency, token use, and external charges.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `google` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

## F. Model coverage
- Catalog snapshot date: `2026-04-25`.
- Relevant text/chat model count after scope filtering: `26` from raw catalog count `38`.
- Status values below come from real text-in/text-out calls unless the row is a parameter-cluster row.

| Model ID | Family | Validation result | Support status / blocker |
|---|---|---|---|
| gemini-2.5-flash-lite | gemini | passed | validated |
| gemini-2.5-flash | gemini | passed | validated |
| gemini-2.5-pro | gemini | passed | validated |
| gemini-2.0-flash | gemini | failed | catalog_listed_but_not_callable_in_endpoint |
| gemini-2.0-flash-001 | gemini | failed | catalog_listed_but_not_callable_in_endpoint |
| gemini-2.0-flash-lite-001 | gemini | failed | catalog_listed_but_not_callable_in_endpoint |
| gemini-2.0-flash-lite | gemini | failed | catalog_listed_but_not_callable_in_endpoint |
| gemma-3-1b-it | gemma | passed | validated |
| gemma-3-4b-it | gemma | passed | validated |
| gemma-3-12b-it | gemma | passed | validated |
| gemma-3-27b-it | gemma | passed | validated |
| gemma-3n-e4b-it | gemma | passed | validated |
| gemma-3n-e2b-it | gemma | passed | validated |
| gemma-4-26b-a4b-it | gemma | passed | validated |
| gemma-4-31b-it | gemma | passed | validated |
| gemini-flash-latest | gemini | passed | validated |
| gemini-flash-lite-latest | gemini | passed | validated |
| gemini-pro-latest | gemini | passed | validated |
| gemini-3-pro-preview | gemini | passed | validated |
| gemini-3-flash-preview | gemini | passed | validated |
| gemini-3.1-pro-preview | gemini | passed | validated |
| gemini-3.1-pro-preview-customtools | gemini | passed | validated |
| gemini-3.1-flash-lite-preview | gemini | passed | validated |
| nano-banana-pro-preview | nano | passed | validated |
| gemini-robotics-er-1.5-preview | gemini | passed | validated |
| gemini-robotics-er-1.6-preview | gemini | passed | validated |

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
from text.apis import google

result = google.generate("Reply with OK.")
print(result["output_text"])
```

### Explicit instruction
```python
result = google.generate(
    "Summarize this in one sentence.",
    instruction="Use plain English.",
)
```

### Explicit model
```python
result = google.generate(
    "Reply with OK.",
    model="gemini-2.5-flash-lite",
)
```

### Full options for the primary surface
```python
result = google.generate("Reply with JSON.", generationConfig={"maxOutputTokens": 64, "temperature": 0, "responseMimeType": "application/json"})
```

## J. Pricing section
- Pricing snapshot date: `2026-04-25`.
- Pricing source: see the official references above and the validation artifact `validacao_text_apis_2026-04-25/catalog_google.json`.
- Pricing can change without a code change, especially for routers and model aliases.
- The wrapper omits premium tiers, tools, web/search, cache writes, and explicit reasoning by default to avoid surprise charges.

## K. Validation note
- Real validation artifact: `tests/artefatos_testes/validacao_text_apis_2026-04-25/validation_matrix.md`.
- Provider result counts in the final matrix: `{'passed': 26, 'failed': 4}`.
- Failure blocker counts: `{'catalog_listed_but_not_callable_in_endpoint': 4}`.
- Failed rows are not claimed as supported; they are documented as provider, route, account, or model restrictions observed during validation.
