"""fal.ai pricing helpers for video operations."""

from ._shared import fal_estimate_unit_price, require_env

FAL_ESTIMATE_OPTIONS = {"billing_unit_quantity", "unit_quantity"}


def fal_pricing_estimate(model, kwargs, env_name):
    quantity = kwargs.get("billing_unit_quantity", kwargs.get("unit_quantity"))
    if quantity is None:
        return None
    value = float(quantity)
    if value <= 0:
        raise ValueError("billing_unit_quantity/unit_quantity must be greater than zero for fal.ai pricing estimates.")
    try:
        api_key = require_env(env_name, "fal.ai")
        return fal_estimate_unit_price(
            model,
            value,
            api_key,
            timeout_seconds=kwargs.get("timeout_seconds"),
        )
    except Exception as exc:
        return {
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "unavailable",
            "cost_reason": f"fal.ai pricing estimate API was unavailable for `{model}`: {exc}",
        }
