"""Image dispatcher.

Exposes :func:`generate`, :func:`edit`, :func:`remix`, and :func:`analyze` as
the unified entrypoints for every supported provider. The provider is selected
via the ``api`` keyword argument and must match the file name (without ``.py``)
of an internal provider module.

Last updated: 2026-04-25
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
    "generate",
    "edit",
    "remix",
    "analyze",
    "update_cost",
    "available_generate_apis",
    "available_edit_apis",
    "available_remix_apis",
    "available_analyze_apis",
]


_GENERATE_APIS = (
    "bfl",
    "falai",
    "fireworks",
    "google",
    "openai",
    "openrouter",
    "stability",
    "together",
    "xai",
)

_EDIT_APIS = _GENERATE_APIS

_REMIX_APIS = _GENERATE_APIS

_ANALYZE_APIS = (
    "anthropic",
    "falai",
    "fireworks",
    "google",
    "groq",
    "openai",
    "openrouter",
    "together",
    "xai",
)


def available_generate_apis():
    """Return the tuple of supported generate provider identifiers."""

    return _GENERATE_APIS


def available_edit_apis():
    """Return the tuple of supported edit provider identifiers."""

    return _EDIT_APIS


def available_remix_apis():
    """Return the tuple of supported remix provider identifiers."""

    return _REMIX_APIS


def available_analyze_apis():
    """Return the tuple of supported analyze provider identifiers."""

    return _ANALYZE_APIS


def _load_module(operation, api, allowed):
    if not isinstance(api, str) or not api:
        raise ValueError(
            f"image.{operation}(...) requires the keyword argument 'api'. "
            f"Available APIs: {', '.join(allowed)}."
        )
    if api not in allowed:
        raise ValueError(
            f"Unknown image {operation} API '{api}'. Available APIs: "
            f"{', '.join(allowed)}."
        )
    return importlib.import_module(f"._{operation}._apis.{api}", __name__)


def generate(prompt, model=None, *, api, **kwargs):
    """Generate one image from a prompt with the selected provider.

    Returns the normalized contract: `cust_usd`, `base64`, `warnings`,
    `request_id`. Provider-native options can be passed through ``**kwargs``.
    """

    module = _load_module("generate", api, _GENERATE_APIS)
    if model is None:
        return module.generate(prompt, **kwargs)
    return module.generate(prompt, model=model, **kwargs)


def edit(prompt, image, model=None, *, api, **kwargs):
    """Edit one image guided by a prompt and optional mask."""

    module = _load_module("edit", api, _EDIT_APIS)
    if model is None:
        return module.edit(prompt, image, **kwargs)
    return module.edit(prompt, image, model=model, **kwargs)


def remix(prompt, reference_images, model=None, *, api, **kwargs):
    """Remix one prompt with reference images using the selected provider."""

    module = _load_module("remix", api, _REMIX_APIS)
    arguments: dict[str, Any] = dict(kwargs)
    if model is not None:
        arguments["model"] = model
    return module.remix(prompt, reference_images, **arguments)


def analyze(prompt, image, model=None, *, api, **kwargs):
    """Run vision/multimodal analysis with the selected provider."""

    module = _load_module("analyze", api, _ANALYZE_APIS)
    if model is None:
        return module.analyze(prompt, image, **kwargs)
    return module.analyze(prompt, image, model=model, **kwargs)


def update_cost(operation, result, *, api):
    """Refresh `cust_usd` / `cost_usd` from a provider that supports lookups."""

    operation = str(operation or "").strip()
    allowed = {
        "generate": _GENERATE_APIS,
        "edit": _EDIT_APIS,
        "remix": _REMIX_APIS,
        "analyze": _ANALYZE_APIS,
    }
    if operation not in allowed:
        raise ValueError(
            "image.update_cost(...) operation must be one of: "
            f"{', '.join(sorted(allowed))}."
        )
    module = _load_module(operation, api, allowed[operation])
    if not hasattr(module, "update_cost"):
        raise NotImplementedError(
            f"image.update_cost is not implemented for {operation} api='{api}'."
        )
    return module.update_cost(result)
