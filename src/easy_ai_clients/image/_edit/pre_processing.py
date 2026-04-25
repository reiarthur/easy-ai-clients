"""Common preprocessing for `edit` providers."""

from __future__ import annotations

import base64

from .._common.errors import InputValidationError
from .._common.image_utils import (
    full_editable_mask,
    load_image_input,
    normalize_public_mask_asset,
    public_mask_to_bfl_fill,
    public_mask_to_openai,
    public_mask_to_stability,
)
from .._common.types import PreparedEditInputs


def _mask_payload_for_provider(
    provider: str,
    *,
    image_width: int,
    image_height: int,
    mask_input: str | None,
) -> tuple[object | None, bytes | None, str | None, str | None, str]:
    if mask_input is None:
        return None, None, None, None, ""

    raw_mask_asset = load_image_input(mask_input, field_name="mask")
    mask_asset, warning = normalize_public_mask_asset(
        raw_mask_asset,
        width=image_width,
        height=image_height,
    )
    if provider == "openai":
        return (
            mask_asset,
            public_mask_to_openai(mask_asset, width=image_width, height=image_height),
            "image/png",
            "mask.png",
            warning,
        )
    if provider == "bfl_fill":
        return (
            mask_asset,
            public_mask_to_bfl_fill(mask_asset, width=image_width, height=image_height),
            "image/png",
            "mask.png",
            warning,
        )
    if provider == "stability":
        return (
            mask_asset,
            public_mask_to_stability(mask_asset, width=image_width, height=image_height),
            "image/png",
            "mask.png",
            warning,
        )
    return (mask_asset, None, None, None, warning)


def prepare_edit_inputs(
    prompt: str,
    image: str,
    *,
    provider: str,
    mask: str | None = None,
) -> PreparedEditInputs:
    """Normalize the public `edit` contract into provider-ready structures.

    The public contract is intentionally provider-neutral:

    - `image` accepts file path, public image URL, raw base64, or data URL;
    - `mask` is optional;
    - when `mask` is provided, the contract is always `black = editable`,
      `white = protected`.

    This function trims the prompt, normalizes the image, validates and
    binarizes the mask when present, converts the public mask into the provider's
    private format when supported, and records any preprocessing warning that
    should flow back to the public `warnings` field.

    Args:
        prompt: Text instruction for the edit.
        image: Public image input.
        provider: Internal provider discriminator used to choose the private mask
            conversion.
        mask: Optional public mask input.

    Returns:
        :class:`PreparedEditInputs` containing normalized assets, provider mask
        bytes when applicable, and preprocessing warnings.

    Raises:
        InputValidationError: If the prompt is empty or any image input cannot be
            normalized safely.
    """

    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise InputValidationError("prompt must be a non-empty string.")

    image_asset = load_image_input(image, field_name="image")
    (
        mask_asset,
        provider_mask_bytes,
        provider_mask_mime_type,
        provider_mask_filename,
        preprocess_warnings,
    ) = (
        _mask_payload_for_provider(
            provider,
            image_width=image_asset.width,
            image_height=image_asset.height,
            mask_input=mask,
        )
    )

    if provider == "stability" and provider_mask_bytes is None:
        public_full_editable_mask = load_image_input(
            base64.b64encode(
                full_editable_mask(
                    width=image_asset.width,
                    height=image_asset.height,
                )
            ).decode("ascii"),
            field_name="mask",
        )
        provider_mask_bytes = public_mask_to_stability(
            public_full_editable_mask,
            width=image_asset.width,
            height=image_asset.height,
        )
        provider_mask_mime_type = "image/png"
        provider_mask_filename = "auto_full_editable_mask.png"

    return PreparedEditInputs(
        prompt=normalized_prompt,
        image=image_asset,
        mask=mask_asset,
        provider_mask_bytes=provider_mask_bytes,
        provider_mask_mime_type=provider_mask_mime_type,
        provider_mask_filename=provider_mask_filename,
        preprocess_warnings=preprocess_warnings,
    )
