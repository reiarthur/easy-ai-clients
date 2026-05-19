"""Hugging Face image editing wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.simple_image_providers import huggingface_image_to_image
from ..pre_processing import prepare_edit_inputs

MODELS_URL = "https://huggingface.co/docs/inference-providers/tasks/image-to-image"
PRICING_URL = "https://huggingface.co/pricing"
_DEFAULTS = {"mask": None, "timeout_seconds": 120}


def edit(prompt: str, image: str, model: str = "stabilityai/stable-diffusion-xl-refiner-1.0", **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    prepared = prepare_edit_inputs(prompt, image, provider="openai", mask=values["mask"])
    return huggingface_image_to_image(
        prompt=prepared.prompt,
        images=[prepared.image],
        model=model,
        timeout_seconds=int(values["timeout_seconds"]),
        parameters=payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    )


__all__ = ["MODELS_URL", "PRICING_URL", "edit"]
