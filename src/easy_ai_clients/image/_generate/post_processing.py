"""Common post-processing for `generate` providers."""

from __future__ import annotations

from decimal import Decimal

from .._common.provider_utils import image_result
from .._common.types import ImageOperationResult


def build_generate_result(
    *,
    base64_value: str = "",
    warnings: str = "",
    cust_usd: Decimal | float = 0.0,
    request_id: str = "",
) -> ImageOperationResult:
    """Build the normalized public result for `generate`.

    Args:
        base64_value: Pure base64 image payload, usually PNG-normalized.
        warnings: Public warning text. Non-empty warnings do not necessarily mean
            hard failure if `base64_value` is still present.
        cust_usd: Exact or safest-known USD cost.
        request_id: Provider request/job id, or `""`.

    Returns:
        Dictionary containing exactly `cust_usd`, `base64`, `warnings`, and
        `request_id`.
    """

    return image_result(
        base64_value=base64_value,
        warnings=warnings,
        cust_usd=cust_usd,
        request_id=request_id,
    )
