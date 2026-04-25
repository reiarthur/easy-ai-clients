"""Helpers do OpenRouter para operações de imagem e visão.

Última atualização: 2026-04-23
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from .._analyze.post_processing import build_analyze_result
from .http_utils import request
from .image_utils import image_to_data_url
from .provider_utils import (
    detect_block,
    extract_image_output,
    extract_request_id,
    extract_text_from_openai_style_response,
    get_openrouter_models,
    join_warnings,
    provider_error_to_warning,
    response_json,
    update_openrouter_cost_from_request_id,
    update_openrouter_image_cost_from_request_id,
    validate_openrouter_model,
)
from .types import (
    AnalyzeOperationResult,
    ImageOperationResult,
    PreparedAnalyzeInputs,
    PreparedEditInputs,
    PreparedGenerateInputs,
    PreparedRemixInputs,
)

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _image_modalities(model: str, *, timeout_seconds: int) -> list[str]:
    metadata = next(
        (item for item in get_openrouter_models(timeout_seconds=timeout_seconds) if item.get("id") == model),
        None,
    )
    outputs = set((metadata or {}).get("architecture", {}).get("output_modalities") or [])
    return ["image", "text"] if {"image", "text"} <= outputs else ["image"]


def _usage_cost(payload: dict) -> Decimal | None:
    usage = payload.get("usage") or {}
    if isinstance(usage, dict) and usage.get("cost") is not None:
        return Decimal(str(usage["cost"]))
    return None


def _resolve_openrouter_image_cost(
    *,
    api_key: str,
    request_id: str,
    base64_value: str,
    warnings: str,
    immediate_cost: Decimal,
    timeout_seconds: int,
) -> tuple[Decimal, str]:
    """Tenta resolver o custo final imediatamente a partir do `request_id`."""

    if immediate_cost != 0 or not request_id:
        return immediate_cost, warnings
    try:
        updated = update_openrouter_image_cost_from_request_id(
            {
                "cust_usd": float(immediate_cost),
                "base64": base64_value,
                "warnings": warnings,
                "request_id": request_id,
            },
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
    except Exception:
        return (
            immediate_cost,
            join_warnings(
                warnings,
                "OpenRouter cost lookup was not immediately available; call updateCost(result_dict) later with the same request_id.",
            ),
        )
    updated_cost = Decimal(str(updated.get("cust_usd") or "0"))
    if updated_cost != 0:
        return updated_cost, warnings
    return (
        immediate_cost,
        join_warnings(
            warnings,
            "OpenRouter cost may require updateCost(result_dict) if the final total is not yet available immediately.",
        ),
    )


def generate_image(
    *,
    api_key: str,
    prepared: PreparedGenerateInputs,
    model: str,
    aspect_ratio: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    extra_body: dict | None = None,
    image_config: dict | None = None,
) -> ImageOperationResult:
    """Execute image generation via OpenRouter chat completions."""

    validation_warning = validate_openrouter_model(
        model=model,
        operation="generate",
        timeout_seconds=timeout_seconds,
    )
    if validation_warning:
        return build_result(warnings=validation_warning)
    try:
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prepared.prompt}],
            "modalities": _image_modalities(model, timeout_seconds=timeout_seconds),
            "image_config": {"aspect_ratio": aspect_ratio, **(image_config or {})},
        }
        if extra_body:
            body.update(extra_body)
        response = request(
            "POST",
            f"{_OPENROUTER_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        blocked = detect_block(payload, operation="generate")
        request_id = str(payload.get("id") or extract_request_id(response, payload))
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        base64_value, warning = extract_image_output(payload, timeout_seconds=timeout_seconds)
        cost = _usage_cost(payload) or Decimal("0")
        warnings = warning
        cost, warnings = _resolve_openrouter_image_cost(
            api_key=api_key,
            request_id=request_id,
            base64_value=base64_value,
            warnings=warnings,
            immediate_cost=cost,
            timeout_seconds=timeout_seconds,
        )
        return build_result(
            base64_value=base64_value,
            warnings=warnings,
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
    image_config: dict | None = None,
) -> ImageOperationResult:
    """Execute OpenRouter image editing."""

    if prepared.mask is not None:
        return build_result(
            warnings=join_warnings(
                prepared.preprocess_warnings,
                "OpenRouter image editing with explicit uploaded masks is not standardized safely across routed providers.",
            )
        )
    validation_warning = validate_openrouter_model(
        model=model,
        operation="edit",
        timeout_seconds=timeout_seconds,
    )
    if validation_warning:
        return build_result(warnings=validation_warning)
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
            "modalities": _image_modalities(model, timeout_seconds=timeout_seconds),
            "image_config": {"aspect_ratio": aspect_ratio, **(image_config or {})},
        }
        if extra_body:
            body.update(extra_body)
        response = request(
            "POST",
            f"{_OPENROUTER_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        blocked = detect_block(payload, operation="edit")
        request_id = str(payload.get("id") or extract_request_id(response, payload))
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        base64_value, warning = extract_image_output(payload, timeout_seconds=timeout_seconds)
        cost = _usage_cost(payload) or Decimal("0")
        warnings = warning
        cost, warnings = _resolve_openrouter_image_cost(
            api_key=api_key,
            request_id=request_id,
            base64_value=base64_value,
            warnings=warnings,
            immediate_cost=cost,
            timeout_seconds=timeout_seconds,
        )
        return build_result(
            base64_value=base64_value,
            warnings=join_warnings(prepared.preprocess_warnings, warnings),
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
    image_config: dict | None = None,
) -> ImageOperationResult:
    """Execute OpenRouter reference-guided image generation."""

    validation_warning = validate_openrouter_model(
        model=model,
        operation="remix",
        timeout_seconds=timeout_seconds,
    )
    if validation_warning:
        return build_result(warnings=validation_warning)
    parts = [{"type": "text", "text": prepared.prompt}]
    if prepared.base_image is not None:
        parts.append({"type": "image_url", "image_url": {"url": image_to_data_url(prepared.base_image)}})
    for image in prepared.reference_images:
        parts.append({"type": "image_url", "image_url": {"url": image_to_data_url(image)}})
    try:
        body = {
            "model": model,
            "messages": [{"role": "user", "content": parts}],
            "modalities": _image_modalities(model, timeout_seconds=timeout_seconds),
            "image_config": {"aspect_ratio": aspect_ratio, **(image_config or {})},
        }
        if extra_body:
            body.update(extra_body)
        response = request(
            "POST",
            f"{_OPENROUTER_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        blocked = detect_block(payload, operation="remix")
        request_id = str(payload.get("id") or extract_request_id(response, payload))
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        base64_value, warning = extract_image_output(payload, timeout_seconds=timeout_seconds)
        cost = _usage_cost(payload) or Decimal("0")
        warnings = warning
        cost, warnings = _resolve_openrouter_image_cost(
            api_key=api_key,
            request_id=request_id,
            base64_value=base64_value,
            warnings=warnings,
            immediate_cost=cost,
            timeout_seconds=timeout_seconds,
        )
        return build_result(
            base64_value=base64_value,
            warnings=warnings,
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
    timeout_seconds: int,
    extra_body: dict | None = None,
) -> AnalyzeOperationResult:
    """Executa análise de imagem via OpenRouter."""

    validation_warning = validate_openrouter_model(
        model=model,
        operation="analyze",
        timeout_seconds=timeout_seconds,
    )
    if validation_warning:
        return build_analyze_result(
            input_text=prepared.prompt,
            output=validation_warning,
        )
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
            f"{_OPENROUTER_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        blocked = detect_block(payload, operation="analyze")
        request_id = str(payload.get("id") or extract_request_id(response, payload))
        if blocked is not None:
            return build_analyze_result(
                request_id=request_id or blocked.request_id,
                cost_usd=blocked.cust_usd,
                input_text=prepared.prompt,
                output=blocked.warning,
            )
        cost = _usage_cost(payload) or Decimal("0")
        output = extract_text_from_openai_style_response(payload).strip()
        if cost == 0 and request_id:
            try:
                updated = update_openrouter_cost_from_request_id(
                    build_analyze_result(
                        request_id=request_id,
                        cost_usd=cost,
                        input_text=prepared.prompt,
                        output=output,
                    ),
                    api_key=api_key,
                    timeout_seconds=timeout_seconds,
                )
                cost = Decimal(str(updated.get("cost_usd") or "0"))
            except Exception:
                cost = Decimal("0")
        return build_analyze_result(
            request_id=request_id,
            cost_usd=cost,
            input_text=prepared.prompt,
            output=output or "OpenRouter did not return textual output for the analyze request.",
        )
    except Exception as exc:
        return build_analyze_result(
            input_text=prepared.prompt,
            output=provider_error_to_warning(exc),
        )


def update_cost(result_dict: dict, *, api_key: str, timeout_seconds: int = 60) -> dict:
    """Resolve o custo final do OpenRouter preservando o contrato público."""

    if {"request_id", "cost_usd", "input_text", "output"} <= set(result_dict):
        return update_openrouter_cost_from_request_id(
            result_dict,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
    return update_openrouter_image_cost_from_request_id(
        result_dict,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
    )
