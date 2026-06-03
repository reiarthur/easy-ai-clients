def unavailable_cost_metadata(source=None, details=None):
    """Return empty cost metadata for providers without public cost details.

    Args:
        source: Optional. Cost metadata source.
        details: Optional. Additional details.

    Returns:
        A dictionary with normalized cost fields.
    """
    return {
        "cost_usd": 0.0,
        "cost_currency": "USD",
        "cost_is_estimated": False,
        "cost_source": "unavailable",
        "cost_details": details or {},
    }


def normalize_cost(cost_usd=None, source=None, is_estimated=False, details=None):
    """Return normalized cost metadata.

    Args:
        cost_usd: Optional. Cost in USD.
        source: Optional. Cost metadata source.
        is_estimated: Optional. Whether the cost is estimated.
        details: Optional. Additional provider-specific cost details.

    Returns:
        A dictionary with normalized cost fields.
    """
    amount = _to_number(cost_usd)
    if amount is None:
        return unavailable_cost_metadata(details=details)

    return {
        "cost_usd": amount,
        "cost_currency": "USD",
        "cost_is_estimated": bool(is_estimated),
        "cost_source": source or "unavailable",
        "cost_details": details or {},
    }


def cost_from_response(response, source=None):
    """Extract common cost metadata from a provider response.

    Args:
        response: Required. Provider response.
        source: Optional. Cost metadata source.

    Returns:
        A dictionary with normalized cost fields.
    """
    cost = _find_first(response, ("cost_usd", "usd", "price_usd"))
    if cost is None:
        cost = _find_first(response, ("cost", "price", "amount"))

    source = source or _find_first(response, ("cost_source", "billing_source"))
    estimated = _find_first(response, ("cost_is_estimated", "is_estimated", "estimated"))
    details = _find_first(response, ("cost_details", "billing", "usage"))

    if (
        isinstance(response, dict)
        and response.get("cost_source") == "unavailable"
        and "cost_usd" in response
        and cost == response.get("cost_usd")
    ):
        return unavailable_cost_metadata(details=details)

    if cost is None:
        return unavailable_cost_metadata(details=details)

    if source in (None, "", "unavailable"):
        source = "provider_response"

    return normalize_cost(
        cost,
        source=source,
        is_estimated=bool(estimated) if estimated is not None else False,
        details=details,
    )


def apply_cost_metadata(result, cost):
    """Apply normalized cost metadata to a result dictionary.

    Args:
        result: Required. Result dictionary to update.
        cost: Required. Normalized cost metadata.

    Returns:
        The updated result.
    """
    if not isinstance(result, dict):
        return result

    result["cost_usd"] = cost.get("cost_usd", 0.0)
    result["cost_currency"] = cost.get("cost_currency", "USD")
    result["cost_is_estimated"] = bool(cost.get("cost_is_estimated", False))
    result["cost_source"] = cost.get("cost_source") or "unavailable"
    result["cost_details"] = cost.get("cost_details") or {}
    return result


def has_available_cost(cost):
    """Return whether cost metadata contains an available cost source.

    Args:
        cost: Required. Cost metadata dictionary.

    Returns:
        True when the source is not unavailable.
    """
    return isinstance(cost, dict) and cost.get("cost_source") not in (None, "unavailable")


def _find_first(value, keys):
    """Find the first matching value in nested dictionaries and lists.

    Args:
        value: Required. Response content.
        keys: Required. Candidate keys.

    Returns:
        The first matching value, or None.
    """
    if isinstance(value, dict):
        for key in keys:
            if key in value and value[key] is not None:
                return value[key]
        for item in value.values():
            found = _find_first(item, keys)
            if found is not None:
                return found
    elif isinstance(value, list | tuple):
        for item in value:
            found = _find_first(item, keys)
            if found is not None:
                return found
    return None


def _to_number(value):
    """Convert a value to a float when possible.

    Args:
        value: Required. Value to convert.

    Returns:
        A float or None.
    """
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None
