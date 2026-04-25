"""Helpers da xAI para operações de imagem e visão.

Última atualização: 2026-04-23
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from .._analyze.post_processing import build_analyze_result
from .cost_utils import usd_ticks_to_decimal
from .http_utils import request
from .image_utils import image_to_data_url
from .provider_utils import (
    detect_block,
    download_image_as_base64_png,
    extract_request_id,
    extract_text_from_openai_style_response,
    join_warnings,
    normalize_base64_image_to_png,
    provider_error_to_warning,
    response_json,
)
from .types import (
    AnalyzeOperationResult,
    ImageOperationResult,
    PreparedAnalyzeInputs,
    PreparedEditInputs,
    PreparedGenerateInputs,
    PreparedRemixInputs,
)

_XAI_BASE_URL = "https://api.x.ai/v1"


def _xai_model_supports_reasoning(model: str) -> bool:
    """Retorna se o modelo aceita o parâmetro `reasoning`."""

    return "multi-agent" in (model or "").lower()


def _extract_xai_image(payload: dict, *, timeout_seconds: int) -> tuple[str, str]:
    if payload.get("url"):
        return download_image_as_base64_png(str(payload["url"]), timeout_seconds=timeout_seconds), ""
    data = payload.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            if first.get("b64_json"):
                return normalize_base64_image_to_png(str(first["b64_json"])), ""
            if first.get("url"):
                return (
                    download_image_as_base64_png(
                        str(first["url"]),
                        timeout_seconds=timeout_seconds,
                    ),
                    "",
                )
    return "", "xAI image response did not include an image payload."


def generate_image(
    *,
    api_key: str,
    prepared: PreparedGenerateInputs,
    model: str,
    aspect_ratio: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute xAI image generation."""

    try:
        body = {
            "prompt": prepared.prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
        }
        if extra_body:
            body.update(extra_body)
        response = request(
            "POST",
            f"{_XAI_BASE_URL}/images/generations",
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        blocked = detect_block(payload, operation="generate")
        request_id = extract_request_id(response, payload)
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        cost = usd_ticks_to_decimal((payload.get("usage") or {}).get("cost_in_usd_ticks")) or Decimal("0")
        base64_value, warning = _extract_xai_image(payload, timeout_seconds=timeout_seconds)
        return build_result(
            base64_value=base64_value,
            warnings=warning,
            request_id=request_id,
            cust_usd=cost,
        )
    except Exception as exc:
        return build_result(warnings=provider_error_to_warning(exc))


def edit_image(
    *,
    api_key: str,
    prepared: PreparedEditInputs,
    model: str,
    aspect_ratio: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute xAI image editing with JSON inputs."""

    if prepared.mask is not None:
        return build_result(
            warnings=join_warnings(
                prepared.preprocess_warnings,
                "xAI does not currently document uploaded-mask image editing for this API surface.",
            )
        )
    try:
        body = {
            "prompt": prepared.prompt,
            "model": model,
            "image_url": image_to_data_url(prepared.image),
            "aspect_ratio": aspect_ratio,
        }
        if extra_body:
            body.update(extra_body)
        response = request(
            "POST",
            f"{_XAI_BASE_URL}/images/edits",
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        blocked = detect_block(payload, operation="edit")
        request_id = extract_request_id(response, payload)
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        cost = usd_ticks_to_decimal((payload.get("usage") or {}).get("cost_in_usd_ticks")) or Decimal("0")
        base64_value, warning = _extract_xai_image(payload, timeout_seconds=timeout_seconds)
        return build_result(
            base64_value=base64_value,
            warnings=join_warnings(prepared.preprocess_warnings, warning),
            request_id=request_id,
            cust_usd=cost,
        )
    except Exception as exc:
        return build_result(
            warnings=join_warnings(prepared.preprocess_warnings, provider_error_to_warning(exc))
        )


def remix_image(
    *,
    api_key: str,
    prepared: PreparedRemixInputs,
    model: str,
    aspect_ratio: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute xAI multi-image remixing via ordered image inputs."""

    image_urls: list[str] = []
    if prepared.base_image is not None:
        image_urls.append(image_to_data_url(prepared.base_image))
    image_urls.extend(image_to_data_url(image) for image in prepared.reference_images)
    try:
        body = {
            "prompt": prepared.prompt,
            "model": model,
            "image_urls": image_urls,
            "aspect_ratio": aspect_ratio,
        }
        if extra_body:
            body.update(extra_body)
        response = request(
            "POST",
            f"{_XAI_BASE_URL}/images/edits",
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        blocked = detect_block(payload, operation="remix")
        request_id = extract_request_id(response, payload)
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        cost = usd_ticks_to_decimal((payload.get("usage") or {}).get("cost_in_usd_ticks")) or Decimal("0")
        base64_value, warning = _extract_xai_image(payload, timeout_seconds=timeout_seconds)
        return build_result(
            base64_value=base64_value,
            warnings=warning,
            request_id=request_id,
            cust_usd=cost,
        )
    except Exception as exc:
        return build_result(warnings=provider_error_to_warning(exc))


def analyze_image(
    *,
    api_key: str,
    prepared: PreparedAnalyzeInputs,
    model: str,
    reasoning: str,
    timeout_seconds: int,
    extra_body: dict | None = None,
) -> AnalyzeOperationResult:
    """Executa análise de imagem usando a Responses API da xAI."""

    try:
        payload = {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": image_to_data_url(prepared.image),
                        },
                        {"type": "input_text", "text": prepared.prompt},
                    ],
                }
            ],
        }
        if reasoning and _xai_model_supports_reasoning(model):
            payload["reasoning"] = {"effort": reasoning}
        if extra_body:
            payload.update(extra_body)
        response = request(
            "POST",
            f"{_XAI_BASE_URL}/responses",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        blocked = detect_block(payload, operation="analyze")
        request_id = extract_request_id(response, payload)
        if blocked is not None:
            return build_analyze_result(
                request_id=request_id or blocked.request_id,
                cost_usd=blocked.cust_usd,
                input_text=prepared.prompt,
                output=blocked.warning,
            )
        cost = usd_ticks_to_decimal((payload.get("usage") or {}).get("cost_in_usd_ticks")) or Decimal("0")
        output = extract_text_from_openai_style_response(payload).strip()
        return build_analyze_result(
            request_id=request_id,
            cost_usd=cost,
            input_text=prepared.prompt,
            output=output or "xAI did not return textual output for the analyze request.",
        )
    except Exception as exc:
        return build_analyze_result(
            input_text=prepared.prompt,
            output=provider_error_to_warning(exc),
        )
