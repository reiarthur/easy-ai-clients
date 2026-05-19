"""DeepInfra image editing wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.simple_image_providers import openai_compatible_edit

API_URL = "https://api.deepinfra.com/v1/openai/images/edits"
MODELS_URL = "https://docs.deepinfra.com/apis/image-generation"
PRICING_URL = "https://deepinfra.com/pricing"
_DEFAULTS = {"mask": None, "size": "1024x1024", "quality": None, "output_format": "png", "timeout_seconds": 120}


def edit(prompt: str, image: str, model: str = "black-forest-labs/FLUX-1-Kontext-dev", **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    return openai_compatible_edit(
        provider_label="DeepInfra",
        env_var="DEEPINFRA_API_KEY",
        url=API_URL,
        prompt=prompt,
        image=image,
        model=model,
        mask=values["mask"],
        size=values["size"],
        quality=values["quality"],
        output_format=values["output_format"],
        timeout_seconds=int(values["timeout_seconds"]),
        extra_body=payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    )


__all__ = ["API_URL", "MODELS_URL", "PRICING_URL", "edit"]
