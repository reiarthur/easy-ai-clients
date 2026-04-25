# OpenRouter Text API Wrapper

## A. Overview
- The wrapper targets the OpenAI-compatible OpenRouter chat completions API.
- Raw generation endpoint: `POST https://openrouter.ai/api/v1/chat/completions`.
- Live catalog endpoint: `GET https://openrouter.ai/api/v1/models`.
- The project abstracts credential loading, message construction, parameter validation, streaming accumulation, result normalization, and local cost estimation where available.
- Provider-native kwargs are forwarded directly after validation; unsupported kwargs fail before credentials are read.

## B. Account and access
- Create account / console: https://openrouter.ai/
- API key docs: https://openrouter.ai/settings/keys
- Required environment variable: `OPENROUTER_API_KEY`.
- Access restrictions are provider-specific. The validation matrix records account, tier, route, overload, and not-callable blockers observed in this account.

## C. Official references
- https://openrouter.ai/docs/api-reference/chat-completion
- https://openrouter.ai/docs/api-reference/list-available-models
- https://openrouter.ai/docs/api-reference/get-a-generation
- https://openrouter.ai/pricing

## D. Wrapper behavior summary
- Public function signature: `generate(input_text, instruction=None, model='openai/gpt-oss-20b:free', **kwargs)`.
- Current default model: `openai/gpt-oss-20b:free`.
- Default selection date: `2026-04-25`.
- Default selection source: live provider catalog, official pricing/model documentation, and real smoke validation in `validacao_text_apis_2026-04-25`.
- Tie-break reasoning: openai/gpt-oss-20b:free is a free, callable, general text route in the OpenRouter catalog snapshot.
- Lowest-cost default policy: the wrapper sends only required text fields plus provider-required minimal output caps, when required. It does not enable tools, web/search, cache writes, structured output, premium service tiers, provider plugins, or explicit reasoning by default.
- Parameter validation policy: every kwarg must appear in the provider's documented parameter set for this wrapper context. Otherwise `UnsupportedParameterError` identifies provider/API, model, invalid parameter, supported parameters, and whether the parameter is known elsewhere.
- Streaming policy: `stream=True` is consumed internally; callers still receive the same normalized final dictionary.
- Public return contract: `request_id`, `cost_source`, `cost_usd`, `input_text`, optional `instruction`, and `output_text`, in that order.

