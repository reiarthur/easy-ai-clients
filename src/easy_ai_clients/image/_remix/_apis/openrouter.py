"""OpenRouter remix API wrapper."""

from __future__ import annotations

from ..._common.env_utils import get_provider_api_key
from ..._common.openrouter_utils import remix_image as _remix_image
from ..._common.provider_utils import consume_kwargs, payload_from_keys, provider_error_to_warning
from ..post_processing import build_remix_result
from ..pre_processing import prepare_remix_inputs

_DEFAULTS = {'model': 'black-forest-labs/flux.2-klein-4b', 'base_image': None, 'aspect_ratio': '1:1', 'output_format': 'png', 'timeout_seconds': 120}
_EXTRA_KEYS = ('max_tokens', 'temperature', 'top_p', 'top_k', 'seed', 'provider', 'image_config', 'response_format', 'structured_outputs', 'transforms')


def remix(prompt: str, reference_images: list[str], **kwargs):
    """Generate a reference-guided image with OpenRouter and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in remix/docs/openrouter_api.md."""

    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_remix_result(warnings=warning)
    extra_body = payload_from_keys(values, ('max_tokens', 'temperature', 'top_p', 'top_k', 'seed', 'provider', 'image_config', 'response_format', 'structured_outputs', 'transforms'))
    if extra_body.pop("fal_payload", None):
        fal_payload = values.get("fal_payload") or {}
        if isinstance(fal_payload, dict):
            extra_body.update(fal_payload)
        else:
            return build_remix_result(warnings="fal_payload must be a dictionary.")
    try:
        prepared = prepare_remix_inputs(prompt, reference_images, base_image=values["base_image"])
        return _remix_image(
            api_key=get_provider_api_key('OpenRouter', 'OPENROUTER_API_KEY'),
            prepared=prepared,
            model=values["model"],
            aspect_ratio=values["aspect_ratio"],
            timeout_seconds=int(values["timeout_seconds"]),
            build_result=build_remix_result,
            extra_body=extra_body,
            image_config=values.get("image_config") if isinstance(values.get("image_config"), dict) else None
        )
    except Exception as exc:
        return build_remix_result(warnings=provider_error_to_warning(exc))


def updateCost(result_dict: dict):
    """Update OpenRouter cost for a previous normalized result."""

    from common.openrouter_utils import update_cost

    return update_cost(
        result_dict,
        api_key=get_provider_api_key('OpenRouter', 'OPENROUTER_API_KEY'),
    )


__all__ = ["remix", "updateCost"]
