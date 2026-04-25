# OpenAI Edit API

## Overview

This module implements prompt-guided image editing for OpenAI using the repository-wide normalized public contract. The public function is `edit(prompt, image, model="<lowest_cost_default>", **kwargs)` and returns `cust_usd`, `base64`, `warnings`, `request_id`.

Public image inputs accept local file paths, raw base64 image strings, `data:` URLs, and public HTTP(S) image URLs. Public HTTP(S) URLs are downloaded through the shared image normalization layer with scheme, timeout, content-type, and Pillow image validation.

## Account And Credentials

- Signup/account: https://platform.openai.com/signup
- API key documentation: https://platform.openai.com/api-keys
- Required environment variable: `OPENAI_API_KEY`

## Official Sources

Endpoint documentation:
- https://developers.openai.com/api-reference/images
- https://developers.openai.com/api-reference/responses

Model/catalog documentation:
- https://developers.openai.com/api/docs/models

Pricing documentation:
- https://developers.openai.com/api/docs/pricing

## Current Wrapper Default

- Default model: `gpt-image-1-mini`
- Model selection: `model` argument
- Snapshot date: 2026-04-25

The default is the lowest-cost sensible candidate selected from official pricing, official live catalogs, and repository validation. If official pricing is incomplete, the wrapper uses the strongest official pricing proxy available and records the uncertainty in validation artifacts.

## Lowest-Cost Default Policy

The wrapper sends the smallest valid request shape by default: one output image for image domains, no optional enhancement or premium routing, no explicit mask unless provided, no premium reasoning unless unavoidable, and no provider-specific paid extras unless the caller supplies them in `**kwargs`.

## Parameter Reference

Supported public keyword parameters are provider-native whenever practical. Unsupported keyword arguments return a normalized warning or analyze output instead of being silently ignored.

timeout_seconds plus native OpenAI fields such as size, quality, output_format, n, background, moderation, output_compression, input_fidelity, service_tier, reasoning, max_output_tokens, temperature, top_p, tools, tool_choice, response_format, metadata, user, instructions, and store where accepted by the selected endpoint.

Operational keyword parameters:

- `timeout_seconds`: request or polling timeout, default chosen per provider/domain.
- `mask`: accepted by `edit` wrappers where relevant; the public mask contract remains black = editable and white = protected.
- `base_image`: accepted by `remix` as a keyword where a provider supports or needs an anchor image concept.

## Model Coverage

In-scope analyze families include GPT-4.1, GPT-4o, GPT-5, GPT-5.x, and o-series models with image input. In-scope image families include gpt-image-1-mini, gpt-image-1, gpt-image-1.5, gpt-image-2, chatgpt-image-latest, dall-e-2, and dall-e-3 when the endpoint supports the domain.

OpenAI exposes a catalog endpoint and official model documentation. The wrapper accepts every officially available relevant model id through the model argument; live validation classifies unavailable, gated, or incompatible models in the validation matrix.

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
from edit.apis import openai_api

result = openai_api.edit(
    "Make the background cleaner while preserving the subject.",
    "imagem.png",
)
print(result)
```

## Pricing Notes

Costs are exact only when the provider exposes usage or fixed per-request pricing that this repository can map deterministically. Otherwise the wrapper returns `0.0` with a warning or records the cost uncertainty in the validation matrix. OpenRouter costs can be refined with `updateCost(result_dict)` when a `request_id` is available.

## Validation Note

Validation is executed through the Python 3.11 Conda environment named `image`. Current and future runs write dated artifacts under `tests/artefatos_testes/`, including `validation_matrix.md`, `validation_matrix.json`, provider result JSON files, and sanitized catalog summaries.

Latest validation run for this update: `tests/artefatos_testes/image_api_validation_20260424_222258/`.
