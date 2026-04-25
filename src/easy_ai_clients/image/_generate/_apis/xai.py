"""xAI generate API wrapper."""

from __future__ import annotations

from ..._common.env_utils import get_provider_api_key
from ..._common.provider_utils import consume_kwargs, payload_from_keys, provider_error_to_warning
from ..._common.xai_utils import generate_image as _generate_image
from ..post_processing import build_generate_result
from ..pre_processing import prepare_generate_inputs

_DEFAULTS = {'aspect_ratio': '1:1', 'output_format': 'png', 'timeout_seconds': 120}
_EXTRA_KEYS = ('n', 'response_format', 'user')


def generate(prompt: str, model: str = 'grok-imagine-image', **kwargs):
    """Generate an image with xAI and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in generate/docs/xai_api.md."""

    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_generate_result(warnings=warning)
    extra_body = payload_from_keys(values, ('n', 'response_format', 'user'))
    if extra_body.pop("fal_payload", None):
        fal_payload = values.get("fal_payload") or {}
        if isinstance(fal_payload, dict):
            extra_body.update(fal_payload)
        else:
            return build_generate_result(warnings="fal_payload must be a dictionary.")
    try:
        prepared = prepare_generate_inputs(prompt)
        return _generate_image(
            api_key=get_provider_api_key('xAI', 'XAI_API_KEY'),
            prepared=prepared,
            model=model,
            aspect_ratio=values["aspect_ratio"],
            timeout_seconds=int(values["timeout_seconds"]),
            build_result=build_generate_result,
            extra_body=extra_body
        )
    except Exception as exc:
        return build_generate_result(warnings=provider_error_to_warning(exc))

__all__ = ["generate"]
