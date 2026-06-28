"""fal.ai image pricing helpers."""

from __future__ import annotations

from ..._falai_pricing import fal_pricing_estimate


def fal_image_pricing_estimate(model, values, extra_body, api_key):
    """Estimate fal.ai image generation cost using the official pricing API.

    Args:
        model: Required. fal.ai endpoint id used for the image operation.
        values: Required. Normalized adapter kwargs.
        extra_body: Required. Provider payload after `fal_payload` was merged.
        api_key: Required. fal.ai API key.

    Returns:
        Normalized cost metadata. The cost is an official pre-run estimate, not
        the final billing event for the request.
    """

    pricing_values = dict(values or {})
    pricing_values.update(dict(extra_body or {}))
    return fal_pricing_estimate(
        model,
        pricing_values,
        api_key=api_key,
        timeout_seconds=pricing_values.get("timeout_seconds"),
        default_unit_quantity=_default_image_unit_quantity(pricing_values),
    )


def _default_image_unit_quantity(values):
    """Use the requested image count as the default fal.ai pricing quantity."""

    try:
        count = float((values or {}).get("num_images") or 1)
    except (TypeError, ValueError):
        count = 1.0
    return max(count, 1.0)
