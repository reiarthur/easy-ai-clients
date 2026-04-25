"""Helpers da Fireworks AI para operações de imagem e visão.

Última atualização: 2026-04-23
"""

from __future__ import annotations

import time
from collections.abc import Callable
from decimal import Decimal

from .._analyze.post_processing import build_analyze_result
from .cost_utils import extract_fireworks_usage_cost
from .http_utils import request
from .image_utils import image_to_data_url
from .provider_utils import (
    detect_block,
    download_image_as_base64_png,
    extract_request_id,
    extract_text_from_openai_style_response,
    image_bytes_to_base64_png,
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

_FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
_FIREWORKS_GENERATE_STEP_PRICES = {
    "flux-1-dev-fp8": Decimal("0.0005"),
    "flux-1-schnell-fp8": Decimal("0.00035"),
}
_FIREWORKS_EDIT_IMAGE_PRICES = {
    "flux-kontext-pro": Decimal("0.04"),
    "flux-kontext-max": Decimal("0.08"),
}


def _normalize_fireworks_model_slug(model: str) -> str:
    """Converte ids completos para o slug usado no pricing local."""

    return (model or "").split("/")[-1]


def _poll_fireworks_result(
    *,
    api_key: str,
    model: str,
    request_id: str,
    timeout_seconds: int,
) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: dict = {}
    while time.time() < deadline:
        response = request(
            "POST",
            f"{_FIREWORKS_BASE_URL}/workflows/accounts/fireworks/models/{model}/get_result",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"id": request_id},
            timeout_seconds=timeout_seconds,
        )
        last_payload = response_json(response)
        status = str(last_payload.get("status") or "").lower()
        if status not in {"pending", "processing", "queued", "running", "task not found"}:
            return last_payload
        time.sleep(2.0)
    return last_payload


def _extract_fireworks_result_image(payload: dict, *, timeout_seconds: int) -> tuple[str, str]:
    result = payload.get("result")
    if isinstance(result, str):
        return normalize_base64_image_to_png(result), ""
    if isinstance(result, dict):
        if result.get("sample"):
            return download_image_as_base64_png(str(result["sample"]), timeout_seconds=timeout_seconds), ""
        if result.get("image"):
            return normalize_base64_image_to_png(str(result["image"])), ""
    return "", f"Fireworks result did not include an image payload. Final status: {payload.get('status') or 'unknown'}."


def _fireworks_generate_cost(model: str, steps: int) -> Decimal:
    """Retorna o custo exato de geração por steps para os modelos suportados."""

    return _FIREWORKS_GENERATE_STEP_PRICES.get(
        _normalize_fireworks_model_slug(model),
        Decimal("0"),
    ) * Decimal(str(steps))


def _fireworks_edit_cost(model: str) -> Decimal:
    """Retorna o custo exato por imagem dos modelos Kontext suportados."""

    return _FIREWORKS_EDIT_IMAGE_PRICES.get(
        _normalize_fireworks_model_slug(model),
        Decimal("0"),
    )