## E. Parameter reference
### `cache_control`
- What it is: Router/provider cache control. Omitted by default.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `frequency_penalty`
- What it is: Penalty for repeated tokens.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `image_config`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `logit_bias`
- What it is: Token bias map for OpenAI-compatible APIs.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `logprobs`
- What it is: Token log probability return option. May add payload size and latency.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_completion_tokens`
- What it is: OpenAI-compatible completion cap used by selected reasoning/chat models.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_tokens`
- What it is: Maximum generated tokens for chat-style APIs. Lower values reduce cost and latency.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `messages`
- What it is: Provider-native chat message list. If supplied, it replaces the wrapper-built system/user messages.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `metadata`
- What it is: Provider metadata object. It does not affect output but may affect storage/audit behavior.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `modalities`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `model`
- What it is: Provider model identifier. In this project it is exposed as the explicit `model` function argument; passing it again in kwargs is unnecessary.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `models`
- What it is: OpenRouter fallback model list.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `n`
- What it is: Number of choices. Defaults to provider behavior; values above one increase cost.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `parallel_tool_calls`
- What it is: Tool parallelism control for providers that expose it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `plugins`
- What it is: OpenRouter plugin configuration; omitted by default to avoid paid add-ons.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `presence_penalty`
- What it is: Penalty that encourages new topics.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `provider`
- What it is: Router provider policy object. Omitted by default so the router can choose the cheapest valid route.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `reasoning`
- What it is: Provider-native reasoning object. Omitted by default to avoid premium reasoning cost.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `response_format`
- What it is: Structured output / JSON mode configuration when supported by the model.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `route`
- What it is: OpenRouter route policy.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `seed`
- What it is: Best-effort deterministic seed where the provider supports it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `service_tier`
- What it is: Provider queue/pricing tier. Omitted by default to avoid premium routing.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `session_id`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stop`
- What it is: OpenAI-compatible stop strings.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream`
- What it is: When true, the wrapper accumulates provider streaming internally and still returns the public result dict.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream_options`
- What it is: OpenAI-compatible streaming options, forwarded only when the provider accepts them.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `temperature`
- What it is: Sampling randomness. Lower values improve determinism; some reasoning/default models reject it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tool_choice`
- What it is: Provider-native tool-selection policy.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tools`
- What it is: Provider-native tool definitions. Omitted by default because tools can add latency, token use, and external charges.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_logprobs`
- What it is: Number of top token log probabilities to return.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_p`
- What it is: Nucleus sampling control. Use instead of, not always together with, temperature when the provider restricts sampling.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `trace`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `usage`
- What it is: Router usage accounting request. OpenRouter and fal inject `{'include': True}` when absent so cost can be resolved.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `user`
- What it is: Provider user identifier.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `openrouter` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

## F. Model coverage
- Catalog snapshot date: `2026-04-25`.
- Relevant text/chat model count after scope filtering: `336` from raw catalog count `355`.
- Status values below come from real text-in/text-out calls unless the row is a parameter-cluster row.

| Model ID | Family | Validation result | Support status / blocker |
|---|---|---|---|
| openai/gpt-oss-20b:free | openai | passed | validated |
| openai/gpt-5.5-pro | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5.5 | openai | failed | upstream_provider_rejected_request |
| deepseek/deepseek-v4-pro | deepseek | failed | provider_rate_limit_or_overload |
| deepseek/deepseek-v4-flash | deepseek | failed | provider_rate_limit_or_overload |
| inclusionai/ling-2.6-1t:free | inclusionai | passed | validated |
| tencent/hy3-preview:free | tencent | passed | validated |
| xiaomi/mimo-v2.5-pro | xiaomi | passed | validated |
| xiaomi/mimo-v2.5 | xiaomi | passed | validated |
| inclusionai/ling-2.6-flash:free | inclusionai | passed | validated |
| ~anthropic/claude-opus-latest | ~anthropic | passed | validated |
| openrouter/pareto-code | openrouter | passed | validated |
| moonshotai/kimi-k2.6 | moonshotai | passed | validated |
| anthropic/claude-opus-4.7 | anthropic | passed | validated |
| anthropic/claude-opus-4.6-fast | anthropic | passed | validated |
| z-ai/glm-5.1 | z-ai | passed | validated |
| google/gemma-4-26b-a4b-it:free | google | failed | provider_rate_limit_or_overload |
| google/gemma-4-26b-a4b-it | google | passed | validated |
| google/gemma-4-31b-it:free | google | passed | validated |
| google/gemma-4-31b-it | google | passed | validated |
| qwen/qwen3.6-plus | qwen | passed | validated |
| z-ai/glm-5v-turbo | z-ai | passed | validated |
| arcee-ai/trinity-large-thinking | arcee-ai | passed | validated |
| x-ai/grok-4.20 | x-ai | passed | validated |
| kwaipilot/kat-coder-pro-v2 | kwaipilot | passed | validated |
| rekaai/reka-edge | rekaai | passed | validated |
| xiaomi/mimo-v2-omni | xiaomi | passed | validated |
| xiaomi/mimo-v2-pro | xiaomi | passed | validated |
| minimax/minimax-m2.7 | minimax | passed | validated |
| openai/gpt-5.4-nano | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5.4-mini | openai | failed | upstream_provider_rejected_request |
| mistralai/mistral-small-2603 | mistralai | passed | validated |
| z-ai/glm-5-turbo | z-ai | passed | validated |
| nvidia/nemotron-3-super-120b-a12b:free | nvidia | passed | validated |
| nvidia/nemotron-3-super-120b-a12b | nvidia | passed | validated |
| bytedance-seed/seed-2.0-lite | bytedance-seed | passed | validated |
| qwen/qwen3.5-9b | qwen | passed | validated |
| openai/gpt-5.4-pro | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5.4 | openai | failed | upstream_provider_rejected_request |
| inception/mercury-2 | inception | passed | validated |
| openai/gpt-5.3-chat | openai | failed | upstream_provider_rejected_request |
| google/gemini-3.1-flash-lite-preview | google | passed | validated |
| bytedance-seed/seed-2.0-mini | bytedance-seed | passed | validated |
| qwen/qwen3.5-35b-a3b | qwen | passed | validated |
| qwen/qwen3.5-27b | qwen | passed | validated |
| qwen/qwen3.5-122b-a10b | qwen | passed | validated |
| qwen/qwen3.5-flash-02-23 | qwen | passed | validated |
| liquid/lfm-2-24b-a2b | liquid | passed | validated |
| google/gemini-3.1-pro-preview-customtools | google | passed | validated |
| openai/gpt-5.3-codex | openai | failed | upstream_provider_rejected_request |
| aion-labs/aion-2.0 | aion-labs | passed | validated |
| google/gemini-3.1-pro-preview | google | passed | validated |
| anthropic/claude-sonnet-4.6 | anthropic | passed | validated |
| qwen/qwen3.5-plus-02-15 | qwen | passed | validated |
| qwen/qwen3.5-397b-a17b | qwen | passed | validated |
| minimax/minimax-m2.5:free | minimax | passed | validated |
| minimax/minimax-m2.5 | minimax | passed | validated |
| z-ai/glm-5 | z-ai | passed | validated |
| qwen/qwen3-max-thinking | qwen | passed | validated |
| anthropic/claude-opus-4.6 | anthropic | passed | validated |
| qwen/qwen3-coder-next | qwen | passed | validated |
| openrouter/free | openrouter | passed | validated |
| stepfun/step-3.5-flash | stepfun | passed | validated |
| arcee-ai/trinity-large-preview | arcee-ai | passed | validated |
| moonshotai/kimi-k2.5 | moonshotai | passed | validated |
| upstage/solar-pro-3 | upstage | passed | validated |
| minimax/minimax-m2-her | minimax | passed | validated |
| writer/palmyra-x5 | writer | passed | validated |
| liquid/lfm-2.5-1.2b-thinking:free | liquid | passed | validated |
| liquid/lfm-2.5-1.2b-instruct:free | liquid | passed | validated |
| z-ai/glm-4.7-flash | z-ai | passed | validated |
| openai/gpt-5.2-codex | openai | failed | upstream_provider_rejected_request |
| allenai/olmo-3.1-32b-instruct | allenai | passed | validated |
| bytedance-seed/seed-1.6-flash | bytedance-seed | passed | validated |
| bytedance-seed/seed-1.6 | bytedance-seed | passed | validated |
| minimax/minimax-m2.1 | minimax | passed | validated |
| z-ai/glm-4.7 | z-ai | passed | validated |
| google/gemini-3-flash-preview | google | passed | validated |
| xiaomi/mimo-v2-flash | xiaomi | passed | validated |
| nvidia/nemotron-3-nano-30b-a3b:free | nvidia | passed | validated |
| nvidia/nemotron-3-nano-30b-a3b | nvidia | passed | validated |
| openai/gpt-5.2-chat | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5.2-pro | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5.2 | openai | failed | upstream_provider_rejected_request |
| mistralai/devstral-2512 | mistralai | passed | validated |
| relace/relace-search | relace | passed | validated |
| z-ai/glm-4.6v | z-ai | passed | validated |
| nex-agi/deepseek-v3.1-nex-n1 | nex-agi | passed | validated |
| essentialai/rnj-1-instruct | essentialai | passed | validated |
| openrouter/bodybuilder | openrouter | passed | validated |
| openai/gpt-5.1-codex-max | openai | failed | upstream_provider_rejected_request |
| amazon/nova-2-lite-v1 | amazon | passed | validated |
| mistralai/ministral-14b-2512 | mistralai | passed | validated |
| mistralai/ministral-8b-2512 | mistralai | passed | validated |
| mistralai/ministral-3b-2512 | mistralai | passed | validated |
| mistralai/mistral-large-2512 | mistralai | passed | validated |
| arcee-ai/trinity-mini | arcee-ai | passed | validated |
| deepseek/deepseek-v3.2-speciale | deepseek | passed | validated |
| deepseek/deepseek-v3.2 | deepseek | passed | validated |
| prime-intellect/intellect-3 | prime-intellect | passed | validated |
| anthropic/claude-opus-4.5 | anthropic | passed | validated |
| allenai/olmo-3-32b-think | allenai | failed | catalog_listed_but_not_callable_in_endpoint |
| x-ai/grok-4.1-fast | x-ai | passed | validated |
| deepcogito/cogito-v2.1-671b | deepcogito | passed | validated |
| openai/gpt-5.1 | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5.1-chat | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5.1-codex | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5.1-codex-mini | openai | failed | upstream_provider_rejected_request |
| moonshotai/kimi-k2-thinking | moonshotai | passed | validated |
| amazon/nova-premier-v1 | amazon | passed | validated |
| perplexity/sonar-pro-search | perplexity | passed | validated |
| mistralai/voxtral-small-24b-2507 | mistralai | passed | validated |
| nvidia/nemotron-nano-12b-v2-vl:free | nvidia | passed | validated |
| nvidia/nemotron-nano-12b-v2-vl | nvidia | passed | validated |
| minimax/minimax-m2 | minimax | passed | validated |
| qwen/qwen3-vl-32b-instruct | qwen | passed | validated |
| ibm-granite/granite-4.0-h-micro | ibm-granite | passed | validated |
| anthropic/claude-haiku-4.5 | anthropic | passed | validated |
| qwen/qwen3-vl-8b-thinking | qwen | passed | validated |
| qwen/qwen3-vl-8b-instruct | qwen | passed | validated |
| nvidia/llama-3.3-nemotron-super-49b-v1.5 | nvidia | passed | validated |
| baidu/ernie-4.5-21b-a3b-thinking | baidu | failed | provider_internal_error |
| qwen/qwen3-vl-30b-a3b-thinking | qwen | passed | validated |
| qwen/qwen3-vl-30b-a3b-instruct | qwen | passed | validated |
| openai/gpt-5-pro | openai | failed | upstream_provider_rejected_request |
| z-ai/glm-4.6 | z-ai | passed | validated |
| anthropic/claude-sonnet-4.5 | anthropic | passed | validated |
| deepseek/deepseek-v3.2-exp | deepseek | passed | validated |
| thedrummer/cydonia-24b-v4.1 | thedrummer | passed | validated |
| relace/relace-apply-3 | relace | failed | upstream_provider_rejected_request |
| google/gemini-2.5-flash-lite-preview-09-2025 | google | passed | validated |
| qwen/qwen3-vl-235b-a22b-thinking | qwen | passed | validated |
| qwen/qwen3-vl-235b-a22b-instruct | qwen | passed | validated |
| qwen/qwen3-max | qwen | passed | validated |
| qwen/qwen3-coder-plus | qwen | passed | validated |
| openai/gpt-5-codex | openai | failed | upstream_provider_rejected_request |
| deepseek/deepseek-v3.1-terminus | deepseek | passed | validated |
| x-ai/grok-4-fast | x-ai | passed | validated |
| alibaba/tongyi-deepresearch-30b-a3b | alibaba | passed | validated |
| qwen/qwen3-coder-flash | qwen | passed | validated |
| qwen/qwen3-next-80b-a3b-thinking | qwen | passed | validated |
| qwen/qwen3-next-80b-a3b-instruct:free | qwen | failed | provider_rate_limit_or_overload |
| qwen/qwen3-next-80b-a3b-instruct | qwen | passed | validated |
| qwen/qwen-plus-2025-07-28:thinking | qwen | passed | validated |
| qwen/qwen-plus-2025-07-28 | qwen | passed | validated |
| nvidia/nemotron-nano-9b-v2:free | nvidia | passed | validated |
| nvidia/nemotron-nano-9b-v2 | nvidia | passed | validated |
| moonshotai/kimi-k2-0905 | moonshotai | passed | validated |
| qwen/qwen3-30b-a3b-thinking-2507 | qwen | passed | validated |
| x-ai/grok-code-fast-1 | x-ai | passed | validated |
| nousresearch/hermes-4-70b | nousresearch | passed | validated |
| nousresearch/hermes-4-405b | nousresearch | passed | validated |
| deepseek/deepseek-chat-v3.1 | deepseek | passed | validated |
| mistralai/mistral-medium-3.1 | mistralai | passed | validated |
| baidu/ernie-4.5-21b-a3b | baidu | failed | provider_rate_limit_or_overload |
| baidu/ernie-4.5-vl-28b-a3b | baidu | failed | provider_rate_limit_or_overload |
| z-ai/glm-4.5v | z-ai | passed | validated |
| ai21/jamba-large-1.7 | ai21 | passed | validated |
| openai/gpt-5-chat | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5 | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5-mini | openai | failed | upstream_provider_rejected_request |
| openai/gpt-5-nano | openai | failed | upstream_provider_rejected_request |
| openai/gpt-oss-120b:free | openai | passed | validated |
| openai/gpt-oss-120b | openai | passed | validated |
| openai/gpt-oss-20b | openai | passed | validated |
| anthropic/claude-opus-4.1 | anthropic | passed | validated |
| mistralai/codestral-2508 | mistralai | passed | validated |
| qwen/qwen3-coder-30b-a3b-instruct | qwen | passed | validated |
| qwen/qwen3-30b-a3b-instruct-2507 | qwen | passed | validated |
| z-ai/glm-4.5 | z-ai | passed | validated |
| z-ai/glm-4.5-air:free | z-ai | failed | provider_rate_limit_or_overload |
| z-ai/glm-4.5-air | z-ai | passed | validated |
| qwen/qwen3-235b-a22b-thinking-2507 | qwen | passed | validated |
| z-ai/glm-4-32b | z-ai | passed | validated |
| qwen/qwen3-coder:free | qwen | failed | provider_rate_limit_or_overload |
| qwen/qwen3-coder | qwen | passed | validated |
| bytedance/ui-tars-1.5-7b | bytedance | passed | validated |
| google/gemini-2.5-flash-lite | google | passed | validated |
| qwen/qwen3-235b-a22b-2507 | qwen | passed | validated |
| switchpoint/router | switchpoint | passed | validated |
| moonshotai/kimi-k2 | moonshotai | passed | validated |
| mistralai/devstral-medium | mistralai | passed | validated |
| mistralai/devstral-small | mistralai | passed | validated |
| cognitivecomputations/dolphin-mistral-24b-venice-edition:free | cognitivecomputations | failed | provider_rate_limit_or_overload |
| x-ai/grok-4 | x-ai | passed | validated |
| google/gemma-3n-e2b-it:free | google | failed | provider_rate_limit_or_overload |
| tencent/hunyuan-a13b-instruct | tencent | passed | validated |
| tngtech/deepseek-r1t2-chimera | tngtech | passed | validated |
| morph/morph-v3-large | morph | passed | validated |
| morph/morph-v3-fast | morph | passed | validated |
| baidu/ernie-4.5-vl-424b-a47b | baidu | passed | validated |
| baidu/ernie-4.5-300b-a47b | baidu | passed | validated |
| mistralai/mistral-small-3.2-24b-instruct | mistralai | passed | validated |
| minimax/minimax-m1 | minimax | passed | validated |
| google/gemini-2.5-flash | google | passed | validated |
| google/gemini-2.5-pro | google | passed | validated |
| openai/o3-pro | openai | failed | upstream_provider_rejected_request |
| x-ai/grok-3-mini | x-ai | passed | validated |
| x-ai/grok-3 | x-ai | passed | validated |
| google/gemini-2.5-pro-preview | google | passed | validated |
| deepseek/deepseek-r1-0528 | deepseek | passed | validated |
| anthropic/claude-opus-4 | anthropic | passed | validated |
| anthropic/claude-sonnet-4 | anthropic | passed | validated |
| google/gemma-3n-e4b-it:free | google | passed | validated |
| google/gemma-3n-e4b-it | google | passed | validated |
| mistralai/mistral-medium-3 | mistralai | passed | validated |
| google/gemini-2.5-pro-preview-05-06 | google | passed | validated |
| arcee-ai/spotlight | arcee-ai | failed | provider_temporarily_unavailable |
| arcee-ai/maestro-reasoning | arcee-ai | failed | provider_temporarily_unavailable |
| arcee-ai/virtuoso-large | arcee-ai | failed | provider_temporarily_unavailable |
| arcee-ai/coder-large | arcee-ai | failed | provider_temporarily_unavailable |
| meta-llama/llama-guard-4-12b | meta-llama | passed | validated |
| qwen/qwen3-30b-a3b | qwen | passed | validated |
| qwen/qwen3-8b | qwen | passed | validated |
| qwen/qwen3-14b | qwen | passed | validated |
| qwen/qwen3-32b | qwen | passed | validated |
| qwen/qwen3-235b-a22b | qwen | passed | validated |
| openai/o4-mini-high | openai | failed | upstream_provider_rejected_request |
| openai/o3 | openai | failed | upstream_provider_rejected_request |
| openai/o4-mini | openai | failed | upstream_provider_rejected_request |
| openai/gpt-4.1 | openai | failed | upstream_provider_rejected_request |
| openai/gpt-4.1-mini | openai | failed | upstream_provider_rejected_request |
| openai/gpt-4.1-nano | openai | failed | upstream_provider_rejected_request |
| alfredpros/codellama-7b-instruct-solidity | alfredpros | failed | account_or_tier_access_required |
| x-ai/grok-3-mini-beta | x-ai | passed | validated |
| x-ai/grok-3-beta | x-ai | passed | validated |
| meta-llama/llama-4-maverick | meta-llama | passed | validated |
| meta-llama/llama-4-scout | meta-llama | passed | validated |
| deepseek/deepseek-chat-v3-0324 | deepseek | passed | validated |
| openai/o1-pro | openai | failed | upstream_provider_rejected_request |
| mistralai/mistral-small-3.1-24b-instruct | mistralai | passed | validated |
| google/gemma-3-4b-it:free | google | passed | validated |
| google/gemma-3-4b-it | google | passed | validated |
| google/gemma-3-12b-it:free | google | failed | provider_rate_limit_or_overload |
| google/gemma-3-12b-it | google | passed | validated |
| cohere/command-a | cohere | passed | validated |
| openai/gpt-4o-mini-search-preview | openai | passed | validated |
| openai/gpt-4o-search-preview | openai | passed | validated |
| rekaai/reka-flash-3 | rekaai | passed | validated |
| google/gemma-3-27b-it:free | google | failed | provider_rate_limit_or_overload |
| google/gemma-3-27b-it | google | passed | validated |
| thedrummer/skyfall-36b-v2 | thedrummer | passed | validated |
| perplexity/sonar-reasoning-pro | perplexity | passed | validated |
| perplexity/sonar-pro | perplexity | passed | validated |
| qwen/qwq-32b | qwen | passed | validated |
| google/gemini-2.0-flash-lite-001 | google | passed | validated |
| anthropic/claude-3.7-sonnet | anthropic | passed | validated |
| anthropic/claude-3.7-sonnet:thinking | anthropic | passed | validated |
| mistralai/mistral-saba | mistralai | passed | validated |
| meta-llama/llama-guard-3-8b | meta-llama | failed | upstream_provider_rejected_request |
| openai/o3-mini-high | openai | failed | upstream_provider_rejected_request |
| google/gemini-2.0-flash-001 | google | passed | validated |
| qwen/qwen-vl-plus | qwen | passed | validated |
| aion-labs/aion-1.0 | aion-labs | passed | validated |
| aion-labs/aion-1.0-mini | aion-labs | passed | validated |
| aion-labs/aion-rp-llama-3.1-8b | aion-labs | passed | validated |
| qwen/qwen-vl-max | qwen | passed | validated |
| qwen/qwen-turbo | qwen | passed | validated |
| qwen/qwen2.5-vl-72b-instruct | qwen | passed | validated |
| qwen/qwen-plus | qwen | passed | validated |
| qwen/qwen-max | qwen | passed | validated |
| openai/o3-mini | openai | failed | upstream_provider_rejected_request |
| mistralai/mistral-small-24b-instruct-2501 | mistralai | passed | validated |
| deepseek/deepseek-r1-distill-qwen-32b | deepseek | passed | validated |
| perplexity/sonar | perplexity | passed | validated |
| deepseek/deepseek-r1-distill-llama-70b | deepseek | passed | validated |
| deepseek/deepseek-r1 | deepseek | passed | validated |
| minimax/minimax-01 | minimax | passed | validated |
| microsoft/phi-4 | microsoft | passed | validated |
| sao10k/l3.1-70b-hanami-x1 | sao10k | passed | validated |
| deepseek/deepseek-chat | deepseek | passed | validated |
| sao10k/l3.3-euryale-70b | sao10k | passed | validated |
| openai/o1 | openai | failed | upstream_provider_rejected_request |
| cohere/command-r7b-12-2024 | cohere | passed | validated |
| meta-llama/llama-3.3-70b-instruct:free | meta-llama | failed | provider_rate_limit_or_overload |
| meta-llama/llama-3.3-70b-instruct | meta-llama | passed | validated |
| amazon/nova-lite-v1 | amazon | passed | validated |
| amazon/nova-micro-v1 | amazon | passed | validated |
| amazon/nova-pro-v1 | amazon | passed | validated |
| openai/gpt-4o-2024-11-20 | openai | passed | validated |
| mistralai/mistral-large-2411 | mistralai | passed | validated |
| mistralai/mistral-large-2407 | mistralai | passed | validated |
| mistralai/pixtral-large-2411 | mistralai | passed | validated |
| qwen/qwen-2.5-coder-32b-instruct | qwen | passed | validated |
| thedrummer/unslopnemo-12b | thedrummer | passed | validated |
| anthropic/claude-3.5-haiku | anthropic | passed | validated |
| anthracite-org/magnum-v4-72b | anthracite-org | passed | validated |
| qwen/qwen-2.5-7b-instruct | qwen | passed | validated |
| nvidia/llama-3.1-nemotron-70b-instruct | nvidia | passed | validated |
| inflection/inflection-3-pi | inflection | passed | validated |
| inflection/inflection-3-productivity | inflection | passed | validated |
| thedrummer/rocinante-12b | thedrummer | passed | validated |
| meta-llama/llama-3.2-1b-instruct | meta-llama | passed | validated |
| meta-llama/llama-3.2-11b-vision-instruct | meta-llama | passed | validated |
| meta-llama/llama-3.2-3b-instruct:free | meta-llama | failed | provider_rate_limit_or_overload |
| meta-llama/llama-3.2-3b-instruct | meta-llama | passed | validated |
| qwen/qwen-2.5-72b-instruct | qwen | passed | validated |
| cohere/command-r-08-2024 | cohere | passed | validated |
| cohere/command-r-plus-08-2024 | cohere | passed | validated |
| sao10k/l3.1-euryale-70b | sao10k | passed | validated |
| nousresearch/hermes-3-llama-3.1-70b | nousresearch | passed | validated |
| nousresearch/hermes-3-llama-3.1-405b:free | nousresearch | failed | provider_rate_limit_or_overload |
| nousresearch/hermes-3-llama-3.1-405b | nousresearch | passed | validated |
| sao10k/l3-lunaris-8b | sao10k | passed | validated |
| openai/gpt-4o-2024-08-06 | openai | passed | validated |
| meta-llama/llama-3.1-70b-instruct | meta-llama | passed | validated |
| meta-llama/llama-3.1-8b-instruct | meta-llama | passed | validated |
| mistralai/mistral-nemo | mistralai | passed | validated |
| openai/gpt-4o-mini-2024-07-18 | openai | passed | validated |
| openai/gpt-4o-mini | openai | passed | validated |
| google/gemma-2-27b-it | google | passed | validated |
| sao10k/l3-euryale-70b | sao10k | passed | validated |
| nousresearch/hermes-2-pro-llama-3-8b | nousresearch | passed | validated |
| openai/gpt-4o-2024-05-13 | openai | passed | validated |
| openai/gpt-4o | openai | passed | validated |
| meta-llama/llama-3-70b-instruct | meta-llama | passed | validated |
| meta-llama/llama-3-8b-instruct | meta-llama | passed | validated |
| mistralai/mixtral-8x22b-instruct | mistralai | passed | validated |
| microsoft/wizardlm-2-8x22b | microsoft | passed | validated |
| openai/gpt-4-turbo | openai | passed | validated |
| anthropic/claude-3-haiku | anthropic | passed | validated |
| mistralai/mistral-large | mistralai | passed | validated |
| openai/gpt-3.5-turbo-0613 | openai | passed | validated |
| openai/gpt-4-turbo-preview | openai | failed | catalog_listed_but_not_callable_in_endpoint |
| mistralai/mixtral-8x7b-instruct | mistralai | passed | validated |
| alpindale/goliath-120b | alpindale | passed | validated |
| openrouter/auto | openrouter | passed | validated |
| openai/gpt-4-1106-preview | openai | failed | upstream_provider_rejected_request |
| mistralai/mistral-7b-instruct-v0.1 | mistralai | passed | validated |
| openai/gpt-3.5-turbo-16k | openai | passed | validated |
| mancer/weaver | mancer | passed | validated |
| undi95/remm-slerp-l2-13b | undi95 | passed | validated |
| gryphe/mythomax-l2-13b | gryphe | passed | validated |
| openai/gpt-3.5-turbo | openai | passed | validated |
| openai/gpt-4-0314 | openai | failed | catalog_listed_but_not_callable_in_endpoint |
| openai/gpt-4 | openai | passed | validated |

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
from text.apis import openrouter

result = openrouter.generate("Reply with OK.")
print(result["output_text"])
```

