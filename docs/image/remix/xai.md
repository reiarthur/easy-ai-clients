# xAI Remix API

## Overview

This module implements reference-conditioned image generation for xAI using the repository-wide normalized public contract. The public function is `remix(prompt, reference_images, **kwargs)` and returns `cust_usd`, `base64`, `warnings`, `request_id`.

Public image inputs accept local file paths, raw base64 image strings, `data:` URLs, and public HTTP(S) image URLs. Public HTTP(S) URLs are downloaded through the shared image normalization layer with scheme, timeout, content-type, and Pillow image validation.

## Account And Credentials

- Signup/account: https://console.x.ai/
- API key documentation: https://console.x.ai/team/api-keys
- Required environment variable: `XAI_API_KEY`

## Official Sources

Endpoint documentation:
- https://docs.x.ai/docs/api-reference
- https://docs.x.ai/docs/guides/image-generation

Model/catalog documentation:
- https://docs.x.ai/docs/models

Pricing documentation:
- https://docs.x.ai/docs/models

## Current Wrapper Default

- Default model: `grok-imagine-image`
- Model selection: `model` keyword argument in **kwargs
- Snapshot date: 2026-04-25

The default is the lowest-cost sensible candidate selected from official pricing, official live catalogs, and repository validation. If official pricing is incomplete, the wrapper uses the strongest official pricing proxy available and records the uncertainty in validation artifacts.

## Lowest-Cost Default Policy

The wrapper sends the smallest valid request shape by default: one output image for image domains, no optional enhancement or premium routing, no explicit mask unless provided, no premium reasoning unless unavoidable, and no provider-specific paid extras unless the caller supplies them in `**kwargs`.

For `remix`, the public signature intentionally has no dedicated `model` parameter. When no `model` keyword is supplied, `grok-imagine-image` is used internally as the cheapest relevant reference-capable default currently implemented for this provider.

## Parameter Reference

Supported public keyword parameters are provider-native whenever practical. Unsupported keyword arguments return a normalized warning or analyze output instead of being silently ignored.

timeout_seconds, aspect_ratio, reasoning, n, response_format, max_output_tokens, temperature, top_p, tools, tool_choice, metadata, user, instructions, and store where accepted.

Operational keyword parameters:

- `timeout_seconds`: request or polling timeout, default chosen per provider/domain.
- `mask`: accepted by `edit` wrappers where relevant; the public mask contract remains black = editable and white = protected.
- `base_image`: accepted by `remix` as a keyword where a provider supports or needs an anchor image concept.

## Model Coverage

Analyze uses Grok responses models with image input. Image domains use grok-imagine-image and grok-imagine-image-pro when available.

xAI coverage is based on the live /v1/models catalog and official image generation guide. The wrapper supports Grok vision and Grok Imagine image models that the account exposes.

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

For dynamic providers, the Markdown page is intentionally family-oriented. The dated validation matrix contains the per-model rows and catalog snapshot summaries for the live execution.

## Python Example

```python
from remix.apis import xai_api

result = xai_api.remix(
    "Create a new image using these references.",
    ["imagem.png"],
)
print(result)
```

## Pricing Notes

Costs are exact only when the provider exposes usage or fixed per-request pricing that this repository can map deterministically. Otherwise the wrapper returns `0.0` with a warning or records the cost uncertainty in the validation matrix. OpenRouter costs can be refined with `updateCost(result_dict)` when a `request_id` is available.

## Validation Note

Validation is executed through the Python 3.11 Conda environment named `image`. Current and future runs write dated artifacts under `tests/artefatos_testes/`, including `validation_matrix.md`, `validation_matrix.json`, provider result JSON files, and sanitized catalog summaries.

Latest validation run for this update: `tests/artefatos_testes/image_api_validation_20260424_222258/`.
