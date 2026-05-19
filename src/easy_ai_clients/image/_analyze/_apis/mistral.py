"""Mistral OCR/vision image analysis wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.simple_image_providers import openai_style_vision_analyze

CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
MODELS_URL = "https://docs.mistral.ai/api/endpoint/ocr"
PRICING_URL = "https://mistral.ai/products/la-plateforme#pricing"
_DEFAULTS = {"timeout_seconds": 60}


def analyze(prompt: str, image: str, model: str = "pixtral-large-latest", **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    return openai_style_vision_analyze(
        provider_label="Mistral",
        env_var="MISTRAL_API_KEY",
        url=CHAT_URL,
        prompt=prompt,
        image=image,
        model=model,
        timeout_seconds=int(values["timeout_seconds"]),
        extra_body=payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    )


__all__ = ["CHAT_URL", "MODELS_URL", "PRICING_URL", "analyze"]