### Explicit instruction
```python
result = openrouter.generate(
    "Summarize this in one sentence.",
    instruction="Use plain English.",
)
```

### Explicit model
```python
result = openrouter.generate(
    "Reply with OK.",
    model="openai/gpt-oss-20b:free",
)
```

### Full options for the primary surface
```python
result = openrouter.generate("Reply with OK.", model="openai/gpt-oss-20b:free", max_tokens=64, temperature=0, top_p=1, stop=["END"], stream=True)
```

## J. Pricing section
- Pricing snapshot date: `2026-04-25`.
- Pricing source: see the official references above and the validation artifact `validacao_text_apis_2026-04-25/catalog_openrouter.json`.
- Pricing can change without a code change, especially for routers and model aliases.
- The wrapper omits premium tiers, tools, web/search, cache writes, and explicit reasoning by default to avoid surprise charges.

## K. Validation note
- Real validation artifact: `tests/artefatos_testes/validacao_text_apis_2026-04-25/validation_matrix.md`.
- Provider result counts in the final matrix: `{'passed': 280, 'failed': 61}`.
- Failure blocker counts: `{'upstream_provider_rejected_request': 37, 'provider_rate_limit_or_overload': 15, 'catalog_listed_but_not_callable_in_endpoint': 3, 'provider_internal_error': 1, 'provider_temporarily_unavailable': 4, 'account_or_tier_access_required': 1}`.
- Failed rows are not claimed as supported; they are documented as provider, route, account, or model restrictions observed during validation.
