"""Hugging Face image analysis wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.simple_image_providers import huggingface_analyze

MODELS_URL = "https://huggingface.co/docs/inference-providers/tasks/image-text-to-text"
PRICING_URL = "https://huggingface.co/pricing"
_DEFAULTS = {"timeout_seconds": 60}


def analyze(prompt: str, image: str, model: str = "Qwen/Qwen2.5-VL-7B-Instruct", **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    return huggingface_analyze(
        prompt=prompt,
        image=image,
        model=model,
        timeout_seconds=int(values["timeout_seconds"]),
        parameters=payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    )


__all__ = ["MODELS_URL", "PRICING_URL", "analyze"]
