# Fireworks AI Text API Wrapper

## A. Overview
- The wrapper targets the OpenAI-compatible Fireworks chat completions API.
- Raw generation endpoint: `POST https://api.fireworks.ai/inference/v1/chat/completions`.
- Live catalog endpoint: `GET https://api.fireworks.ai/inference/v1/models`.
- The project abstracts credential loading, message construction, parameter validation, streaming accumulation, result normalization, and local cost estimation where available.
- Provider-native kwargs are forwarded directly; documented parameters are reference metadata, and provider rejections are returned through the normalized public error shape.

## B. Account and access
- Create account / console: https://fireworks.ai/
- API key docs: https://fireworks.ai/account/api-keys
- Required environment variable: `FIREWORKS_API_KEY`.
- Access restrictions are provider-specific. The validation matrix records account, tier, route, overload, and not-callable blockers observed in this account.

## C. Official references
- https://fireworks.ai/docs/api-reference/post-chatcompletions
- https://docs.fireworks.ai/guides/querying-text-models
- https://fireworks.ai/pricing
- https://docs.fireworks.ai/updates/changelog

## D. Wrapper behavior summary
- Public function signature: `generate(input_text, instruction=None, model='accounts/fireworks/models/gpt-oss-20b', **kwargs)`.
- Current default model: `accounts/fireworks/models/gpt-oss-20b`.
- Default selection date: `2026-04-25`.
- Default selection source: live provider catalog, official pricing/model documentation, and source defaults.
- Tie-break reasoning: accounts/fireworks/models/gpt-oss-20b is the lowest-cost serverless text model validated from Fireworks pricing and catalog.
- Lowest-cost default policy: the wrapper sends only required text fields plus provider-required minimal output caps, when required. It does not enable tools, web/search, cache writes, structured output, premium service tiers, provider plugins, or explicit reasoning by default.
- Parameter validation policy: every kwarg must appear in the provider's documented parameter set for this wrapper context. Otherwise `UnsupportedParameterError` identifies provider/API, model, invalid parameter, supported parameters, and whether the parameter is known elsewhere.
- Streaming policy: `stream=True` is consumed internally; callers still receive the same normalized final dictionary.
- Public return contract: `request_id`, `cost_source`, `cost_usd`, `input_text`, optional `instruction`, and `output_text`, in that order.

## E. Parameter reference
### `context_length_exceeded_behavior`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `echo`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `echo_last`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `frequency_penalty`
- What it is: Penalty for repeated tokens.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `function_call`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `functions`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `ignore_eos`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `logit_bias`
- What it is: Token bias map for OpenAI-compatible APIs.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `logprobs`
- What it is: Token log probability return option. May add payload size and latency.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_completion_tokens`
- What it is: OpenAI-compatible completion cap used by selected reasoning/chat models.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_tokens`
- What it is: Maximum generated tokens for chat-style APIs. Lower values reduce cost and latency.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `messages`
- What it is: Provider-native chat message list. If supplied, it replaces the wrapper-built system/user messages.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `metadata`
- What it is: Provider metadata object. It does not affect output but may affect storage/audit behavior.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `min_p`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `mirostat_lr`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `mirostat_target`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `model`
- What it is: Provider model identifier. In this project it is exposed as the explicit `model` function argument; passing it again in kwargs is unnecessary.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `n`
- What it is: Number of choices. Defaults to provider behavior; values above one increase cost.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `parallel_tool_calls`
- What it is: Tool parallelism control for providers that expose it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `perf_metrics_in_response`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `prediction`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `presence_penalty`
- What it is: Penalty that encourages new topics.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `prompt_cache_isolation_key`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `prompt_cache_key`
- What it is: Cache key for providers that expose prompt caching.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `prompt_truncate_len`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `raw_output`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `reasoning_effort`
- What it is: Provider-native reasoning effort selector for compatible model families.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `reasoning_history`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `repetition_penalty`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `response_format`
- What it is: Structured output / JSON mode configuration when supported by the model.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `return_token_ids`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `safe_tokenization`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `seed`
- What it is: Best-effort deterministic seed where the provider supports it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `service_tier`
- What it is: Provider queue/pricing tier. Omitted by default to avoid premium routing.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `speculation`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stop`
- What it is: OpenAI-compatible stop strings.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream`
- What it is: When true, the wrapper accumulates provider streaming internally and still returns the public result dict.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream_options`
- What it is: OpenAI-compatible streaming options, forwarded only when the provider accepts them.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `temperature`
- What it is: Sampling randomness. Lower values improve determinism; some reasoning/default models reject it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `thinking`
- What it is: Provider-native thinking configuration for Anthropic/DeepSeek/Fireworks-compatible models.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tool_choice`
- What it is: Provider-native tool-selection policy.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tools`
- What it is: Provider-native tool definitions. Omitted by default because tools can add latency, token use, and external charges.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_k`
- What it is: Provider-specific sampling cutoff. Higher values may increase diversity.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_logprobs`
- What it is: Number of top token log probabilities to return.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_p`
- What it is: Nucleus sampling control. Use instead of, not always together with, temperature when the provider restricts sampling.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `typical_p`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `user`
- What it is: Provider user identifier.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `fireworks` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

## F. Model coverage
- Catalog snapshot date: `2026-04-25`.
- Relevant text/chat model count after scope filtering: `5` from raw catalog count `7`.
- Status values below come from real text-in/text-out calls unless the row is a parameter-cluster row.

| Model ID | Family | Validation result | Support status / blocker |
|---|---|---|---|
| accounts/fireworks/models/gpt-oss-20b | accounts | passed | validated |
| accounts/fireworks/models/kimi-k2p5 | accounts | passed | validated |
| accounts/fireworks/models/kimi-k2p6 | accounts | passed | validated |
| accounts/fireworks/models/glm-5p1 | accounts | passed | validated |
| accounts/fireworks/models/minimax-m2p7 | accounts | passed | validated |
| accounts/fireworks/models/glm-5 | accounts | passed | validated |

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
    api="fireworks",
)
print(result["output_text"])
~~~

### Explicit instruction and model
~~~python
result = text.generate(
    "Summarize this in one sentence.",
    instruction="Use plain English.",
    model="accounts/fireworks/models/gpt-oss-20b",
    api="fireworks",
)
~~~

### Provider-native options
~~~python
result = text.generate(
    "Reply with OK.",
    model="accounts/fireworks/models/gpt-oss-20b",
    api="fireworks",
)
~~~

## J. Pricing section
- Pricing snapshot date: `2026-04-25`.
- Pricing source: see the official references above plus provider usage fields or local fallback pricing tables in source.
- Pricing can change without a code change, especially for routers and model aliases.
- The wrapper omits premium tiers, tools, web/search, cache writes, and explicit reasoning by default to avoid surprise charges.

## K. Validation note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.