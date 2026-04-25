"""Groq analyze API wrapper."""

from __future__ import annotations

from ..._common.cost_utils import extract_groq_usage_cost
from ..._common.env_utils import get_provider_api_key
from ..._common.http_utils import request
from ..._common.image_utils import image_to_data_url
from ..._common.provider_utils import (
    consume_kwargs,
    detect_block,
    extract_request_id,
    extract_text_from_openai_style_response,
    payload_from_keys,
    provider_error_to_warning,
    response_json,
)
from ..post_processing import build_analyze_result
from ..pre_processing import prepare_analyze_inputs

_DEFAULTS = {'service_tier': 'flex', 'timeout_seconds': 60}
_EXTRA_KEYS = ('max_output_tokens', 'temperature', 'top_p', 'metadata', 'user', 'instructions', 'store', 'tools', 'tool_choice')


def analyze(prompt: str, image: str, model: str = 'meta-llama/llama-4-scout-17b-16e-instruct', **kwargs):
    """Analyze an image with Groq and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in analyze/docs/groq_api.md."""

    input_text = prompt.strip() if isinstance(prompt, str) else ""
    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_analyze_result(input_text=input_text, output=warning)
    extra_body = payload_from_keys(values, _EXTRA_KEYS)
    extra_body.pop("service_tier", None)
    try:
        prepared = prepare_analyze_inputs(prompt, image)
        request_body = {
            "model": model,
            "service_tier": values["service_tier"],
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prepared.prompt},
                        {"type": "input_image", "image_url": image_to_data_url(prepared.image)},
                    ],
                }
            ],
        }
        request_body.update(extra_body)
        response = request(
            "POST",
            "https://api.groq.com/openai/v1/responses",
            headers={"Authorization": f"Bearer {get_provider_api_key('Groq', 'GROQ_API_KEY')}"},
            json=request_body,
            timeout_seconds=int(values["timeout_seconds"]),
        )
        payload = response_json(response)
        blocked = detect_block(payload, operation="analyze")
        request_id = extract_request_id(response, payload)
        if blocked is not None:
            return build_analyze_result(request_id=request_id or blocked.request_id, cost_usd=blocked.cust_usd, input_text=prepared.prompt, output=blocked.warning)
        output = extract_text_from_openai_style_response(payload).strip()
        return build_analyze_result(request_id=request_id, cost_usd=extract_groq_usage_cost(model, payload.get("usage")) or 0.0, input_text=prepared.prompt, output=output or "Groq did not return textual output for the analyze request.")
    except Exception as exc:
        return build_analyze_result(input_text=input_text, output=provider_error_to_warning(exc))


__all__ = ["analyze"]
