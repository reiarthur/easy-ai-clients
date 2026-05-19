"""DeepInfra vision analysis wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.simple_image_providers import openai_style_vision_analyze

API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
MODELS_URL = "https://docs.deepinfra.com/chat/vision"
PRICING_URL = "https://deepinfra.com/pricing"
_DEFAULTS = {"timeout_seconds": 60}


def analyze(prompt: str, image: str, model: str = "meta-llama/Llama-3.2-11B-Vision-Instruct", **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    return openai_style_vision_analyze(
        provider_label="DeepInfra",
        env_var="DEEPINFRA_API_KEY",
        url=API_URL,
        prompt=prompt,
        image=image,
        model=model,
        timeout_seconds=int(values["timeout_seconds"]),
        extra_body=payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    )


__all__ = ["API_URL", "MODELS_URL", "PRICING_URL", "analyze"]
