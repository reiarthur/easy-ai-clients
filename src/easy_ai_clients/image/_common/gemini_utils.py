"""Helpers do Google Gemini para operações de imagem e visão.

Última atualização: 2026-04-23
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from .._analyze.post_processing import build_analyze_result
from .cost_utils import extract_gemini_image_usage_cost, extract_gemini_usage_cost
from .http_utils import request
from .image_utils import image_to_base64
from .provider_utils import (
    detect_block,
    extract_request_id,
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

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _gemini_inline_part(asset) -> dict[str, dict[str, str]]:
    return {
        "inlineData": {
            "mimeType": "image/png",
            "data": image_to_base64(asset),
        }
    }


def _gemini_request(
    *,
    api_key: str,
    model: str,
    payload: dict,
    timeout_seconds: int,
) -> tuple[dict, str]:
    response = request(
        "POST",
        f"{_GEMINI_BASE_URL}/{model}:generateContent",
        headers={"x-goog-api-key": api_key},
        json=payload,
        timeout_seconds=timeout_seconds,
    )
    parsed = response_json(response)
    return parsed, extract_request_id(response, parsed)


def _extract_gemini_image(payload: dict) -> tuple[str, str]:
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        return "", "Gemini response did not include candidates."
    for candidate in candidates:
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            inline_data = part.get("inlineData") or part.get("inline_data") or {}
            data = inline_data.get("data")
            if data:
                return normalize_base64_image_to_png(str(data)), ""
    return "", "Gemini response did not include an output image."


def _extract_gemini_text(payload: dict) -> str:
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        return ""
    text_parts: list[str] = []
    for candidate in candidates:
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            if part.get("text"):
                text_parts.append(str(part["text"]))
    return "\n".join(text_parts).strip()


def generate_image(
    *,
    api_key: str,
    prepared: PreparedGenerateInputs,
    model: str,
    aspect_ratio: str,
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    generation_config: dict | None = None,
) -> ImageOperationResult:
    """Execute Gemini image generation."""

    del output_format  # Gemini returns inline image bytes, then we normalize to PNG.
    try:
        config = {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio},
        }
        if generation_config:
            config.update(generation_config)
            image_config = dict(config.get("imageConfig") or {})
            image_config.setdefault("aspectRatio", aspect_ratio)
            config["imageConfig"] = image_config
        payload, request_id = _gemini_request(
            api_key=api_key,
            model=model,
            payload={
                "contents": [{"role": "user", "parts": [{"text": prepared.prompt}]}],
                "generationConfig": config,
            },
            timeout_seconds=timeout_seconds,
        )
        blocked = detect_block(payload, operation="generate")
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        image_base64, warning = _extract_gemini_image(payload)
        cost = extract_gemini_image_usage_cost(model, payload.get("usageMetadata")) or Decimal("0")
        cost_warning = ""
        if cost == 0:
            cost_warning = (
                "Gemini did not expose enough public pricing metadata to recover the exact image request cost."
            )
        return build_result(
            base64_value=image_base64,
            warnings=join_warnings(warning, cost_warning),
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
    generation_config: dict | None = None,
) -> ImageOperationResult:
    """Execute Gemini conversational image editing without explicit mask support."""

    del output_format
    if prepared.mask is not None:
        return build_result(
            warnings=join_warnings(
                prepared.preprocess_warnings,
                "Gemini image editing with an explicit uploaded mask is not documented as a safe official capability for this layer.",
            )
        )
    try:
        config = {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio},
        }
        if generation_config:
            config.update(generation_config)
            image_config = dict(config.get("imageConfig") or {})
            image_config.setdefault("aspectRatio", aspect_ratio)
            config["imageConfig"] = image_config
        payload, request_id = _gemini_request(
            api_key=api_key,
            model=model,
            payload={
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prepared.prompt},
                            _gemini_inline_part(prepared.image),
                        ],
                    }
                ],
                "generationConfig": config,
            },
            timeout_seconds=timeout_seconds,
        )
        blocked = detect_block(payload, operation="edit")
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        image_base64, warning = _extract_gemini_image(payload)
        cost = extract_gemini_image_usage_cost(model, payload.get("usageMetadata")) or Decimal("0")
        cost_warning = ""
        if cost == 0:
            cost_warning = (
                "Gemini did not expose enough public pricing metadata to recover the exact image request cost."
            )
        return build_result(
            base64_value=image_base64,
            warnings=join_warnings(prepared.preprocess_warnings, warning, cost_warning),
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
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    generation_config: dict | None = None,
) -> ImageOperationResult:
    """Execute Gemini multi-image reference generation."""

    del output_format
    try:
        parts = [{"text": prepared.prompt}]
        if prepared.base_image is not None:
            parts.append(_gemini_inline_part(prepared.base_image))
        parts.extend(_gemini_inline_part(image) for image in prepared.reference_images)
        config = {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio},
        }
        if generation_config:
            config.update(generation_config)
            image_config = dict(config.get("imageConfig") or {})
            image_config.setdefault("aspectRatio", aspect_ratio)
            config["imageConfig"] = image_config
        payload, request_id = _gemini_request(
            api_key=api_key,
            model=model,
            payload={
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": config,
            },
            timeout_seconds=timeout_seconds,
        )
        blocked = detect_block(payload, operation="remix")
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        image_base64, warning = _extract_gemini_image(payload)
        cost = extract_gemini_image_usage_cost(model, payload.get("usageMetadata")) or Decimal("0")
        cost_warning = ""
        if cost == 0:
            cost_warning = (
                "Gemini did not expose enough public pricing metadata to recover the exact image request cost."
            )
        return build_result(
            base64_value=image_base64,
            warnings=join_warnings(warning, cost_warning),
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
    generation_config: dict | None = None,
) -> AnalyzeOperationResult:
    """Executa análise de imagem usando o Gemini."""

    try:
        payload, request_id = _gemini_request(
            api_key=api_key,
            model=model,
            payload={
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prepared.prompt},
                            _gemini_inline_part(prepared.image),
                        ],
                    }
                ],
                **({"generationConfig": generation_config} if generation_config else {}),
            },
            timeout_seconds=timeout_seconds,
        )
        blocked = detect_block(payload, operation="analyze")
        if blocked is not None:
            return build_analyze_result(
                request_id=request_id or blocked.request_id,
                cost_usd=blocked.cust_usd,
                input_text=prepared.prompt,
                output=blocked.warning,
            )
        output = _extract_gemini_text(payload).strip()
        return build_analyze_result(
            request_id=request_id,
            cost_usd=extract_gemini_usage_cost(model, payload.get("usageMetadata"))
            or Decimal("0"),
            input_text=prepared.prompt,
            output=output or "Gemini did not return textual output for the analyze request.",
        )
    except Exception as exc:
        return build_analyze_result(
            input_text=prepared.prompt,
            output=provider_error_to_warning(exc),
        )
