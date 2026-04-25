# Together AI Text API Wrapper

## A. Overview
- The wrapper targets the OpenAI-compatible Together chat completions API.
- Raw generation endpoint: `POST https://api.together.xyz/v1/chat/completions`.
- Live catalog endpoint: `GET https://api.together.xyz/v1/models`.
- The project abstracts credential loading, message construction, parameter validation, streaming accumulation, result normalization, and local cost estimation where available.
- Provider-native kwargs are forwarded directly after validation; unsupported kwargs fail before credentials are read.

## B. Account and access
- Create account / console: https://api.together.ai/
- API key docs: https://docs.together.ai/docs/api-keys-authentication
- Required environment variable: `TOGETHER_API_KEY`.
- Access restrictions are provider-specific. The validation matrix records account, tier, route, overload, and not-callable blockers observed in this account.

## C. Official references
- https://docs.together.ai/reference/
- https://docs.together.ai/docs/serverless-models
- https://www.together.ai/pricing
- https://docs.together.ai/docs/deprecations

## D. Wrapper behavior summary
- Public function signature: `generate(input_text, instruction=None, model='google/gemma-3n-E4B-it', **kwargs)`.
- Current default model: `google/gemma-3n-E4B-it`.
- Default selection date: `2026-04-25`.
- Default selection source: live provider catalog, official pricing/model documentation, and source defaults.
- Tie-break reasoning: google/gemma-3n-E4B-it was the lowest-cost chat model that returned text in the validated Together catalog.
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
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `frequency_penalty`
- What it is: Penalty for repeated tokens.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `logit_bias`
- What it is: Token bias map for OpenAI-compatible APIs.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `logprobs`
- What it is: Token log probability return option. May add payload size and latency.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_completion_tokens`
- What it is: OpenAI-compatible completion cap used by selected reasoning/chat models.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_tokens`
- What it is: Maximum generated tokens for chat-style APIs. Lower values reduce cost and latency.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `messages`
- What it is: Provider-native chat message list. If supplied, it replaces the wrapper-built system/user messages.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `metadata`
- What it is: Provider metadata object. It does not affect output but may affect storage/audit behavior.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `min_p`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `model`
- What it is: Provider model identifier. In this project it is exposed as the explicit `model` function argument; passing it again in kwargs is unnecessary.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `n`
- What it is: Number of choices. Defaults to provider behavior; values above one increase cost.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `parallel_tool_calls`
- What it is: Tool parallelism control for providers that expose it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `presence_penalty`
- What it is: Penalty that encourages new topics.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `reasoning_effort`
- What it is: Provider-native reasoning effort selector for compatible model families.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `repetition_penalty`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `response_format`
- What it is: Structured output / JSON mode configuration when supported by the model.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `safety_model`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `seed`
- What it is: Best-effort deterministic seed where the provider supports it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `service_tier`
- What it is: Provider queue/pricing tier. Omitted by default to avoid premium routing.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stop`
- What it is: OpenAI-compatible stop strings.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream`
- What it is: When true, the wrapper accumulates provider streaming internally and still returns the public result dict.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream_options`
- What it is: OpenAI-compatible streaming options, forwarded only when the provider accepts them.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `temperature`
- What it is: Sampling randomness. Lower values improve determinism; some reasoning/default models reject it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tool_choice`
- What it is: Provider-native tool-selection policy.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tools`
- What it is: Provider-native tool definitions. Omitted by default because tools can add latency, token use, and external charges.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_k`
- What it is: Provider-specific sampling cutoff. Higher values may increase diversity.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_logprobs`
- What it is: Number of top token log probabilities to return.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_p`
- What it is: Nucleus sampling control. Use instead of, not always together with, temperature when the provider restricts sampling.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `user`
- What it is: Provider user identifier.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `together` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

## F. Model coverage
- Catalog snapshot date: `2026-04-25`.
- Relevant text/chat model count after scope filtering: `145` from raw catalog count `147`.
- Status values below come from real text-in/text-out calls unless the row is a parameter-cluster row.

