"""Anthropic Claude analyze API wrapper."""

from __future__ import annotations

import base64

from ..._common.cost_utils import extract_anthropic_usage_cost
from ..._common.env_utils import get_provider_api_key
from ..._common.http_utils import request
from ..._common.provider_utils import (
    consume_kwargs,
    detect_block,
    extract_request_id,
    payload_from_keys,
    provider_error_to_warning,
    response_json,
)
from ..post_processing import build_analyze_result
from ..pre_processing import prepare_analyze_inputs

_DEFAULTS = {'max_tokens': 1024, 'timeout_seconds': 60}
_EXTRA_KEYS = ('max_tokens', 'temperature', 'top_p', 'top_k', 'system', 'stop_sequences', 'metadata', 'tools', 'tool_choice', 'thinking')


def analyze(prompt: str, image: str, model: str = 'claude-haiku-4-5-20251001', **kwargs):
    """Analyze an image with Anthropic Claude and return the normalized public contract.

Standardized public wrapper. Required image inputs accept local file paths, raw
base64 image strings, data URLs, and public HTTP(S) image URLs. Optional provider
parameters are supplied through **kwargs. Full model, pricing, parameter, and
validation details are documented in analyze/docs/claude_api.md."""

    input_text = prompt.strip() if isinstance(prompt, str) else ""
    values, warning = consume_kwargs(dict(kwargs), _DEFAULTS, passthrough_keys=_EXTRA_KEYS)
    if warning:
        return build_analyze_result(input_text=input_text, output=warning)
    extra_body = payload_from_keys(values, _EXTRA_KEYS)
    max_tokens = int(values.pop("max_tokens", 1024) or 1024)
    extra_body.pop("max_tokens", None)
    try:
        prepared = prepare_analyze_inputs(prompt, image)
        request_body = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64.b64encode(prepared.image.raw_bytes).decode("ascii"),
                            },
                        },
                        {"type": "text", "text": prepared.prompt},
                    ],
                }
            ],
        }
        request_body.update(extra_body)
        response = request(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": get_provider_api_key('Claude API', 'ANTHROPIC_API_KEY'),
                "anthropic-version": "2023-06-01",
            },
            json=request_body,
            timeout_seconds=int(values["timeout_seconds"]),
        )
        payload = response_json(response)
        blocked = detect_block(payload, operation="analyze")
        request_id = extract_request_id(response, payload)
        if blocked is not None:
            return build_analyze_result(request_id=request_id or blocked.request_id, cost_usd=blocked.cust_usd, input_text=prepared.prompt, output=blocked.warning)
        text_blocks = [str(block["text"]) for block in payload.get("content", []) if isinstance(block, dict) and block.get("type") == "text" and block.get("text")]
        return build_analyze_result(request_id=request_id, cost_usd=extract_anthropic_usage_cost(model, payload.get("usage")) or 0.0, input_text=prepared.prompt, output="\n".join(text_blocks).strip() or "Claude did not return textual output for the analyze request.")
    except Exception as exc:
        return build_analyze_result(input_text=input_text, output=provider_error_to_warning(exc))


__all__ = ["analyze"]
