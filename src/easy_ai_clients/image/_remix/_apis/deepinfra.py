"""DeepInfra reference-image remix wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.image_utils import image_to_data_url
from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.simple_image_providers import openai_compatible_edit
from ..pre_processing import prepare_remix_inputs

API_URL = "https://api.deepinfra.com/v1/openai/images/edits"
MODELS_URL = "https://docs.deepinfra.com/apis/image-generation"
PRICING_URL = "https://deepinfra.com/pricing"
_DEFAULTS = {"model": "black-forest-labs/FLUX-1-Kontext-dev", "base_image": None, "size": "1024x1024", "quality": None, "output_format": "png", "timeout_seconds": 120}


def remix(prompt: str, reference_images: list[str], **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    prepared = prepare_remix_inputs(prompt, reference_images, base_image=values["base_image"])
    first_image = prepared.base_image or prepared.reference_images[0]
    return openai_compatible_edit(
        provider_label="DeepInfra",
        env_var="DEEPINFRA_API_KEY",
        url=API_URL,
        prompt=prompt,
        image=image_to_data_url(first_image),
        model=values["model"],
        size=values["size"],
        quality=values["quality"],
        output_format=values["output_format"],
        timeout_seconds=int(values["timeout_seconds"]),
        extra_body=payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    )


__all__ = ["API_URL", "MODELS_URL", "PRICING_URL", "remix"]
