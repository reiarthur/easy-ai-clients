"""Common post-processing for `edit` providers."""

from __future__ import annotations

from decimal import Decimal

from .._common.provider_utils import image_result
from .._common.types import ImageOperationResult


def build_edit_result(
    *,
    base64_value: str = "",
    warnings: str = "",
    cust_usd: Decimal | float = 0.0,
    request_id: str = "",
) -> ImageOperationResult:
    """Build the normalized public result for `edit`.

    Args:
        base64_value: Pure base64 image payload, or `""` when the edit failed or
            was blocked.
        warnings: Public warning text, including unsupported-feature,
            moderation, billing, or preprocessing notes.
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
