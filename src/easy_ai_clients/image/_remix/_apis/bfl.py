"""Black Forest Labs remix API wrapper."""

from __future__ import annotations

from ..._common.bfl_utils import remix_image as _remix_image
from ..._common.env_utils import get_provider_api_key
from ..._common.provider_utils import consume_kwargs, payload_from_keys, provider_error_to_warning
from ..post_processing import build_remix_result
from ..pre_processing import prepare_remix_inputs

_DEFAULTS = {'model': 'flux-2-klein-4b', 'base_image': None, 'output_format': 'png', 'seed': None, 'timeout_seconds': 120}
_EXTRA_KEYS = ('prompt_upsampling', 'safety_tolerance', 'raw', 'guidance', 'steps')


def remix(prompt: str, reference_images: list[str], **kwargs):
    """Generate a reference-guided image with Black Forest Labs and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in remix/docs/black_forest_labs_api.md."""

    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_remix_result(warnings=warning)
    extra_body = payload_from_keys(values, ('prompt_upsampling', 'safety_tolerance', 'raw', 'guidance', 'steps'))
    if extra_body.pop("fal_payload", None):
        fal_payload = values.get("fal_payload") or {}
        if isinstance(fal_payload, dict):
            extra_body.update(fal_payload)
        else:
            return build_remix_result(warnings="fal_payload must be a dictionary.")
    try:
        prepared = prepare_remix_inputs(prompt, reference_images, base_image=values["base_image"])
        return _remix_image(
            api_key=get_provider_api_key('Black Forest Labs', 'BFL_API_KEY'),
            prepared=prepared,
            model=values["model"],
            output_format=values["output_format"],
            timeout_seconds=int(values["timeout_seconds"]),
            build_result=build_remix_result,
            seed=values.get("seed"),
            extra_body=extra_body
        )
    except Exception as exc:
        return build_remix_result(warnings=provider_error_to_warning(exc))

__all__ = ["remix"]
