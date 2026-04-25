# Fireworks AI Analyze API

## Overview

This module implements image-to-text analysis for Fireworks AI using the repository-wide normalized public contract. The public function is `analyze(prompt, image, model=None, **kwargs)` and returns `request_id`, `cost_usd`, `input_text`, `output`.

Public image inputs accept local file paths, raw base64 image strings, `data:` URLs, and public HTTP(S) image URLs. Public HTTP(S) URLs are downloaded through the shared image normalization layer with scheme, timeout, content-type, and Pillow image validation.

## Account And Credentials

- Signup/account: https://fireworks.ai/
- API key documentation: https://fireworks.ai/account/api-keys
- Required environment variable: `FIREWORKS_API_KEY`

## Official Sources

Endpoint documentation:
- https://docs.fireworks.ai/guides/generate-a-new-image
- https://docs.fireworks.ai/guides/edit-an-image
- https://docs.fireworks.ai/guides/querying-vision-language-models

Model/catalog documentation:
- https://api.fireworks.ai/inference/v1/models

Pricing documentation:
- https://fireworks.ai/pricing

## Current Wrapper Default

- Default model: `accounts/fireworks/models/kimi-k2p5`
- Model selection: `model` argument
- Snapshot date: 2026-04-25

The default is the lowest-cost sensible candidate selected from official pricing, official live catalogs, and the implemented source defaults. If official pricing is incomplete, the wrapper uses the strongest official pricing proxy available or returns the safest available estimate.

## Lowest-Cost Default Policy

The wrapper sends the smallest valid request shape by default: one output image for image domains, no optional enhancement or premium routing, no explicit mask unless provided, no premium reasoning unless unavoidable, and no provider-specific paid extras unless the caller supplies them in `**kwargs`.

## Parameter Reference

Supported public keyword parameters are provider-native whenever practical. Unsupported keyword arguments return a normalized warning or analyze output instead of being silently ignored.

timeout_seconds, aspect_ratio, output_format, steps, seed, plus native JSON fields such as strength, prompt_upsampling, safety_tolerance, guidance_scale, max_tokens, temperature, top_p, top_k, stop, tools, and tool_choice when supported.

Operational keyword parameters:

- `timeout_seconds`: request or polling timeout, default chosen per provider/domain.
- `mask`: accepted by `edit` wrappers where relevant; the public mask contract remains black = editable and white = protected.
- `base_image`: accepted by `remix` as a keyword where a provider supports or needs an anchor image concept.

## Model Coverage

Analyze coverage includes image-input chat models in the Fireworks catalog. Image coverage includes flux-1-schnell-fp8 and flux-1-dev-fp8 for generation plus flux-kontext-pro and flux-kontext-max for edit/remix workflows.

Fireworks coverage is catalog-driven. Analyze uses models with image input and text output through chat completions; image domains use the official FLUX workflow surfaces where the account catalog exposes them.

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
    api="fireworks",
)
print(result)
~~~

## Pricing Notes

Costs are exact only when the provider exposes usage or fixed per-request pricing that this repository can map deterministically. Otherwise the wrapper returns 0.0 with a warning or with the safest available estimate. OpenRouter costs can be refined with image.update_cost("analyze", result, api="openrouter") when a request_id is available.

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.