"""Hugging Face image generation wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.simple_image_providers import huggingface_generate

MODELS_URL = "https://huggingface.co/docs/inference-providers/tasks/text-to-image"
PRICING_URL = "https://huggingface.co/pricing"
_DEFAULTS = {"timeout_seconds": 120}


def generate(prompt: str, model: str = "black-forest-labs/FLUX.1-schnell", **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    return huggingface_generate(
        prompt=prompt,
        model=model,
        timeout_seconds=int(values["timeout_seconds"]),
        parameters=payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    )


__all__ = ["MODELS_URL", "PRICING_URL", "generate"]
