"""Runway image remix wrapper."""

from __future__ import annotations

from typing import Any

from ..._common.image_utils import image_to_data_url
from ..._common.provider_utils import consume_kwargs, payload_from_keys
from ..._common.runway_image import submit_runway_image_task
from ..pre_processing import prepare_remix_inputs

API_URL = "/v1/image_to_image"
MODELS_URL = "https://docs.dev.runwayml.com/guides/models/"
PRICING_URL = "https://docs.dev.runwayml.com/guides/pricing/"
_DEFAULTS = {"model": "gen4_image", "base_image": None, "ratio": None, "sync": True, "timeout_seconds": 900}


def remix(prompt: str, reference_images: list[str], **kwargs: Any):
    values, _ = consume_kwargs(dict(kwargs), _DEFAULTS)
    prepared = prepare_remix_inputs(prompt, reference_images, base_image=values["base_image"])
    references = ([prepared.base_image] if prepared.base_image else []) + prepared.reference_images
    payload = {
        "model": values["model"],
        "promptText": prepared.prompt,
        "referenceImages": [image_to_data_url(image) for image in references],
        **payload_from_keys(values, values.get("_provider_kwargs", {}).keys()),
    }
    if values["ratio"]:
        payload["ratio"] = values["ratio"]
    return submit_runway_image_task(
        endpoint=API_URL,
        payload=payload,
        model=values["model"],
        prompt=prepared.prompt,
        sync=bool(values["sync"]),
        timeout_seconds=float(values["timeout_seconds"]),
    )


__all__ = ["API_URL", "MODELS_URL", "PRICING_URL", "remix"]
