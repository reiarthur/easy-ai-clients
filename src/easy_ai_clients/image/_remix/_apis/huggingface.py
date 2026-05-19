"""Hugging Face image remix wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.simple_image_providers import huggingface_image_to_image
from ..pre_processing import prepare_remix_inputs

MODELS_URL = "https://huggingface.co/docs/inference-providers/tasks/image-to-image"
PRICING_URL = "https://huggingface.co/pricing"
_DEFAULTS = {"model": "stabilityai/stable-diffusion-xl-refiner-1.0", "base_image": None, "timeout_seconds": 120}


def remix(prompt: str, reference_images: list[str], **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    prepared = prepare_remix_inputs(prompt, reference_images, base_image=values["base_image"])
    images = ([prepared.base_image] if prepared.base_image else []) + prepared.reference_images
    return huggingface_image_to_image(
        prompt=prepared.prompt,
        images=images,
        model=values["model"],
        timeout_seconds=int(values["timeout_seconds"]),
        parameters=payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    )


__all__ = ["MODELS_URL", "PRICING_URL", "remix"]
