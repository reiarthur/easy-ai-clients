# DeepInfra Text API Wrapper

## A. Overview
- The wrapper targets the OpenAI-compatible chat completions API.
- Raw generation endpoint: `POST https://api.deepinfra.com/v1/openai/chat/completions`.
- Live catalog endpoint: `GET https://api.deepinfra.com/v1/openai/models`.
- The project abstracts credential loading, message construction, parameter validation, streaming accumulation, result normalization, and local cost estimation where available.
- Provider-native kwargs are forwarded directly after validation; unsupported kwargs fail before credentials are read.

## B. Account and access
- Create account / console: https://deepinfra.com/
- API key docs: https://deepinfra.com/dash/api_keys
- Required environment variable: `DEEPINFRA_API_KEY`.
- Access restrictions are provider-specific. The validation matrix records account, tier, route, overload, and not-callable blockers observed in this account.

## C. Official references
- https://docs.deepinfra.com/chat/overview
- https://docs.deepinfra.com/api-reference/openai
- https://deepinfra.com/models
- https://deepinfra.com/pricing

## D. Wrapper behavior summary
- Public function signature: `generate(input_text, instruction=None, model='Qwen/Qwen3.5-0.8B', **kwargs)`.
- Current default model: `Qwen/Qwen3.5-0.8B`.
- Default selection date: `2026-04-25`.
- Default selection source: live provider catalog, official pricing/model documentation, and source defaults.
- Tie-break reasoning: Qwen/Qwen3.5-0.8B is the lowest-cost text chat route in the DeepInfra pricing/catalog snapshot that returned text.
- Lowest-cost default policy: the wrapper sends only required text fields plus provider-required minimal output caps, when required. It does not enable tools, web/search, cache writes, structured output, premium service tiers, provider plugins, or explicit reasoning by default.
- Parameter validation policy: every kwarg must appear in the provider's documented parameter set for this wrapper context. Otherwise `UnsupportedParameterError` identifies provider/API, model, invalid parameter, supported parameters, and whether the parameter is known elsewhere.
- Streaming policy: `stream=True` is consumed internally; callers still receive the same normalized final dictionary.
- Public return contract: `request_id`, `cost_source`, `cost_usd`, `input_text`, optional `instruction`, and `output_text`, in that order.

## E. Parameter reference
### `frequency_penalty`
- What it is: Penalty for repeated tokens.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `logit_bias`
- What it is: Token bias map for OpenAI-compatible APIs.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `logprobs`
- What it is: Token log probability return option. May add payload size and latency.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_completion_tokens`
- What it is: OpenAI-compatible completion cap used by selected reasoning/chat models.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_tokens`
- What it is: Maximum generated tokens for chat-style APIs. Lower values reduce cost and latency.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `messages`
- What it is: Provider-native chat message list. If supplied, it replaces the wrapper-built system/user messages.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `metadata`
- What it is: Provider metadata object. It does not affect output but may affect storage/audit behavior.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `min_p`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `model`
- What it is: Provider model identifier. In this project it is exposed as the explicit `model` function argument; passing it again in kwargs is unnecessary.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `n`
- What it is: Number of choices. Defaults to provider behavior; values above one increase cost.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `parallel_tool_calls`
- What it is: Tool parallelism control for providers that expose it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `presence_penalty`
- What it is: Penalty that encourages new topics.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `reasoning_effort`
- What it is: Provider-native reasoning effort selector for compatible model families.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `repetition_penalty`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `response_format`
- What it is: Structured output / JSON mode configuration when supported by the model.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `seed`
- What it is: Best-effort deterministic seed where the provider supports it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `service_tier`
- What it is: Provider queue/pricing tier. Omitted by default to avoid premium routing.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stop`
- What it is: OpenAI-compatible stop strings.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream`
- What it is: When true, the wrapper accumulates provider streaming internally and still returns the public result dict.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream_options`
- What it is: OpenAI-compatible streaming options, forwarded only when the provider accepts them.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `temperature`
- What it is: Sampling randomness. Lower values improve determinism; some reasoning/default models reject it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tool_choice`
- What it is: Provider-native tool-selection policy.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tools`
- What it is: Provider-native tool definitions. Omitted by default because tools can add latency, token use, and external charges.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_k`
- What it is: Provider-specific sampling cutoff. Higher values may increase diversity.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_logprobs`
- What it is: Number of top token log probabilities to return.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_p`
- What it is: Nucleus sampling control. Use instead of, not always together with, temperature when the provider restricts sampling.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `user`
- What it is: Provider user identifier.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `deepinfra` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

