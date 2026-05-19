"""Runway text-to-image wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.runway_image import submit_runway_image_task
from ..pre_processing import prepare_generate_inputs

API_URL = "/v1/text_to_image"
MODELS_URL = "https://docs.dev.runwayml.com/guides/models/"
PRICING_URL = "https://docs.dev.runwayml.com/guides/pricing/"
_DEFAULTS = {"ratio": "1024:1024", "sync": True, "timeout_seconds": 900}


def generate(prompt: str, model: str = "gen4_image", **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    prepared = prepare_generate_inputs(prompt)
    payload = {
        "model": model,
        "promptText": prepared.prompt,
        "ratio": values["ratio"],
        **payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    }
    return submit_runway_image_task(
        endpoint=API_URL,
        payload=payload,
        model=model,
        prompt=prepared.prompt,
        sync=bool(values["sync"]),
        timeout_seconds=float(values["timeout_seconds"]),
    )


__all__ = ["API_URL", "MODELS_URL", "PRICING_URL", "generate"]
