"""Common preprocessing for `analyze` providers."""

from __future__ import annotations

from .._common.errors import InputValidationError
from .._common.image_utils import load_image_input
from .._common.types import PreparedAnalyzeInputs


def prepare_analyze_inputs(prompt: str, image: str) -> PreparedAnalyzeInputs:
    """Validate and normalize the public `analyze` inputs.

    Args:
        prompt: Image-understanding instruction.
        image: Public image input accepted as path, public image URL, raw
            base64, or data URL.

    Returns:
        :class:`PreparedAnalyzeInputs` with trimmed prompt and normalized image.

    Raises:
        InputValidationError: If the prompt is empty or the image cannot be
            normalized safely.
    """

    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise InputValidationError("prompt must be a non-empty string.")
    return PreparedAnalyzeInputs(
        prompt=normalized_prompt,
        image=load_image_input(image, field_name="image"),
    )
