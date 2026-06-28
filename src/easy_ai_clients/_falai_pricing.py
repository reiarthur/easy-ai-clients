"""Shared fal.ai pricing helpers."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

FAL_API_BASE_URL = "https://api.fal.ai/v1"
FAL_ESTIMATE_OPTIONS = {"billing_unit_quantity", "unit_quantity"}


def fal_estimate_unit_price(model, unit_quantity, api_key, timeout_seconds=None):
    """Estimate fal.ai cost through the official pricing estimate API.

    Args:
        model: Required. fal.ai endpoint id, for example `fal-ai/flux/schnell`.
        unit_quantity: Required. Quantity sent to the fal.ai `unit_price`
            estimate request. It must be greater than zero.
        api_key: Required. fal.ai API key.
        timeout_seconds: Optional. Request timeout. Defaults to 60 seconds.

    Returns:
        Cost metadata using the normalized library fields. The returned cost is
        an official fal.ai estimate, not a post-run billing reconciliation.

    Raises:
        ValueError: If `unit_quantity` is not greater than zero.
        RuntimeError: If the pricing endpoint does not return `total_cost`.
    """

    quantity = float(unit_quantity)
    if quantity <= 0:
        raise ValueError(
            "billing_unit_quantity/unit_quantity must be greater than zero for "
            "fal.ai pricing estimates."
        )

    estimate_url = FAL_API_BASE_URL + "/models/pricing/estimate"
    raw = _http_json(
        "POST",
        estimate_url,
        headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
        payload={
            "estimate_type": "unit_price",
            "endpoints": {model: {"unit_quantity": quantity}},
        },
        timeout_seconds=timeout_seconds,
    )
    if "total_cost" not in raw:
        raise RuntimeError("fal.ai pricing estimate did not return total_cost.")

    return {
        "cost_usd": float(raw["total_cost"]),
        "cost_currency": "USD",
        "cost_is_estimated": True,
        "cost_source": "fal_pricing_estimate_api",
        "cost_reason": (
            "fal.ai pricing estimate API was used with unit_price estimation; "
            "live billing reconciliation is not performed by this helper."
        ),
        "cost_details": {
            "estimate_type": "unit_price",
            "unit_quantity": quantity,
            "pricing_endpoint": estimate_url,
            "pricing_estimate": raw,
        },
        "pricing_estimate": raw,
    }


def fal_pricing_estimate(
    model,
    kwargs,
    api_key,
    timeout_seconds=None,
    default_unit_quantity=None,
):
    """Return fal.ai estimate metadata, or unavailable metadata on lookup failure.

    Args:
        model: Required. fal.ai endpoint id.
        kwargs: Required. Caller kwargs. `billing_unit_quantity` is preferred
            over `unit_quantity` when both are present.
        api_key: Required. fal.ai API key.
        timeout_seconds: Optional. Pricing request timeout.
        default_unit_quantity: Optional. Quantity to estimate when the caller
            did not provide `billing_unit_quantity` or `unit_quantity`.

    Returns:
        A normalized cost metadata dictionary, or `None` when no quantity is
        available.
    """

    quantity = _unit_quantity_from_kwargs(kwargs, default_unit_quantity)
    if quantity is None:
        return None
    try:
        return fal_estimate_unit_price(
            model,
            quantity,
            api_key,
            timeout_seconds=timeout_seconds or (kwargs or {}).get("timeout_seconds"),
        )
    except Exception as exc:
        reason = f"fal.ai pricing estimate API was unavailable for `{model}`: {exc}"
        return {
            "cost_usd": 0.0,
            "cost_currency": "USD",
            "cost_is_estimated": True,
            "cost_source": "unavailable",
            "cost_reason": reason,
            "cost_details": {"cost_lookup_error": reason},
        }


def _unit_quantity_from_kwargs(kwargs, default_unit_quantity=None):
    """Resolve the fal.ai estimate quantity from explicit or default inputs."""

    values = kwargs or {}
    quantity = values.get("billing_unit_quantity", values.get("unit_quantity"))
    if quantity is None:
        quantity = default_unit_quantity
    if quantity is None:
        return None
    value = float(quantity)
    if value <= 0:
        raise ValueError(
            "billing_unit_quantity/unit_quantity must be greater than zero for "
            "fal.ai pricing estimates."
        )
    return value


def _http_json(method, url, headers=None, payload=None, timeout_seconds=None):
    """Call a JSON HTTP endpoint using only stdlib primitives."""

    request_headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(
        url,
        data=data,
        headers=request_headers,
        method=str(method).upper(),
    )
    try:
        with urllib.request.urlopen(request, timeout=float(timeout_seconds or 60)) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = " ".join(body[:1200].split()) or str(exc)
        raise RuntimeError(f"HTTP {exc.code} from {url}: {message}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc.reason}") from exc
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))
