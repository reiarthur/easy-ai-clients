"""Common preprocessing for `generate` providers."""

from __future__ import annotations

from .._common.errors import InputValidationError
from .._common.types import PreparedGenerateInputs


def prepare_generate_inputs(prompt: str) -> PreparedGenerateInputs:
    """Validate and normalize the public `generate` prompt.

    Args:
        prompt: Natural-language prompt used for text-to-image generation.

    Returns:
        :class:`PreparedGenerateInputs` with trimmed prompt text.

    Raises:
        InputValidationError: If the prompt is empty after trimming.
    """

    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise InputValidationError("prompt must be a non-empty string.")
    return PreparedGenerateInputs(prompt=normalized_prompt)
