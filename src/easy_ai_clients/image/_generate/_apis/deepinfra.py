"""DeepInfra image generation wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.simple_image_providers import openai_compatible_generate

API_URL = "https://api.deepinfra.com/v1/openai/images/generations"
MODELS_URL = "https://docs.deepinfra.com/apis/image-generation"
PRICING_URL = "https://deepinfra.com/pricing"
_DEFAULTS = {"size": "1024x1024", "quality": None, "output_format": "png", "timeout_seconds": 120}


def generate(prompt: str, model: str = "black-forest-labs/FLUX-1-schnell", **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    return openai_compatible_generate(
        provider_label="DeepInfra",
        env_var="DEEPINFRA_API_KEY",
        url=API_URL,
        prompt=prompt,
        model=model,
        size=values["size"],
        quality=values["quality"],
        output_format=values["output_format"],
        timeout_seconds=int(values["timeout_seconds"]),
        extra_body=payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    )


__all__ = ["API_URL", "MODELS_URL", "PRICING_URL", "generate"]
