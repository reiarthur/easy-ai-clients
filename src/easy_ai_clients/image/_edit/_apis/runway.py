"""Runway image editing wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.image_utils import image_to_data_url
from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.runway_image import submit_runway_image_task
from ..pre_processing import prepare_edit_inputs

API_URL = "/v1/image_to_image"
MODELS_URL = "https://docs.dev.runwayml.com/guides/models/"
PRICING_URL = "https://docs.dev.runwayml.com/guides/pricing/"
_DEFAULTS = {"mask": None, "ratio": None, "sync": True, "timeout_seconds": 900}


def edit(prompt: str, image: str, model: str = "gen4_image", **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    prepared = prepare_edit_inputs(prompt, image, provider="openai", mask=values["mask"])
    payload = {
        "model": model,
        "promptText": prepared.prompt,
        "referenceImage": image_to_data_url(prepared.image),
        **payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    }
    if values["ratio"]:
        payload["ratio"] = values["ratio"]
    return submit_runway_image_task(
        endpoint=API_URL,
        payload=payload,
        model=model,
        prompt=prepared.prompt,
        sync=bool(values["sync"]),
        timeout_seconds=float(values["timeout_seconds"]),
    )


__all__ = ["API_URL", "MODELS_URL", "PRICING_URL", "edit"]
