"""Fireworks AI generate API wrapper."""

from __future__ import annotations

from ..._common.env_utils import get_provider_api_key
from ..._common.fireworks_utils import generate_image as _generate_image
from ..._common.provider_utils import consume_kwargs, payload_from_keys, provider_error_to_warning
from ..post_processing import build_generate_result
from ..pre_processing import prepare_generate_inputs

_DEFAULTS = {'aspect_ratio': '1:1', 'output_format': 'png', 'steps': 4, 'seed': None, 'timeout_seconds': 120}
_EXTRA_KEYS = ('strength', 'prompt_upsampling', 'safety_tolerance', 'guidance_scale')


def generate(prompt: str, model: str = 'flux-1-schnell-fp8', **kwargs):
    """Generate an image with Fireworks AI and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in generate/docs/fireworks_ai_api.md."""

    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_generate_result(warnings=warning)
    extra_body = payload_from_keys(values, ('strength', 'prompt_upsampling', 'safety_tolerance', 'guidance_scale'))
    if extra_body.pop("fal_payload", None):
        fal_payload = values.get("fal_payload") or {}
        if isinstance(fal_payload, dict):
            extra_body.update(fal_payload)
        else:
            return build_generate_result(warnings="fal_payload must be a dictionary.")
    try:
        prepared = prepare_generate_inputs(prompt)
        return _generate_image(
            api_key=get_provider_api_key('Fireworks AI', 'FIREWORKS_API_KEY'),
            prepared=prepared,
            model=model,
            aspect_ratio=values["aspect_ratio"],
            output_format=values["output_format"],
            timeout_seconds=int(values["timeout_seconds"]),
            build_result=build_generate_result,
            seed=values.get("seed"),
            extra_body=extra_body,
            steps=int(values["steps"]) if values.get("steps") is not None else None
        )
    except Exception as exc:
        return build_generate_result(warnings=provider_error_to_warning(exc))

__all__ = ["generate"]
