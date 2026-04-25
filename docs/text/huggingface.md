# Hugging Face Inference Providers Text API Wrapper

## A. Overview
- The wrapper targets the OpenAI-compatible Hugging Face router chat completions API.
- Raw generation endpoint: `POST https://router.huggingface.co/v1/chat/completions`.
- Live catalog endpoint: `GET https://router.huggingface.co/v1/models`.
- The project abstracts credential loading, message construction, parameter validation, streaming accumulation, result normalization, and local cost estimation where available.
- Provider-native kwargs are forwarded directly after validation; unsupported kwargs fail before credentials are read.

## B. Account and access
- Create account / console: https://huggingface.co/join
- API key docs: https://huggingface.co/settings/tokens
- Required environment variable: `HUGGINGFACE_API_KEY`.
- Access restrictions are provider-specific. The validation matrix records account, tier, route, overload, and not-callable blockers observed in this account.

## C. Official references
- https://huggingface.co/docs/inference-providers/tasks/chat-completion
- https://huggingface.co/inference-providers/models
- https://huggingface.co/docs/inference-providers/pricing

## D. Wrapper behavior summary
- Public function signature: `generate(input_text, instruction=None, model='Qwen/Qwen3-4B-Instruct-2507', **kwargs)`.
- Current default model: `Qwen/Qwen3-4B-Instruct-2507`.
- Default selection date: `2026-04-25`.
- Default selection source: live provider catalog, official pricing/model documentation, and real smoke validation in `validacao_text_apis_2026-04-25`.
- Tie-break reasoning: Qwen/Qwen3-4B-Instruct-2507 was the lowest-cost router text model validated with non-empty output.
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
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `logit_bias`
- What it is: Token bias map for OpenAI-compatible APIs.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `logprobs`
- What it is: Token log probability return option. May add payload size and latency.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_completion_tokens`
- What it is: OpenAI-compatible completion cap used by selected reasoning/chat models.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `max_tokens`
- What it is: Maximum generated tokens for chat-style APIs. Lower values reduce cost and latency.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `messages`
- What it is: Provider-native chat message list. If supplied, it replaces the wrapper-built system/user messages.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `metadata`
- What it is: Provider metadata object. It does not affect output but may affect storage/audit behavior.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `model`
- What it is: Provider model identifier. In this project it is exposed as the explicit `model` function argument; passing it again in kwargs is unnecessary.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `n`
- What it is: Number of choices. Defaults to provider behavior; values above one increase cost.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `parallel_tool_calls`
- What it is: Tool parallelism control for providers that expose it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `presence_penalty`
- What it is: Penalty that encourages new topics.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `provider`
- What it is: Router provider policy object. Omitted by default so the router can choose the cheapest valid route.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `response_format`
- What it is: Structured output / JSON mode configuration when supported by the model.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `seed`
- What it is: Best-effort deterministic seed where the provider supports it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `service_tier`
- What it is: Provider queue/pricing tier. Omitted by default to avoid premium routing.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stop`
- What it is: OpenAI-compatible stop strings.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream`
- What it is: When true, the wrapper accumulates provider streaming internally and still returns the public result dict.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `stream_options`
- What it is: OpenAI-compatible streaming options, forwarded only when the provider accepts them.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `temperature`
- What it is: Sampling randomness. Lower values improve determinism; some reasoning/default models reject it.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tool_choice`
- What it is: Provider-native tool-selection policy.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tool_prompt`
- What it is: Provider-native option forwarded without aliasing after validation.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `tools`
- What it is: Provider-native tool definitions. Omitted by default because tools can add latency, token use, and external charges.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_logprobs`
- What it is: Number of top token log probabilities to return.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `top_p`
- What it is: Nucleus sampling control. Use instead of, not always together with, temperature when the provider restricts sampling.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

### `user`
- What it is: Provider user identifier.
- Accepted values: provider-native values documented by the official API for the selected model/family.
- Provider default: provider-owned when the field is omitted.
- Project default: omitted unless the wrapper must send it or the caller passes it explicitly.
- Practical impact: may affect cost, latency, determinism, reasoning depth, routing, tool use, structured outputs, safety behavior, caching, token usage; see model-specific provider docs.
- Model restrictions: validated for `huggingface` at family/model level in the validation matrix; unsupported combinations fail provider-side and are recorded as blockers.

