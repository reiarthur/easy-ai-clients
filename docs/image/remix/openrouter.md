# OpenRouter Remix API

## Overview

This module implements reference-conditioned image generation for OpenRouter using the repository-wide normalized public contract. The public function is `remix(prompt, reference_images, **kwargs)` and returns `cust_usd`, `base64`, `warnings`, `request_id`.

Public image inputs accept local file paths, raw base64 image strings, `data:` URLs, and public HTTP(S) image URLs. Public HTTP(S) URLs are downloaded through the shared image normalization layer with scheme, timeout, content-type, and Pillow image validation.

## Account And Credentials

- Signup/account: https://openrouter.ai/
- API key documentation: https://openrouter.ai/settings/keys
- Required environment variable: `OPENROUTER_API_KEY`

## Official Sources

Endpoint documentation:
- https://openrouter.ai/docs
- https://openrouter.ai/docs/api-reference/chat-completion
- https://openrouter.ai/docs/api-reference/generation

Model/catalog documentation:
- https://openrouter.ai/api/v1/models

Pricing documentation:
- https://openrouter.ai/docs#models
- https://openrouter.ai/api/v1/models

## Current Wrapper Default

- Default model: `black-forest-labs/flux.2-klein-4b`
- Model selection: `model` keyword argument in **kwargs
- Snapshot date: 2026-04-25

The default is the lowest-cost sensible candidate selected from official pricing, official live catalogs, and the implemented source defaults. If official pricing is incomplete, the wrapper uses the strongest official pricing proxy available or returns the safest available estimate.

## Lowest-Cost Default Policy

The wrapper sends the smallest valid request shape by default: one output image for image domains, no optional enhancement or premium routing, no explicit mask unless provided, no premium reasoning unless unavoidable, and no provider-specific paid extras unless the caller supplies them in `**kwargs`.

For `remix`, the public signature intentionally has no dedicated `model` parameter. When no `model` keyword is supplied, `black-forest-labs/flux.2-klein-4b` is used internally as the cheapest relevant reference-capable default currently implemented for this provider.

## Parameter Reference

Supported public keyword parameters are provider-native whenever practical. Unsupported keyword arguments return a normalized warning or analyze output instead of being silently ignored.

timeout_seconds, aspect_ratio, image_config, provider routing, max_tokens, temperature, top_p, top_k, seed, stop, penalties, reasoning, response_format, structured_outputs, tools, tool_choice, and transforms according to supported_parameters in the live catalog.

Operational keyword parameters:

- `timeout_seconds`: request or polling timeout, default chosen per provider/domain.
- `mask`: accepted by `edit` wrappers where relevant; the public mask contract remains black = editable and white = protected.
- `base_image`: accepted by `remix` as a keyword where a provider supports or needs an anchor image concept.

## Model Coverage

The live catalog is authoritative. Analyze requires image input and text output. Generate requires image output. Edit/remix require both image input and image output. The matrix records every discovered relevant model id.

OpenRouter is a large dynamic aggregator. Coverage is grouped by input/output modality and supported_parameters from the live model catalog; the wrapper validates modality compatibility before calls.

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

result = image.remix(
    "Keep the subject but use watercolor style.",
    ["input.png"],
    api="openrouter",
)
print(result)
~~~

## Pricing Notes

Costs are exact only when the provider exposes usage or fixed per-request pricing that this repository can map deterministically. Otherwise the wrapper returns 0.0 with a warning or with the safest available estimate. OpenRouter costs can be refined with image.update_cost("remix", result, api="openrouter") when a request_id is available.

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.