def generate_image(
    *,
    api_key: str,
    prepared: PreparedGenerateInputs,
    model: str,
    aspect_ratio: str,
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    seed: int | None = None,
    steps: int = 4,
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute Fireworks FLUX.1 schnell text-to-image generation."""

    body = {
        "prompt": prepared.prompt,
        "aspect_ratio": aspect_ratio,
    }
    if seed is not None:
        body["seed"] = seed
    if steps is not None:
        body["steps"] = steps
    if extra_body:
        body.update(extra_body)
    try:
        response = request(
            "POST",
            f"{_FIREWORKS_BASE_URL}/workflows/accounts/fireworks/models/{model}/text_to_image",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "image/png",
            },
            json=body,
            timeout_seconds=timeout_seconds,
        )
        content_type = (response.headers.get("content-type") or "").lower()
        if content_type.startswith("image/"):
            return build_result(
                base64_value=image_bytes_to_base64_png(response.content),
                warnings="",
                request_id=extract_request_id(response),
                cust_usd=_fireworks_generate_cost(model, steps),
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
        images = payload.get("base64") or []
        base64_value = ""
        if isinstance(images, list) and images:
            image_value = str(images[0])
            base64_value = normalize_base64_image_to_png(image_value)
        warning = "" if base64_value else "Fireworks generate response did not include base64 output."
        cost = _fireworks_generate_cost(model, steps)
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
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    seed: int | None = None,
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute Fireworks Kontext edit."""

    if prepared.mask is not None:
        return build_result(
            warnings=join_warnings(
                prepared.preprocess_warnings,
                "Fireworks Kontext does not currently document uploaded-mask editing for this layer.",
            )
        )
    body = {
        "prompt": prepared.prompt,
        "input_image": image_to_data_url(prepared.image),
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
    }
    if seed is not None:
        body["seed"] = seed
    if extra_body:
        body.update(extra_body)
    try:
        response = request(
            "POST",
            f"{_FIREWORKS_BASE_URL}/workflows/accounts/fireworks/models/{model}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        request_id = str(payload.get("request_id") or extract_request_id(response, payload))
        poll_payload = _poll_fireworks_result(
            api_key=api_key,
            model=model,
            request_id=request_id,
            timeout_seconds=timeout_seconds,
        )
        blocked = detect_block(poll_payload, operation="edit")
        if blocked is not None:
            return build_result(
                warnings=join_warnings(prepared.preprocess_warnings, blocked.warning),
                request_id=request_id or blocked.request_id,
                cust_usd=_fireworks_edit_cost(model),
            )
        base64_value, warning = _extract_fireworks_result_image(
            poll_payload,
            timeout_seconds=timeout_seconds,
        )
        if base64_value:
            return build_result(
                base64_value=base64_value,
                warnings=prepared.preprocess_warnings,
                request_id=request_id,
                cust_usd=_fireworks_edit_cost(model),
            )
        return build_result(
            warnings=join_warnings(prepared.preprocess_warnings, warning),
            request_id=request_id,
            cust_usd=_fireworks_edit_cost(model),
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
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    seed: int | None = None,
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute the supported Fireworks reference-guided generation subset."""

    if prepared.base_image is not None:
        return build_result(
            warnings=(
                "Fireworks remix with separate base_image plus reference_images is not clearly documented for the current public API surface."
            )
        )
    if len(prepared.reference_images) != 1:
        return build_result(
            warnings=(
                "Fireworks Kontext currently exposes a single input_image field in this implementation, so multi-reference remix is not supported."
            )
        )
    body = {
        "prompt": prepared.prompt,
        "input_image": image_to_data_url(prepared.reference_images[0]),
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
    }
    if seed is not None:
        body["seed"] = seed
    if extra_body:
        body.update(extra_body)
    try:
        response = request(
            "POST",
            f"{_FIREWORKS_BASE_URL}/workflows/accounts/fireworks/models/{model}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        request_id = str(payload.get("request_id") or extract_request_id(response, payload))
        poll_payload = _poll_fireworks_result(
            api_key=api_key,
            model=model,
            request_id=request_id,
            timeout_seconds=timeout_seconds,
        )
        blocked = detect_block(poll_payload, operation="remix")
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=_fireworks_edit_cost(model),
            )
        base64_value, warning = _extract_fireworks_result_image(
            poll_payload,
            timeout_seconds=timeout_seconds,
        )
        if base64_value:
            return build_result(
                base64_value=base64_value,
                warnings="",
                request_id=request_id,
                cust_usd=_fireworks_edit_cost(model),
            )
        return build_result(
            warnings=warning,
            request_id=request_id,
            cust_usd=_fireworks_edit_cost(model),
        )
    except Exception as exc:
        return build_result(warnings=provider_error_to_warning(exc))


def analyze_image(
    *,
    api_key: str,
    prepared: PreparedAnalyzeInputs,
    model: str,
    timeout_seconds: int,
    extra_body: dict | None = None,
) -> AnalyzeOperationResult:
    """Executa análise de imagem via chat completions da Fireworks."""

    try:
        body = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prepared.prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_to_data_url(prepared.image)},
                        },
                    ],
                }
            ],
        }
        if extra_body:
            body.update(extra_body)
        response = request(
            "POST",
            f"{_FIREWORKS_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
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
        output = extract_text_from_openai_style_response(payload).strip()
        return build_analyze_result(
            request_id=request_id,
            cost_usd=extract_fireworks_usage_cost(model, payload.get("usage")) or Decimal("0"),
            input_text=prepared.prompt,
            output=output or "Fireworks did not return textual output for the analyze request.",
        )
    except Exception as exc:
        return build_analyze_result(
            input_text=prepared.prompt,
            output=provider_error_to_warning(exc),
        )
