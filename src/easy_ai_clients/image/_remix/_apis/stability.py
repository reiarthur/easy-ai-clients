"""Stability AI remix API wrapper."""

from __future__ import annotations

from ..._common.env_utils import get_provider_api_key
from ..._common.provider_utils import consume_kwargs, payload_from_keys, provider_error_to_warning
from ..._common.stability_utils import remix_image as _remix_image
from ..post_processing import build_remix_result
from ..pre_processing import prepare_remix_inputs

_DEFAULTS = {'model': 'stable-image-style', 'base_image': None, 'aspect_ratio': '1:1', 'output_format': 'png', 'seed': None, 'timeout_seconds': 120}
_EXTRA_KEYS = ('style_preset', 'cfg_scale', 'grow_mask', 'creativity', 'fidelity', 'finish_reason')


def remix(prompt: str, reference_images: list[str], **kwargs):
    """Generate a reference-guided image with Stability AI and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in remix/docs/stability_ai_api.md."""

    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_remix_result(warnings=warning)
    extra_form = payload_from_keys(values, ('style_preset', 'cfg_scale', 'grow_mask', 'creativity', 'fidelity', 'finish_reason'))
    try:
        prepared = prepare_remix_inputs(prompt, reference_images, base_image=values["base_image"])
        return _remix_image(
            api_key=get_provider_api_key('Stability AI', 'STABILITY_API_KEY'),
            prepared=prepared,
            model=values["model"],
            aspect_ratio=values["aspect_ratio"],
            output_format=values["output_format"],
            timeout_seconds=int(values["timeout_seconds"]),
            build_result=build_remix_result,
            seed=values.get("seed"),
            extra_form=extra_form
        )
    except Exception as exc:
        return build_remix_result(warnings=provider_error_to_warning(exc))

__all__ = ["remix"]
