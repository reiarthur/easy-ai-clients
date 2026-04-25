# Groq Analyze API

## Overview

This module implements image-to-text analysis for Groq using the repository-wide normalized public contract. The public function is `analyze(prompt, image, model="<lowest_cost_default>", **kwargs)` and returns `request_id`, `cost_usd`, `input_text`, `output`.

Public image inputs accept local file paths, raw base64 image strings, `data:` URLs, and public HTTP(S) image URLs. Public HTTP(S) URLs are downloaded through the shared image normalization layer with scheme, timeout, content-type, and Pillow image validation.

## Account And Credentials

- Signup/account: https://console.groq.com/
- API key documentation: https://console.groq.com/keys
- Required environment variable: `GROQ_API_KEY`

## Official Sources

Endpoint documentation:
- https://console.groq.com/docs/vision
- https://console.groq.com/docs/api-reference

Model/catalog documentation:
- https://console.groq.com/docs/models

Pricing documentation:
- https://groq.com/pricing

## Current Wrapper Default

- Default model: `meta-llama/llama-4-scout-17b-16e-instruct`
- Model selection: `model` argument
- Snapshot date: 2026-04-25

The default is the lowest-cost sensible candidate selected from official pricing, official live catalogs, and repository validation. If official pricing is incomplete, the wrapper uses the strongest official pricing proxy available and records the uncertainty in validation artifacts.

## Lowest-Cost Default Policy

The wrapper sends the smallest valid request shape by default: one output image for image domains, no optional enhancement or premium routing, no explicit mask unless provided, no premium reasoning unless unavoidable, and no provider-specific paid extras unless the caller supplies them in `**kwargs`.

## Parameter Reference

Supported public keyword parameters are provider-native whenever practical. Unsupported keyword arguments return a normalized warning or analyze output instead of being silently ignored.

timeout_seconds, service_tier, max_output_tokens, temperature, top_p, metadata, user, instructions, tools, tool_choice, and store where accepted by Groq Responses.

Operational keyword parameters:

- `timeout_seconds`: request or polling timeout, default chosen per provider/domain.
- `mask`: accepted by `edit` wrappers where relevant; the public mask contract remains black = editable and white = protected.
- `base_image`: accepted by `remix` as a keyword where a provider supports or needs an anchor image concept.

## Model Coverage

In-scope models are Groq models documented for vision on the Responses API, currently led by meta-llama/llama-4-scout-17b-16e-instruct.

Groq coverage is analyze-only in this repository. The wrapper targets the official OpenAI-compatible Responses vision surface and validates the live model catalog during smoke tests.

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
from analyze.apis import groq_api

result = groq_api.analyze(
    "Describe the important visual details.",
    "imagem.png",
)
print(result)
```

## Pricing Notes

Costs are exact only when the provider exposes usage or fixed per-request pricing that this repository can map deterministically. Otherwise the wrapper returns `0.0` with a warning or records the cost uncertainty in the validation matrix. OpenRouter costs can be refined with `updateCost(result_dict)` when a `request_id` is available.

## Validation Note

Validation is executed through the Python 3.11 Conda environment named `image`. Current and future runs write dated artifacts under `tests/artefatos_testes/`, including `validation_matrix.md`, `validation_matrix.json`, provider result JSON files, and sanitized catalog summaries.

Latest validation run for this update: `tests/artefatos_testes/image_api_validation_20260424_222258/`.