## F. Model coverage
- Catalog snapshot date: `2026-04-25`.
- Relevant text/chat model count after scope filtering: `121` from raw catalog count `122`.
- Status values below come from real text-in/text-out calls unless the row is a parameter-cluster row.

| Model ID | Family | Validation result | Support status / blocker |
|---|---|---|---|
| Qwen/Qwen3-4B-Instruct-2507 | Qwen | passed | validated |
| moonshotai/Kimi-K2.6 | moonshotai | passed | validated |
| google/gemma-4-31B-it | google | passed | validated |
| zai-org/GLM-5.1 | zai-org | passed | validated |
| MiniMaxAI/MiniMax-M2.7 | MiniMaxAI | passed | validated |
| google/gemma-4-26B-A4B-it | google | passed | validated |
| Qwen/Qwen3.5-9B | Qwen | passed | validated |
| deepseek-ai/DeepSeek-R1 | deepseek-ai | passed | validated |
| openai/gpt-oss-120b | openai | passed | validated |
| moonshotai/Kimi-K2.5 | moonshotai | passed | validated |
| Qwen/Qwen3-Coder-Next | Qwen | passed | validated |
| Qwen/Qwen2.5-7B-Instruct | Qwen | passed | validated |
| meta-llama/Llama-3.1-8B-Instruct | meta-llama | passed | validated |
| Qwen/Qwen3.5-27B | Qwen | passed | validated |
| Qwen/Qwen3-8B | Qwen | passed | validated |
| Qwen/Qwen3.5-35B-A3B | Qwen | passed | validated |
| openai/gpt-oss-20b | openai | passed | validated |
| Qwen/Qwen3-VL-8B-Instruct | Qwen | passed | validated |
| Qwen/Qwen3.5-397B-A17B | Qwen | passed | validated |
| zai-org/GLM-5.1-FP8 | zai-org | passed | validated |
| meta-llama/Meta-Llama-3-8B-Instruct | meta-llama | passed | validated |
| meta-llama/Llama-3.2-1B-Instruct | meta-llama | passed | validated |
| Qwen/Qwen3-Coder-30B-A3B-Instruct | Qwen | passed | validated |
| zai-org/GLM-4.7-Flash | zai-org | passed | validated |
| zai-org/GLM-5 | zai-org | passed | validated |
| Qwen/Qwen2.5-Coder-7B-Instruct | Qwen | passed | validated |
| deepseek-ai/DeepSeek-V3 | deepseek-ai | passed | validated |
| Qwen/Qwen3.5-122B-A10B | Qwen | passed | validated |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B | deepseek-ai | passed | validated |
| deepseek-ai/DeepSeek-V3.2-Exp | deepseek-ai | passed | validated |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-7B | deepseek-ai | passed | validated |
| Qwen/Qwen3-Coder-480B-A35B-Instruct | Qwen | passed | validated |
| deepseek-ai/DeepSeek-V3.1 | deepseek-ai | passed | validated |
| Qwen/Qwen3-32B | Qwen | passed | validated |
| meta-llama/Llama-3.3-70B-Instruct | meta-llama | passed | validated |
| Qwen/Qwen3-30B-A3B | Qwen | passed | validated |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-32B | deepseek-ai | passed | validated |
| MiniMaxAI/MiniMax-M2.5 | MiniMaxAI | passed | validated |
| deepseek-ai/DeepSeek-R1-Distill-Llama-70B | deepseek-ai | passed | validated |
| Qwen/Qwen3-Next-80B-A3B-Instruct | Qwen | passed | validated |
| swiss-ai/Apertus-8B-Instruct-2509 | swiss-ai | passed | validated |
| XiaomiMiMo/MiMo-V2-Flash | XiaomiMiMo | passed | validated |
| meta-llama/Llama-4-Scout-17B-16E-Instruct | meta-llama | passed | validated |
| zai-org/GLM-4.5-Air | zai-org | passed | validated |
| Qwen/Qwen3-4B-Thinking-2507 | Qwen | passed | validated |
| deepseek-ai/DeepSeek-V3-0324 | deepseek-ai | passed | validated |
| moonshotai/Kimi-K2-Instruct | moonshotai | passed | validated |
| Qwen/Qwen3-VL-30B-A3B-Instruct | Qwen | passed | validated |
| meta-llama/Llama-Guard-4-12B | meta-llama | passed | validated |
| deepseek-ai/DeepSeek-R1-0528 | deepseek-ai | passed | validated |
| google/gemma-3-27b-it | google | passed | validated |
| google/gemma-3n-E4B-it | google | passed | validated |
| zai-org/GLM-4.6V-Flash | zai-org | failed | provider_rate_limit_or_overload |
| Qwen/Qwen2.5-Coder-3B-Instruct | Qwen | passed | validated |
| zai-org/GLM-4.6V | zai-org | passed | validated |
| Qwen/QwQ-32B | Qwen | failed | provider_temporarily_unavailable |
| NousResearch/Hermes-2-Pro-Llama-3-8B | NousResearch | passed | validated |
| zai-org/GLM-4.7 | zai-org | passed | validated |
| moonshotai/Kimi-K2-Thinking | moonshotai | passed | validated |
| Qwen/Qwen3-235B-A22B-Instruct-2507 | Qwen | passed | validated |
| zai-org/GLM-4.6-FP8 | zai-org | passed | validated |
| Qwen/Qwen3-235B-A22B | Qwen | passed | validated |
| Qwen/Qwen3-Coder-Next-FP8 | Qwen | passed | validated |
| zai-org/GLM-4.6 | zai-org | passed | validated |
| moonshotai/Kimi-K2-Instruct-0905 | moonshotai | passed | validated |
| zai-org/GLM-4.5V | zai-org | passed | validated |
| allenai/Olmo-3-7B-Instruct | allenai | passed | validated |
| deepseek-ai/DeepSeek-V3.1-Terminus | deepseek-ai | passed | validated |
| meta-llama/Llama-4-Maverick-17B-128E-Instruct | meta-llama | failed | model_parameter_or_payload_restriction |
| MiniMaxAI/MiniMax-M2.1 | MiniMaxAI | passed | validated |
| CohereLabs/aya-expanse-32b | CohereLabs | passed | validated |
| Qwen/Qwen2.5-Coder-32B-Instruct | Qwen | passed | validated |
| CohereLabs/c4ai-command-a-03-2025 | CohereLabs | passed | validated |
| deepseek-ai/DeepSeek-R1-Distill-Llama-8B | deepseek-ai | passed | validated |
| CohereLabs/command-a-reasoning-08-2025 | CohereLabs | passed | validated |
| CohereLabs/command-a-vision-07-2025 | CohereLabs | passed | validated |
| CohereLabs/command-a-translate-08-2025 | CohereLabs | passed | validated |
| Qwen/Qwen2.5-VL-72B-Instruct | Qwen | passed | validated |
| katanemo/Arch-Router-1.5B | katanemo | passed | validated |
| aisingapore/Gemma-SEA-LION-v4-27B-IT | aisingapore | passed | validated |
| CohereLabs/c4ai-command-r-08-2024 | CohereLabs | passed | validated |
| zai-org/GLM-4.7-FP8 | zai-org | passed | validated |
| CohereLabs/aya-vision-32b | CohereLabs | passed | validated |
| swiss-ai/Apertus-70B-Instruct-2509 | swiss-ai | passed | validated |
| CohereLabs/c4ai-command-r7b-12-2024 | CohereLabs | passed | validated |
| alpindale/WizardLM-2-8x22B | alpindale | passed | validated |
| meta-llama/Llama-3.1-70B-Instruct | meta-llama | passed | validated |
| aisingapore/Qwen-SEA-LION-v4-32B-IT | aisingapore | passed | validated |
| CohereLabs/c4ai-command-r7b-arabic-02-2025 | CohereLabs | passed | validated |
| meta-llama/Meta-Llama-3-70B-Instruct | meta-llama | passed | validated |
| Qwen/Qwen3-VL-30B-A3B-Thinking | Qwen | passed | validated |
| dicta-il/DictaLM-3.0-24B-Thinking | dicta-il | passed | validated |
| CohereLabs/tiny-aya-global | CohereLabs | passed | validated |
| Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8 | Qwen | passed | validated |
| Sao10K/L3-8B-Stheno-v3.2 | Sao10K | passed | validated |
| utter-project/EuroLLM-22B-Instruct-2512 | utter-project | passed | validated |
| CohereLabs/tiny-aya-water | CohereLabs | passed | validated |
| deepcogito/cogito-671b-v2.1 | deepcogito | passed | validated |
| Sao10K/L3-70B-Euryale-v2.1 | Sao10K | passed | validated |
| CohereLabs/tiny-aya-earth | CohereLabs | passed | validated |
| deepcogito/cogito-671b-v2.1-FP8 | deepcogito | passed | validated |
| Sao10K/L3-8B-Lunaris-v1 | Sao10K | passed | validated |
| CohereLabs/tiny-aya-fire | CohereLabs | passed | validated |
| EssentialAI/rnj-1-instruct | EssentialAI | passed | validated |
| Qwen/Qwen2.5-72B-Instruct | Qwen | passed | validated |
| Qwen/Qwen3-14B | Qwen | passed | validated |
| zai-org/GLM-4.5V-FP8 | zai-org | passed | validated |
| meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8 | meta-llama | failed | model_parameter_or_payload_restriction |
| zai-org/GLM-4-32B-0414 | zai-org | passed | validated |
| zai-org/GLM-4.6V-FP8 | zai-org | passed | validated |
| baidu/ERNIE-4.5-VL-424B-A47B-Base-PT | baidu | passed | validated |
| deepseek-ai/DeepSeek-Prover-V2-671B | deepseek-ai | passed | validated |
| Qwen/Qwen3-VL-235B-A22B-Instruct | Qwen | passed | validated |
| MiniMaxAI/MiniMax-M1-80k | MiniMaxAI | passed | validated |
| Qwen/Qwen3-VL-235B-A22B-Thinking | Qwen | passed | validated |
| baidu/ERNIE-4.5-300B-A47B-Base-PT | baidu | passed | validated |
| zai-org/AutoGLM-Phone-9B-Multilingual | zai-org | passed | validated |
| zai-org/GLM-4.5 | zai-org | passed | validated |
| Qwen/Qwen3-235B-A22B-Thinking-2507 | Qwen | passed | validated |
| Qwen/Qwen3-Next-80B-A3B-Thinking | Qwen | passed | validated |
| MiniMaxAI/MiniMax-M2 | MiniMaxAI | passed | validated |

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
from text.apis import huggingface

