"""Common preprocessing for `remix` providers."""

from __future__ import annotations

from .._common.errors import InputValidationError
from .._common.image_utils import load_image_input, load_image_inputs
from .._common.types import PreparedRemixInputs, ReferenceImagesInput


def prepare_remix_inputs(
    prompt: str,
    reference_images: ReferenceImagesInput,
    *,
    base_image: str | None = None,
) -> PreparedRemixInputs:
    """Normalize the public `remix` contract into structured image assets.

    Args:
        prompt: Text instruction guiding the new generated image.
        reference_images: Non-empty list of images used as references. Each item
            accepts file path, public image URL, raw base64, or data URL.
        base_image: Optional image whose identity/composition should be preserved
            when the provider supports a distinct base/anchor image concept.

    Returns:
        :class:`PreparedRemixInputs` with trimmed prompt, normalized reference
        list, and optional normalized base image.

    Raises:
        InputValidationError: If the prompt is empty or any image input cannot be
            normalized safely.
    """

    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise InputValidationError("prompt must be a non-empty string.")
    if isinstance(reference_images, str):
        raise InputValidationError("reference_images must be a non-empty list of image inputs.")

    references = load_image_inputs(reference_images, field_name="reference_images")
    return PreparedRemixInputs(
        prompt=normalized_prompt,
        reference_images=references,
        base_image=load_image_input(base_image, field_name="base_image")
        if base_image is not None
        else None,
    )
