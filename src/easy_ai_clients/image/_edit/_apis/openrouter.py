"""OpenRouter edit API wrapper."""

from __future__ import annotations

from ..._common.env_utils import get_provider_api_key
from ..._common.openrouter_utils import edit_image as _edit_image
from ..._common.provider_utils import consume_kwargs, payload_from_keys, provider_error_to_warning
from ..post_processing import build_edit_result
from ..pre_processing import prepare_edit_inputs

_DEFAULTS = {'mask': None, 'aspect_ratio': '1:1', 'output_format': 'png', 'timeout_seconds': 120}
_EXTRA_KEYS = ('max_tokens', 'temperature', 'top_p', 'top_k', 'seed', 'provider', 'image_config', 'response_format', 'structured_outputs', 'transforms')


def edit(prompt: str, image: str, model: str = 'black-forest-labs/flux.2-klein-4b', **kwargs):
    """Edit an image with OpenRouter and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in edit/docs/openrouter_api.md."""

    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_edit_result(warnings=warning)
    extra_body = payload_from_keys(values, ('max_tokens', 'temperature', 'top_p', 'top_k', 'seed', 'provider', 'image_config', 'response_format', 'structured_outputs', 'transforms'))
    if extra_body.pop("fal_payload", None):
        fal_payload = values.get("fal_payload") or {}
        if isinstance(fal_payload, dict):
            extra_body.update(fal_payload)
        else:
            return build_edit_result(warnings="fal_payload must be a dictionary.")
    try:
        prepared = prepare_edit_inputs(prompt, image, provider='openrouter', mask=values["mask"])
        return _edit_image(
            api_key=get_provider_api_key('OpenRouter', 'OPENROUTER_API_KEY'),
            prepared=prepared,
            model=model,
            aspect_ratio=values["aspect_ratio"],
            timeout_seconds=int(values["timeout_seconds"]),
            build_result=build_edit_result,
            extra_body=extra_body,
            image_config=values.get("image_config") if isinstance(values.get("image_config"), dict) else None
        )
    except Exception as exc:
        return build_edit_result(warnings=provider_error_to_warning(exc))


def updateCost(result_dict: dict):
    """Update OpenRouter cost for a previous normalized result."""

    from common.openrouter_utils import update_cost

    return update_cost(
        result_dict,
        api_key=get_provider_api_key('OpenRouter', 'OPENROUTER_API_KEY'),
    )


__all__ = ["edit", "updateCost"]
