"""Google Gemini edit API wrapper."""

from __future__ import annotations

from ..._common.env_utils import get_provider_api_key
from ..._common.gemini_utils import edit_image as _edit_image
from ..._common.provider_utils import consume_kwargs, payload_from_keys, provider_error_to_warning
from ..post_processing import build_edit_result
from ..pre_processing import prepare_edit_inputs

_DEFAULTS = {'mask': None, 'aspect_ratio': '1:1', 'output_format': 'png', 'timeout_seconds': 120}
_EXTRA_KEYS = ('temperature', 'topP', 'topK', 'candidateCount', 'seed', 'imageConfig')


def edit(prompt: str, image: str, model: str = 'gemini-2.5-flash-image', **kwargs):
    """Edit an image with Google Gemini and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in edit/docs/google_gemini_api.md."""

    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_edit_result(warnings=warning)
    generation_config = payload_from_keys(values, ('temperature', 'topP', 'topK', 'candidateCount', 'seed', 'imageConfig'))
    if values.get("imageConfig"):
        generation_config["imageConfig"] = values["imageConfig"]
    try:
        prepared = prepare_edit_inputs(prompt, image, provider='google_gemini', mask=values["mask"])
        return _edit_image(
            api_key=get_provider_api_key('Google Gemini', 'GOOGLE_API_KEY'),
            prepared=prepared,
            model=model,
            aspect_ratio=values["aspect_ratio"],
            output_format=values["output_format"],
            timeout_seconds=int(values["timeout_seconds"]),
            build_result=build_edit_result,
            generation_config=generation_config
        )
    except Exception as exc:
        return build_edit_result(warnings=provider_error_to_warning(exc))

__all__ = ["edit"]
