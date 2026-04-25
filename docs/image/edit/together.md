# Together AI Edit API

## Overview

This module implements prompt-guided image editing for Together AI using the repository-wide normalized public contract. The public function is `edit(prompt, image, model=None, **kwargs)` and returns `cust_usd`, `base64`, `warnings`, `request_id`.

Public image inputs accept local file paths, raw base64 image strings, `data:` URLs, and public HTTP(S) image URLs. Public HTTP(S) URLs are downloaded through the shared image normalization layer with scheme, timeout, content-type, and Pillow image validation.

## Account And Credentials

- Signup/account: https://api.together.ai/signin
- API key documentation: https://api.together.ai/settings/api-keys
- Required environment variable: `TOGETHER_API_KEY`

## Official Sources

Endpoint documentation:
- https://docs.together.ai/reference/images
- https://docs.together.ai/reference/chat-completions

Model/catalog documentation:
- https://docs.together.ai/docs/serverless-models
- https://api.together.xyz/v1/models

Pricing documentation:
- https://www.together.ai/pricing

## Current Wrapper Default

- Default model: `black-forest-labs/FLUX.2-dev`
- Model selection: `model` argument
- Snapshot date: 2026-04-25

The default is the lowest-cost sensible candidate selected from official pricing, official live catalogs, and the implemented source defaults. If official pricing is incomplete, the wrapper uses the strongest official pricing proxy available or returns the safest available estimate.

## Lowest-Cost Default Policy

The wrapper sends the smallest valid request shape by default: one output image for image domains, no optional enhancement or premium routing, no explicit mask unless provided, no premium reasoning unless unavoidable, and no provider-specific paid extras unless the caller supplies them in `**kwargs`.

## Parameter Reference

Supported public keyword parameters are provider-native whenever practical. Unsupported keyword arguments return a normalized warning or analyze output instead of being silently ignored.

timeout_seconds, width, height, steps, seed, output_format, negative_prompt, guidance_scale, num_images, image_loras, max_tokens, temperature, top_p, top_k, repetition_penalty, stop, tools, and tool_choice according to endpoint and model family.

Operational keyword parameters:

- `timeout_seconds`: request or polling timeout, default chosen per provider/domain.
- `mask`: accepted by `edit` wrappers where relevant; the public mask contract remains black = editable and white = protected.
- `base_image`: accepted by `remix` as a keyword where a provider supports or needs an anchor image concept.

## Model Coverage

The live catalog is authoritative. Image type rows are text-to-image candidates. Reference-capable families include FLUX.1 Kontext, FLUX.2, Gemini/Flash image, and other families when the endpoint accepts image_url or reference_images.

Together coverage is catalog-driven. Text-to-image models are discovered from type=image rows; vision models are discovered from image-capable chat models and documented vision families.

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

result = image.edit(
    "Make the background cleaner while preserving the subject.",
    "input.png",
    api="together",
)
print(result)
~~~

## Pricing Notes

Costs are exact only when the provider exposes usage or fixed per-request pricing that this repository can map deterministically. Otherwise the wrapper returns 0.0 with a warning or with the safest available estimate. OpenRouter costs can be refined with image.update_cost("edit", result, api="openrouter") when a request_id is available.

## Validation Note

The bundled unit tests validate imports and dispatcher routing without calling paid provider APIs. Provider model catalogs, account access, prices, and rate limits can change independently of this package; run your own provider smoke tests with your credentials before relying on a specific model in production.