"""fal.ai edit API wrapper."""

from __future__ import annotations

from ..._common.env_utils import get_provider_api_key
from ..._common.falai_utils import edit_image as _edit_image
from ..._common.provider_utils import consume_kwargs, payload_from_keys, provider_error_to_warning
from ..post_processing import build_edit_result
from ..pre_processing import prepare_edit_inputs

_DEFAULTS = {'mask': None, 'output_format': 'png', 'seed': None, 'timeout_seconds': 180}
_EXTRA_KEYS = ('num_images', 'image_size', 'guidance_scale', 'num_inference_steps', 'enable_safety_checker', 'sync_mode', 'fal_payload')


def edit(prompt: str, image: str, model: str = 'fal-ai/flux-pro/kontext', **kwargs):
    """Edit an image with fal.ai and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in edit/docs/falai.md."""

    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_edit_result(warnings=warning)
    extra_body = payload_from_keys(values, ('num_images', 'image_size', 'guidance_scale', 'num_inference_steps', 'enable_safety_checker', 'sync_mode', 'fal_payload'))
    if extra_body.pop("fal_payload", None):
        fal_payload = values.get("fal_payload") or {}
        if isinstance(fal_payload, dict):
            extra_body.update(fal_payload)
        else:
            return build_edit_result(warnings="fal_payload must be a dictionary.")
    try:
        prepared = prepare_edit_inputs(prompt, image, provider='falai', mask=values["mask"])
        return _edit_image(
            api_key=get_provider_api_key('fal.ai', 'FAL_KEY'),
            prepared=prepared,
            model=model,
            output_format=values["output_format"],
            timeout_seconds=int(values["timeout_seconds"]),
            build_result=build_edit_result,
            seed=values.get("seed"),
            extra_body=extra_body
        )
    except Exception as exc:
        return build_edit_result(warnings=provider_error_to_warning(exc))

__all__ = ["edit"]