## F. Model coverage
- Catalog snapshot date: `2026-04-25`.
- Relevant text/chat model count after scope filtering: `86` from raw catalog count `154`.
- Status values below come from real text-in/text-out calls unless the row is a parameter-cluster row.

| Model ID | Family | Validation result | Support status / blocker |
|---|---|---|---|
| Qwen/Qwen3.5-0.8B | Qwen | passed | validated |
| google/gemini-2.5-pro | google | failed | provider_internal_error |
| Qwen/Qwen3-Max | Qwen | passed | validated |
| deepseek-ai/DeepSeek-V3.1 | deepseek-ai | passed | validated |
| Qwen/Qwen3-14B | Qwen | passed | validated |
| moonshotai/Kimi-K2.5 | moonshotai | passed | validated |
| anthropic/claude-4-sonnet | anthropic | passed | validated |
| deepseek-ai/DeepSeek-V3 | deepseek-ai | passed | validated |
| google/gemini-2.5-flash | google | passed | validated |
| NousResearch/Hermes-3-Llama-3.1-405B | NousResearch | passed | validated |
| deepseek-ai/DeepSeek-R1-0528 | deepseek-ai | passed | validated |
| Qwen/Qwen3-30B-A3B | Qwen | passed | validated |
| Qwen/Qwen3-Max-Thinking | Qwen | passed | validated |
| stepfun-ai/Step-3.5-Flash | stepfun-ai | passed | validated |
| mistralai/Mistral-Small-24B-Instruct-2501 | mistralai | passed | validated |
| meta-llama/Meta-Llama-3-8B-Instruct | meta-llama | passed | validated |
| Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo | Qwen | passed | validated |
| zai-org/GLM-4.6 | zai-org | passed | validated |
| meta-llama/Llama-3.2-11B-Vision-Instruct | meta-llama | passed | validated |
| google/gemma-3-27b-it | google | passed | validated |
| openai/gpt-oss-120b-Turbo | openai | passed | validated |
| meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8 | meta-llama | failed | provider_rate_limit_or_overload |
| Qwen/Qwen3-VL-30B-A3B-Instruct | Qwen | passed | validated |
| meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo | meta-llama | passed | validated |
| nvidia/NVIDIA-Nemotron-Nano-9B-v2 | nvidia | passed | validated |
| meta-llama/Meta-Llama-3.1-8B-Instruct | meta-llama | passed | validated |
| Wan-AI/Wan2.6-T2I | Wan-AI | failed | catalog_listed_but_not_callable_in_endpoint |
| anthropic/claude-3-7-sonnet-latest | anthropic | passed | validated |
| zai-org/GLM-5.1 | zai-org | passed | validated |
| google/gemini-1.5-flash-8b | google | failed | catalog_listed_but_not_callable_in_endpoint |
| Qwen/Qwen3-32B | Qwen | passed | validated |
| Sao10K/L3.3-70B-Euryale-v2.3 | Sao10K | passed | validated |
| openai/gpt-oss-20b | openai | passed | validated |
| nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL | nvidia | passed | validated |
| ByteDance/Seed-1.8 | ByteDance | passed | validated |
| Qwen/Qwen3.5-2B | Qwen | passed | validated |
| mistralai/Mistral-Nemo-Instruct-2407 | mistralai | passed | validated |
| meta-llama/Llama-4-Scout-17B-16E-Instruct | meta-llama | passed | validated |
| zai-org/GLM-4.7-Flash | zai-org | passed | validated |
| moonshotai/Kimi-K2.6 | moonshotai | passed | validated |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | mistralai | passed | validated |
| google/gemini-1.5-flash | google | failed | catalog_listed_but_not_callable_in_endpoint |
| allenai/Olmo-3.1-32B-Instruct | allenai | passed | validated |
| Qwen/Qwen3-Next-80B-A3B-Instruct | Qwen | passed | validated |
| nvidia/Llama-3.1-Nemotron-70B-Instruct | nvidia | passed | validated |
| deepseek-ai/DeepSeek-R1-0528-Turbo | deepseek-ai | passed | validated |
| meta-llama/Llama-Guard-4-12B | meta-llama | passed | validated |
| deepseek-ai/DeepSeek-V4-Pro | deepseek-ai | failed | provider_timeout |
| ByteDance/Seed-2.0-mini | ByteDance | passed | validated |
| mistralai/Mixtral-8x7B-Instruct-v0.1 | mistralai | passed | validated |
| Qwen/Qwen3-235B-A22B-Instruct-2507 | Qwen | passed | validated |
| meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo | meta-llama | passed | validated |
| Gryphe/MythoMax-L2-13b | Gryphe | passed | validated |
| NousResearch/Hermes-3-Llama-3.1-70B | NousResearch | passed | validated |
| Qwen/Qwen3.5-122B-A10B | Qwen | passed | validated |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | meta-llama | passed | validated |
| zai-org/GLM-5 | zai-org | passed | validated |
| nvidia/NVIDIA-Nemotron-3-Super-120B-A12B | nvidia | passed | validated |
| anthropic/claude-4-opus | anthropic | passed | validated |
| google/gemma-4-26B-A4B-it | google | passed | validated |
| Qwen/Qwen3.5-27B | Qwen | passed | validated |
| deepseek-ai/DeepSeek-V3.2 | deepseek-ai | passed | validated |
| MiniMaxAI/MiniMax-M2.5 | MiniMaxAI | passed | validated |
| meta-llama/Meta-Llama-3.1-70B-Instruct | meta-llama | passed | validated |
| nvidia/Llama-3.3-Nemotron-Super-49B-v1.5 | nvidia | passed | validated |
| Sao10K/L3-8B-Lunaris-v1-Turbo | Sao10K | passed | validated |
| Qwen/Qwen3.6-35B-A3B | Qwen | passed | validated |
| openai/gpt-oss-120b | openai | passed | validated |
| nvidia/Nemotron-3-Nano-30B-A3B | nvidia | passed | validated |
| microsoft/phi-4 | microsoft | passed | validated |
| Qwen/Qwen3.5-4B | Qwen | passed | validated |
| Qwen/Qwen2.5-72B-Instruct | Qwen | passed | validated |
| Qwen/Qwen3-235B-A22B-Thinking-2507 | Qwen | passed | validated |
| deepseek-ai/DeepSeek-R1-Distill-Llama-70B | deepseek-ai | passed | validated |
| google/gemma-3-4b-it | google | passed | validated |
| google/gemma-4-31B-it | google | passed | validated |
| deepseek-ai/DeepSeek-V3-0324 | deepseek-ai | passed | validated |
| deepseek-ai/DeepSeek-V3.1-Terminus | deepseek-ai | passed | validated |
| Qwen/Qwen3-VL-235B-A22B-Instruct | Qwen | passed | validated |
| zai-org/GLM-4.7 | zai-org | passed | validated |
| Qwen/Qwen3.5-397B-A17B | Qwen | passed | validated |
| Qwen/Qwen3.5-35B-A3B | Qwen | passed | validated |
| Sao10K/L3.1-70B-Euryale-v2.2 | Sao10K | passed | validated |
| ByteDance/Seed-2.0-pro | ByteDance | passed | validated |
| google/gemma-3-12b-it | google | passed | validated |
| deepseek-ai/DeepSeek-V4-Flash | deepseek-ai | passed | validated |

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
### Minimal call
~~~python
from easy_ai_clients import text

result = text.generate(
    "Reply with OK.",
    api="deepinfra",
)
print(result["output_text"])
~~~

### Explicit instruction and model
~~~python
result = text.generate(
    "Summarize this in one sentence.",
    instruction="Use plain English.",
    model="Qwen/Qwen3.5-0.8B",
    api="deepinfra",
)
~~~

### Provider-native options
~~~python
result = text.generate(
    "Reply with OK.",
    model="Qwen/Qwen3.5-0.8B",
    api="deepinfra",
)
~~~

## J. Pricing section
- Pricing snapshot date: `2026-04-25`.
- Pricing source: see the official references above plus provider usage fields or local fallback pricing tables in source.
- Pricing can change without a code change, especially for routers and model aliases.
- The wrapper omits premium tiers, tools, web/search, cache writes, and explicit reasoning by default to avoid surprise charges.

## K. Validation note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.