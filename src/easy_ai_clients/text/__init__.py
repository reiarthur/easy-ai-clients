"""Text-in / text-out dispatcher.

Exposes :func:`generate` as the unified entrypoint for every supported
provider. The provider is selected by the ``api`` argument and must match the
file name (without ``.py``) of an internal provider module.

Last updated: 2026-04-25
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = ["generate", "list_models", "update_cost", "available_apis"]


_AVAILABLE_APIS = (
    "anthropic",
    "cohere",
    "deepinfra",
    "deepseek",
    "fal",
    "fireworks",
    "google",
    "groq",
    "huggingface",
    "mistral",
    "openai",
    "openrouter",
    "together",
    "xai",
)


def available_apis():
    """Return the tuple of supported provider identifiers for ``api``."""

    return _AVAILABLE_APIS


def _load(api):
    """Import the provider module identified by ``api``."""
    if not isinstance(api, str) or not api:
        raise ValueError(
            "text.generate(...) requires the keyword argument 'api' set to a "
            f"provider identifier. Available APIs: {', '.join(_AVAILABLE_APIS)}."
        )
    if api not in _AVAILABLE_APIS:
        raise ValueError(
            f"Unknown text API '{api}'. Available APIs: "
            f"{', '.join(_AVAILABLE_APIS)}."
        )
    return importlib.import_module(f"._apis.{api}", __name__)


def generate(input_text, instruction=None, model=None, *, api, **kwargs):
    """Generate text with the selected provider.

    ### Parameters:
    - input_text (str): User prompt sent to the provider.
    - instruction (str | None): Optional system instruction.
    - model (str | None): Provider-specific model identifier. When omitted, the
      provider default is used.
    - api (str): Provider identifier. Must match a supported value listed by
      :func:`available_apis`.
    - **kwargs: Extra provider-native parameters forwarded to the underlying
      provider call.

    ### Returns:
    - dict: Normalized result with `request_id`, `cost_source`, `cost_usd`,
      `input_text`, optional `instruction`, and `output_text`.
    """

    module = _load(api)
    if model is None:
        return module.generate(input_text, instruction=instruction, **kwargs)
    return module.generate(input_text, instruction=instruction, model=model, **kwargs)


def list_models(*, api: str, **kwargs: Any):
    """List the catalog models exposed by the selected provider."""

    module = _load(api)
    if not hasattr(module, "list_models"):
        raise NotImplementedError(
            f"text.list_models is not implemented for api='{api}'."
        )
    return module.list_models(**kwargs)


def update_cost(result, *, api):
    """Update ``cost_usd`` of a previous generate result when the provider supports it."""

    module = _load(api)
    if not hasattr(module, "update_cost"):
        raise NotImplementedError(
            f"text.update_cost is not implemented for api='{api}'."
        )
    return module.update_cost(result)
