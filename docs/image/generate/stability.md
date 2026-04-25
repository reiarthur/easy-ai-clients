# Stability AI Generate API

## Overview

This module implements text-to-image generation for Stability AI using the repository-wide normalized public contract. The public function is `generate(prompt, model="<lowest_cost_default>", **kwargs)` and returns `cust_usd`, `base64`, `warnings`, `request_id`.

Public image inputs accept local file paths, raw base64 image strings, `data:` URLs, and public HTTP(S) image URLs. Public HTTP(S) URLs are downloaded through the shared image normalization layer with scheme, timeout, content-type, and Pillow image validation.

## Account And Credentials

- Signup/account: https://platform.stability.ai/
- API key documentation: https://platform.stability.ai/account/keys
- Required environment variable: `STABILITY_API_KEY`

## Official Sources

Endpoint documentation:
- https://platform.stability.ai/docs/api-reference#tag/Generate
- https://platform.stability.ai/docs/api-reference#tag/Edit
- https://platform.stability.ai/docs/api-reference#tag/Control

Model/catalog documentation:
- https://platform.stability.ai/docs

Pricing documentation:
- https://platform.stability.ai/pricing

## Current Wrapper Default

- Default model: `stable-image-core`
- Model selection: `model` argument
- Snapshot date: 2026-04-25

The default is the lowest-cost sensible candidate selected from official pricing, official live catalogs, and repository validation. If official pricing is incomplete, the wrapper uses the strongest official pricing proxy available and records the uncertainty in validation artifacts.

## Lowest-Cost Default Policy

The wrapper sends the smallest valid request shape by default: one output image for image domains, no optional enhancement or premium routing, no explicit mask unless provided, no premium reasoning unless unavoidable, and no provider-specific paid extras unless the caller supplies them in `**kwargs`.

## Parameter Reference

Supported public keyword parameters are provider-native whenever practical. Unsupported keyword arguments return a normalized warning or analyze output instead of being silently ignored.

timeout_seconds, aspect_ratio, output_format, seed, negative_prompt, style_preset, cfg_scale, grow_mask, creativity, and fidelity where supported by the operation endpoint.

Operational keyword parameters:

- `timeout_seconds`: request or polling timeout, default chosen per provider/domain.
- `mask`: accepted by `edit` wrappers where relevant; the public mask contract remains black = editable and white = protected.
- `base_image`: accepted by `remix` as a keyword where a provider supports or needs an anchor image concept.

## Model Coverage

In-scope surfaces are stable-image-core, stable-image-ultra, stable-image-inpaint, stable-image-style, and stable-image-structure.

Stability exposes operation-specific surfaces rather than arbitrary model ids. The wrapper maps stable-image-core, stable-image-ultra, stable-image-inpaint, stable-image-style, and stable-image-structure to their official endpoints.

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
from generate.apis import stability_ai_api

result = stability_ai_api.generate(
    "Create a small clean product icon.",
)
print(result)
```

## Pricing Notes

Costs are exact only when the provider exposes usage or fixed per-request pricing that this repository can map deterministically. Otherwise the wrapper returns `0.0` with a warning or records the cost uncertainty in the validation matrix. OpenRouter costs can be refined with `updateCost(result_dict)` when a `request_id` is available.

## Validation Note

Validation is executed through the Python 3.11 Conda environment named `image`. Current and future runs write dated artifacts under `tests/artefatos_testes/`, including `validation_matrix.md`, `validation_matrix.json`, provider result JSON files, and sanitized catalog summaries.

Latest validation run for this update: `tests/artefatos_testes/image_api_validation_20260424_222258/`.
