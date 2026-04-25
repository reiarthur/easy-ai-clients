"""fal.ai analyze API wrapper."""

from __future__ import annotations

from ..._common.env_utils import get_provider_api_key
from ..._common.falai_utils import analyze_image as _analyze_image
from ..._common.provider_utils import (
    consume_kwargs,
    payload_from_keys,
    provider_error_to_warning,
)
from ..post_processing import build_analyze_result
from ..pre_processing import prepare_analyze_inputs

_DEFAULTS = {'vision_endpoint': 'fal-ai/any-llm/vision', 'timeout_seconds': 120}
_EXTRA_KEYS = ('max_tokens', 'temperature', 'top_p', 'system_prompt', 'response_format', 'fal_payload')


def analyze(prompt: str, image: str, model: str = 'google/gemini-2.5-flash-lite', **kwargs):
    """Analyze an image with fal.ai and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in analyze/docs/falai.md."""

    input_text = prompt.strip() if isinstance(prompt, str) else ""
    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_analyze_result(input_text=input_text, output=warning)
    extra_body = payload_from_keys(values, ('max_tokens', 'temperature', 'top_p', 'system_prompt', 'response_format', 'fal_payload'))
    if extra_body.pop("fal_payload", None):
        fal_payload = values.get("fal_payload") or {}
        if isinstance(fal_payload, dict):
            extra_body.update(fal_payload)
        else:
            return build_analyze_result(input_text=input_text, output="fal_payload must be a dictionary.")
    try:
        prepared = prepare_analyze_inputs(prompt, image)
        return _analyze_image(
            api_key=get_provider_api_key('fal.ai', 'FAL_KEY'),
            prepared=prepared,
            model=model,
            timeout_seconds=int(values["timeout_seconds"]),
            build_result=build_analyze_result,
            vision_endpoint=values["vision_endpoint"],
            extra_body=extra_body,
        )
    except Exception as exc:
        return build_analyze_result(input_text=input_text, output=provider_error_to_warning(exc))

__all__ = ["analyze"]