result = huggingface.generate("Reply with OK.")
print(result["output_text"])
```

### Explicit instruction
```python
result = huggingface.generate(
    "Summarize this in one sentence.",
    instruction="Use plain English.",
)
```

### Explicit model
```python
result = huggingface.generate(
    "Reply with OK.",
    model="Qwen/Qwen3-4B-Instruct-2507",
)
```

### Full options for the primary surface
```python
result = huggingface.generate("Reply with OK.", model="Qwen/Qwen3-4B-Instruct-2507", max_tokens=64, temperature=0, top_p=1, stop=["END"], stream=True)
```

## J. Pricing section
- Pricing snapshot date: `2026-04-25`.
- Pricing source: see the official references above and the validation artifact `validacao_text_apis_2026-04-25/catalog_huggingface.json`.
- Pricing can change without a code change, especially for routers and model aliases.
- The wrapper omits premium tiers, tools, web/search, cache writes, and explicit reasoning by default to avoid surprise charges.

## K. Validation note
- Real validation artifact: `tests/artefatos_testes/validacao_text_apis_2026-04-25/validation_matrix.md`.
- Provider result counts in the final matrix: `{'passed': 122, 'failed': 4}`.
- Failure blocker counts: `{'provider_rate_limit_or_overload': 1, 'provider_temporarily_unavailable': 1, 'model_parameter_or_payload_restriction': 2}`.
- Failed rows are not claimed as supported; they are documented as provider, route, account, or model restrictions observed during validation.
