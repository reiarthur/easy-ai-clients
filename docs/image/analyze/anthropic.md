# Anthropic Claude Analyze API

## Overview

This module implements image-to-text analysis for Anthropic Claude using the repository-wide normalized public contract. The public function is `analyze(prompt, image, model=None, **kwargs)` and returns `request_id`, `cost_usd`, `input_text`, `output`.

Public image inputs accept local file paths, raw base64 image strings, `data:` URLs, and public HTTP(S) image URLs. Public HTTP(S) URLs are downloaded through the shared image normalization layer with scheme, timeout, content-type, and Pillow image validation.

## Account And Credentials

- Signup/account: https://console.anthropic.com/
- API key documentation: https://console.anthropic.com/settings/keys
- Required environment variable: `ANTHROPIC_API_KEY`

## Official Sources

Endpoint documentation:
- https://docs.anthropic.com/en/api/messages
- https://docs.anthropic.com/en/docs/build-with-claude/vision

Model/catalog documentation:
- https://docs.anthropic.com/en/docs/about-claude/models

Pricing documentation:
- https://www.anthropic.com/pricing

## Current Wrapper Default

- Default model: `claude-haiku-4-5-20251001`
- Model selection: `model` argument
- Snapshot date: 2026-04-25

The default is the lowest-cost sensible candidate selected from official pricing, official live catalogs, and the implemented source defaults. If official pricing is incomplete, the wrapper uses the strongest official pricing proxy available or returns the safest available estimate.

## Lowest-Cost Default Policy

The wrapper sends the smallest valid request shape by default: one output image for image domains, no optional enhancement or premium routing, no explicit mask unless provided, no premium reasoning unless unavoidable, and no provider-specific paid extras unless the caller supplies them in `**kwargs`.

## Parameter Reference

Supported public keyword parameters are provider-native whenever practical. Unsupported keyword arguments return a normalized warning or analyze output instead of being silently ignored.

timeout_seconds, max_tokens, temperature, top_p, top_k, system, stop_sequences, metadata, tools, tool_choice, and thinking.

Operational keyword parameters:

- `timeout_seconds`: request or polling timeout, default chosen per provider/domain.
- `mask`: accepted by `edit` wrappers where relevant; the public mask contract remains black = editable and white = protected.
- `base_image`: accepted by `remix` as a keyword where a provider supports or needs an anchor image concept.

## Model Coverage

In-scope models are Claude models with image input on the Messages API, especially Haiku, Sonnet, and Opus 4.x families visible to the account.

Claude coverage is analyze-only in this repository. Vision-capable Claude 4 and 4.5/4.6/4.7 families are accepted by model id when visible to the account.

Coverage classes used by the validation matrix:

| Status | Meaning |
| --- | --- |
| `official_available` | The model appears in an official catalog or official documentation for this domain. |
| `implemented` | The wrapper can form a request for the model using this repository's normalized contract. |
| `tested` | A live request was attempted and returned a provider result or normalized provider rejection. |
| `blocked` | The live attempt was blocked by key, quota, billing, rate limit, region, gating, or provider policy. |
| `incompatible` | The official model/schema cannot be normalized safely into this domain's public contract. |

## Domain Notes

The wrapper preserves the repository return shape exactly. Provider-side safety blocks, auth failures, billing failures, unsupported combinations, and transport failures are converted into the normalized `warnings` field for image operations or the normalized `output` field for analyze operations.

For dynamic providers, the Markdown page is intentionally family-oriented. Provider model availability is dynamic; use the official provider docs and your own credentials for live production checks.

## Python Example

~~~python
from easy_ai_clients import image

result = image.analyze(
    "Describe the important visual details.",
    "input.png",
    api="anthropic",
)
print(result)
~~~

## Pricing Notes

Costs are exact only when the provider exposes usage or fixed per-request pricing that this repository can map deterministically. Otherwise the wrapper returns 0.0 with a warning or with the safest available estimate. OpenRouter costs can be refined with image.update_cost("analyze", result, api="openrouter") when a request_id is available.

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.