| Model ID | Family | Validation result | Support status / blocker |
|---|---|---|---|
| google/gemma-3n-E4B-it | google | passed | validated |
| deepseek-ai/DeepSeek-V4-Pro | deepseek-ai | passed | validated |
| zai-org/GLM-5.1 | zai-org | passed | validated |
| moonshotai/Kimi-K2.6 | moonshotai | passed | validated |
| MiniMaxAI/MiniMax-M2.7 | MiniMaxAI | passed | validated |
| google/gemma-4-31B-it | google | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3.5-397B-A17B | Qwen | passed | validated |
| MiniMaxAI/MiniMax-M2.5 | MiniMaxAI | passed | validated |
| openai/gpt-oss-120b | openai | passed | validated |
| openai/gpt-oss-20b | openai | passed | validated |
| zai-org/GLM-5 | zai-org | passed | validated |
| moonshotai/Kimi-K2.5 | moonshotai | passed | validated |
| deepseek-ai/DeepSeek-R1 | deepseek-ai | passed | validated |
| deepseek-ai/DeepSeek-V3.1 | deepseek-ai | failed | provider_temporarily_unavailable |
| Qwen/Qwen3.5-9B | Qwen | passed | validated |
| Qwen/Qwen3-Coder-Next-FP8 | Qwen | passed | validated |
| Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8 | Qwen | passed | validated |
| Qwen/Qwen3-235B-A22B-Instruct-2507-tput | Qwen | passed | validated |
| Qwen/Qwen2.5-7B-Instruct-Turbo | Qwen | passed | validated |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | meta-llama | passed | validated |
| meta-llama/Meta-Llama-3-8B-Instruct-Lite | meta-llama | passed | validated |
| arize-ai/qwen-2-1.5b-instruct | arize-ai | passed | validated |
| LiquidAI/LFM2-24B-A2B | LiquidAI | passed | validated |
| essentialai/rnj-1-instruct | essentialai | passed | validated |
| deepcogito/cogito-v2-1-671b | deepcogito | passed | validated |
| mistralai/Mistral-Small-24B-Instruct-2501 | mistralai | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-VL-8B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| google/gemma-4-E4B-it | google | failed | model_parameter_or_payload_restriction |
| Hcompany/Holo3-35B-A3B | Hcompany | failed | model_parameter_or_payload_restriction |
| google/gemma-4-26B-A4B-it | google | failed | model_parameter_or_payload_restriction |
| moonshotai/Kimi-K2-Thinking | moonshotai | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-Coder-30B-A3B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo | meta-llama | failed | model_parameter_or_payload_restriction |
| zai-org/GLM-4.7 | zai-org | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-VL-32B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO | NousResearch | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-32B | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-Next-80B-A3B-Thinking | Qwen | failed | model_parameter_or_payload_restriction |
| google/gemma-2-9b-it | google | failed | model_parameter_or_payload_restriction |
| nim/meta/llama-3.1-70b-instruct | nim | failed | model_parameter_or_payload_restriction |
| nim/meta/llama-3.1-8b-instruct | nim | failed | model_parameter_or_payload_restriction |
| nim/nv-mistralai/mistral-nemo-12b-instruct | nim | failed | model_parameter_or_payload_restriction |
| nim/nvidia/llama-3.1-nemotron-70b-instruct | nim | failed | model_parameter_or_payload_restriction |
| deepcogito/cogito-v1-preview-llama-70B | deepcogito | failed | model_parameter_or_payload_restriction |
| deepcogito/cogito-v1-preview-llama-70B-Turbo | deepcogito | failed | model_parameter_or_payload_restriction |
| zai-org/GLM-5-FP4 | zai-org | failed | model_parameter_or_payload_restriction |
| deepcogito/cogito-v1-preview-llama-8B | deepcogito | failed | model_parameter_or_payload_restriction |
| MiniMaxAI/MiniMax-M2.5-FP4 | MiniMaxAI | failed | model_parameter_or_payload_restriction |
| deepcogito/cogito-v1-preview-qwen-14B | deepcogito | failed | model_parameter_or_payload_restriction |
| deepcogito/cogito-v1-preview-qwen-32B | deepcogito | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-R1-Distill-Llama-70B | deepseek-ai | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B | deepseek-ai | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-14B | deepseek-ai | failed | model_parameter_or_payload_restriction |
| google/gemma-3-4b-it | google | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-7B | deepseek-ai | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-V3-DE | deepseek-ai | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-V3.1-Base | deepseek-ai | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-V3.2-Exp | deepseek-ai | failed | model_parameter_or_payload_restriction |
| deepseek-ai/deepseek-coder-33b-instruct | deepseek-ai | failed | model_parameter_or_payload_restriction |
| meta-llama/Llama-3.2-1B | meta-llama | failed | model_parameter_or_payload_restriction |
| nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 | nvidia | failed | model_parameter_or_payload_restriction |
| zai-org/GLM-4.5-Air-FP8 | zai-org | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-Next-80B-A3B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| agentica-org/DeepCoder-14B-Preview | agentica-org | failed | model_parameter_or_payload_restriction |
| MiniMaxAI/MiniMax-M1-40k | MiniMaxAI | failed | model_parameter_or_payload_restriction |
| MiniMaxAI/MiniMax-M1-80k | MiniMaxAI | failed | model_parameter_or_payload_restriction |
| Qwen/QwQ-32B | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2-1.5B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-1.5B | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-1.5B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-14B | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-3B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-72B | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-7B | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-7B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-Coder-32B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-VL-72B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-0.6B | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-1.7B | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-235B-A22B-fp8 | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-8B | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-Next-80B-A3B-Instruct-FP8 | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-VL-235B-A22B-Instruct-FP8 | Qwen | failed | model_parameter_or_payload_restriction |
| google/gemma-3-27b-pt | google | failed | model_parameter_or_payload_restriction |
| meta-llama/Llama-2-7b-chat-hf | meta-llama | failed | model_parameter_or_payload_restriction |
| nim/meta/llama-3.2-90b-vision-instruct | nim | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3.5-397B-A17B-FP8 | Qwen | failed | model_parameter_or_payload_restriction |
| google/gemma-2b-it | google | failed | model_parameter_or_payload_restriction |
| mistralai/Magistral-Small-2506 | mistralai | failed | model_parameter_or_payload_restriction |
| mistralai/Mistral-7B-Instruct-v0.1 | mistralai | failed | model_parameter_or_payload_restriction |
| mistralai/Mistral-7B-v0.1 | mistralai | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-R1-Original | deepseek-ai | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-V3.1-Terminus | deepseek-ai | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-30B-A3B-Instruct-2507-Lora | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-4B-Instruct-2507 | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-8B-Lora | Qwen | failed | model_parameter_or_payload_restriction |
| meta-llama/Llama-3.1-405B | meta-llama | failed | model_parameter_or_payload_restriction |
| meta-llama/Meta-Llama-3.1-70B | meta-llama | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-V3.2 | deepseek-ai | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-V3-0324 | deepseek-ai | failed | model_parameter_or_payload_restriction |
| meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8 | meta-llama | failed | model_parameter_or_payload_restriction |
| deepseek-ai/DeepSeek-R1-0528 | deepseek-ai | passed | validated |
| meta-llama/Llama-4-Maverick-17B-128E | meta-llama | failed | model_parameter_or_payload_restriction |
| nim/mistralai/mixtral-8x22b-instruct-v01 | nim | failed | model_parameter_or_payload_restriction |
| togethercomputer/meta-llama-3.1-8B-Instruct-AWQ-INT4 | togethercomputer | failed | model_parameter_or_payload_restriction |
| zai-org/GLM-4.5V | zai-org | failed | model_parameter_or_payload_restriction |
| zai-org/GLM-4.6 | zai-org | failed | model_parameter_or_payload_restriction |
| meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo | meta-llama | failed | model_parameter_or_payload_restriction |
| MiniMaxAI/MiniMax-M2 | MiniMaxAI | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-14B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| google/gemma-4-E2B-it | google | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3.6-35B-A3B-FP8 | Qwen | failed | model_parameter_or_payload_restriction |
| nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16 | nvidia | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3.5-122B-A10B-FP8 | Qwen | failed | model_parameter_or_payload_restriction |
| meta-llama/Llama-3.1-405B-Instruct | meta-llama | failed | model_parameter_or_payload_restriction |
| meta-llama/Llama-3.2-1B-Instruct | meta-llama | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-30B-A3B | Qwen | failed | model_parameter_or_payload_restriction |
| google/gemma-3-1b-it | google | failed | model_parameter_or_payload_restriction |
| google/gemma-3-270m-it | google | failed | model_parameter_or_payload_restriction |
| meta-llama/Llama-4-Scout-17B-16E | meta-llama | failed | model_parameter_or_payload_restriction |
| meta-llama/Meta-Llama-3-70B-Instruct-Turbo | meta-llama | failed | model_parameter_or_payload_restriction |
| meta-llama/Meta-Llama-3-8B-Instruct | meta-llama | failed | model_parameter_or_payload_restriction |
| mistralai/Devstral-Small-2505 | mistralai | failed | model_parameter_or_payload_restriction |
| mistralai/Ministral-3-14B-Instruct-2512 | mistralai | failed | model_parameter_or_payload_restriction |
| mistralai/Mistral-7B-Instruct-v0.3 | mistralai | failed | model_parameter_or_payload_restriction |
| mistralai/Mixtral-8x22B-Instruct-v0.1 | mistralai | failed | model_parameter_or_payload_restriction |
| nim/meta/llama-3.2-11b-vision-instruct | nim | failed | model_parameter_or_payload_restriction |
| nim/meta/llama-3.3-70b-instruct | nim | failed | model_parameter_or_payload_restriction |
| nim/mistralai/mixtral-8x7b-instruct-v01 | nim | failed | model_parameter_or_payload_restriction |
| nvidia/Llama-3.1-Nemotron-70B-Instruct-HF | nvidia | failed | model_parameter_or_payload_restriction |
| nvidia/NVIDIA-Nemotron-Nano-9B-v2 | nvidia | failed | model_parameter_or_payload_restriction |
| sarvamai/sarvam-m | sarvamai | failed | model_parameter_or_payload_restriction |
| togethercomputer/EssentialAI-RNJ-1-Instruct | togethercomputer | failed | model_parameter_or_payload_restriction |
| mistralai/Mixtral-8x7B-Instruct-v0.1 | mistralai | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3-235B-A22B-Thinking-2507 | Qwen | failed | model_parameter_or_payload_restriction |
| nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 | nvidia | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-72B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2.5-72B-Instruct-Turbo | Qwen | failed | model_parameter_or_payload_restriction |
| nim/nvidia/llama-3.3-nemotron-super-49b-v1 | nim | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen2-VL-72B-Instruct | Qwen | failed | model_parameter_or_payload_restriction |
| google/gemma-2-27b-it | google | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3.5-9B-FP8 | Qwen | failed | model_parameter_or_payload_restriction |
| meta-llama/Llama-3-8b-chat-hf | meta-llama | failed | model_parameter_or_payload_restriction |
| meta-llama/Llama-4-Scout-17B-16E-Instruct | meta-llama | failed | model_parameter_or_payload_restriction |
| Qwen/Qwen3.5-35B-A3B | Qwen | failed | model_parameter_or_payload_restriction |

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
    api="together",
)
print(result["output_text"])
~~~

### Explicit instruction and model
~~~python
result = text.generate(
    "Summarize this in one sentence.",
    instruction="Use plain English.",
    model="google/gemma-3n-E4B-it",
    api="together",
)
~~~

### Provider-native options
~~~python
result = text.generate(
    "Reply with OK.",
    model="google/gemma-3n-E4B-it",
    api="together",
)
~~~

## J. Pricing section
- Pricing snapshot date: `2026-04-25`.
- Pricing source: see the official references above plus provider usage fields or local fallback pricing tables in source.
- Pricing can change without a code change, especially for routers and model aliases.
- The wrapper omits premium tiers, tools, web/search, cache writes, and explicit reasoning by default to avoid surprise charges.

## K. Validation note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.