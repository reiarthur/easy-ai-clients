"""Helpers da OpenAI para operações de imagem e visão.

Última atualização: 2026-04-23
"""

from __future__ import annotations

import re
from collections.abc import Callable
from decimal import Decimal

from .._analyze.post_processing import build_analyze_result
from .cost_utils import (
    extract_openai_image_usage_cost,
    extract_openai_usage_cost,
    get_openai_dalle_image_price,
)
from .errors import ProviderResponseError
from .http_utils import request
from .image_utils import image_to_data_url, image_to_png_bytes, multipart_image
from .provider_utils import (
    detect_block,
    extract_image_output,
    extract_request_id,
    extract_text_from_openai_style_response,
    join_warnings,
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

_OPENAI_BASE_URL = "https://api.openai.com/v1"
_OPENAI_REASONING_PREFERENCE = ("minimal", "none", "low", "medium", "high", "xhigh")


def _is_openai_dalle_model(model: str) -> bool:
    """Retorna se o modelo pertence à família DALL·E."""

    return (model or "").lower().startswith("dall-e-")


def _normalize_openai_image_quality(model: str, quality: str) -> str | None:
    """Normaliza o parâmetro `quality` para o subconjunto aceito pelo modelo."""

    normalized_model = (model or "").lower()
    normalized_quality = (quality or "").strip().lower()
    if normalized_model == "dall-e-2":
        return None
    if normalized_model == "dall-e-3":
        if normalized_quality in {"high", "hd"}:
            return "hd"
        return "standard"
    if normalized_quality in {"low", "medium", "high"}:
        return normalized_quality
    if normalized_quality in {"auto", "standard", ""}:
        return "low"
    return "low"


def _build_openai_image_json_payload(
    *,
    model: str,
    prompt: str,
    size: str,
    quality: str,
    output_format: str,
    extra_body: dict | None = None,
) -> dict:
    """Monta o payload JSON para `/images/generations`."""

    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
    }
    normalized_quality = _normalize_openai_image_quality(model, quality)
    if normalized_quality:
        payload["quality"] = normalized_quality
    if _is_openai_dalle_model(model):
        payload["response_format"] = "b64_json"
    else:
        payload["output_format"] = output_format
    if extra_body:
        payload.update(extra_body)
    return payload


def _build_openai_image_form_payload(
    *,
    model: str,
    prompt: str,
    size: str,
    quality: str,
    output_format: str,
    extra_body: dict | None = None,
) -> dict:
    """Monta o payload multipart para `/images/edits`."""

    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
    }
    normalized_quality = _normalize_openai_image_quality(model, quality)
    if normalized_quality:
        payload["quality"] = normalized_quality
    if _is_openai_dalle_model(model):
        payload["response_format"] = "b64_json"
    else:
        payload["output_format"] = output_format
    if extra_body:
        payload.update(extra_body)
    return payload


def _openai_image_cost_or_warning(
    *,
    model: str,
    payload: dict,
    size: str,
    quality: str,
) -> tuple[Decimal, str]:
    """Extrai o custo exato do request quando a resposta permite cálculo seguro."""

    usage_cost = extract_openai_image_usage_cost(model, payload.get("usage"))
    if usage_cost is not None:
        return usage_cost, ""

    dalle_cost = get_openai_dalle_image_price(model, size, quality)
    if dalle_cost is not None:
        return dalle_cost, ""

    return (
        Decimal("0"),
        "OpenAI did not expose enough pricing metadata to recover the exact image request cost.",
    )


def _openai_model_supports_reasoning(model: str) -> bool:
    """Retorna se o modelo aceita o bloco `reasoning` na Responses API."""

    return bool(_openai_supported_reasoning_efforts(model))


def _openai_supported_reasoning_efforts(model: str) -> tuple[str, ...]:
    """Retorna os esforços de reasoning suportados, em ordem do mais barato."""

    normalized = (model or "").lower()
    if not normalized:
        return ()
    if normalized.startswith("gpt-5-chat-latest"):
        return ()
    if normalized.startswith(("gpt-5.1-chat-latest", "gpt-5.2-chat-latest", "gpt-5.3-chat-latest")):
        return ("medium",)
    if normalized.startswith(("gpt-5.1",)):
        return ("none", "low", "medium", "high")
    if normalized.startswith(("gpt-5.2", "gpt-5.3", "gpt-5.4")):
        return ("none", "low", "medium", "high", "xhigh")
    if normalized.startswith(("gpt-5",)):
        return ("minimal", "low", "medium", "high")
    if normalized.startswith(("o1", "o3", "o4")):
        return ("low", "medium", "high")
    return ()


def _normalize_openai_reasoning(model: str, reasoning: str) -> str | None:
    """Ajusta o esforço solicitado para o menor valor suportado pelo modelo."""

    supported = _openai_supported_reasoning_efforts(model)
    if not supported:
        return None
    requested = (reasoning or "").strip().lower()
    if not requested or requested == "minimal":
        return supported[0]
    if requested in supported:
        return requested
    if requested == "none" and "none" in supported:
        return "none"
    return supported[0]


def _extract_supported_reasoning_from_error(response_text: str) -> tuple[str, ...]:
    """Lê do erro da API os esforços de reasoning explicitamente aceitos."""

    lowered = (response_text or "").lower()
    found = tuple(
        value for value in _OPENAI_REASONING_PREFERENCE if re.search(rf"['`\"]{value}['`\"]", lowered)
    )
    return found


def _build_openai_analyze_payload(
    *,
    prepared: PreparedAnalyzeInputs,
    model: str,
    service_tier: str | None,
    reasoning: str | None,
    extra_body: dict | None = None,
) -> dict:
    """Monta o payload da Responses API já com os fallbacks calculados."""

    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prepared.prompt},
                    {
                        "type": "input_image",
                        "image_url": image_to_data_url(prepared.image),
                    },
                ],
            }
        ],
    }
    if service_tier and _openai_model_supports_service_tier(model):
        payload["service_tier"] = service_tier
    if reasoning:
        payload["reasoning"] = {"effort": reasoning}
    if extra_body:
        payload.update(extra_body)
    return payload


def _openai_model_supports_service_tier(model: str) -> bool:
    """Retorna se o modelo pode receber `service_tier` com segurança."""

    normalized = (model or "").lower()
    return normalized.startswith(("gpt-5",))


def generate_image(
    *,
    api_key: str,
    prepared: PreparedGenerateInputs,
    model: str,
    size: str,
    quality: str,
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute a text-to-image request against OpenAI Images API."""

    try:
        response = request(
            "POST",
            f"{_OPENAI_BASE_URL}/images/generations",
            headers={"Authorization": f"Bearer {api_key}"},
            json=_build_openai_image_json_payload(
                model=model,
                prompt=prepared.prompt,
                size=size,
                quality=quality,
                output_format=output_format,
                extra_body=extra_body,
            ),
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
        base64_value, warning = extract_image_output(payload, timeout_seconds=timeout_seconds)
        cost, cost_warning = _openai_image_cost_or_warning(
            model=model,
            payload=payload,
            size=size,
            quality=quality,
        )
        warnings = join_warnings(warning, cost_warning)
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
    size: str,
    quality: str,
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute an edit request against OpenAI Images API."""

    try:
        files = [
            multipart_image(
                "image",
                image_to_png_bytes(prepared.image),
                filename="image.png",
                mime_type="image/png",
            )
        ]
        if prepared.provider_mask_bytes is not None:
            files.append(
                multipart_image(
                    "mask",
                    prepared.provider_mask_bytes,
                    filename=prepared.provider_mask_filename or "mask.png",
                    mime_type=prepared.provider_mask_mime_type or "image/png",
                )
            )

        response = request(
            "POST",
            f"{_OPENAI_BASE_URL}/images/edits",
            headers={"Authorization": f"Bearer {api_key}"},
            data=_build_openai_image_form_payload(
                model=model,
                prompt=prepared.prompt,
                size=size,
                quality=quality,
                output_format=output_format,
                extra_body=extra_body,
            ),
            files=files,
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
        base64_value, warning = extract_image_output(payload, timeout_seconds=timeout_seconds)
        cost, cost_warning = _openai_image_cost_or_warning(
            model=model,
            payload=payload,
            size=size,
            quality=quality,
        )
        warnings = join_warnings(
            prepared.preprocess_warnings,
            warning,
            cost_warning,
        )
        return build_result(
            base64_value=base64_value,
            warnings=warnings,
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
    size: str,
    quality: str,
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute a multi-image guided generation request via OpenAI image edits."""

    try:
        ordered_images = []
        if prepared.base_image is not None:
            ordered_images.append(prepared.base_image)
        ordered_images.extend(prepared.reference_images)

        files = []
        for index, image in enumerate(ordered_images, start=1):
            files.append(
                multipart_image(
                    "image[]",
                    image_to_png_bytes(image),
                    filename=f"image_{index}.png",
                    mime_type="image/png",
                )
            )

        response = request(
            "POST",
            f"{_OPENAI_BASE_URL}/images/edits",
            headers={"Authorization": f"Bearer {api_key}"},
            data=_build_openai_image_form_payload(
                model=model,
                prompt=prepared.prompt,
                size=size,
                quality=quality,
                output_format=output_format,
                extra_body=extra_body,
            ),
            files=files,
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
        base64_value, warning = extract_image_output(payload, timeout_seconds=timeout_seconds)
        cost, cost_warning = _openai_image_cost_or_warning(
            model=model,
            payload=payload,
            size=size,
            quality=quality,
        )
        warnings = join_warnings(warning, cost_warning)
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
    service_tier: str,
    reasoning: str,
    timeout_seconds: int,
    extra_body: dict | None = None,
) -> AnalyzeOperationResult:
    """Executa análise de imagem usando a OpenAI Responses API."""

    try:
        normalized_reasoning = _normalize_openai_reasoning(model, reasoning)
        payload_variants = []
        payload_variants.append(
            _build_openai_analyze_payload(
                prepared=prepared,
                model=model,
                service_tier=service_tier,
                reasoning=normalized_reasoning,
                extra_body=extra_body,
            )
        )
        payload_variants.append(
            _build_openai_analyze_payload(
                prepared=prepared,
                model=model,
                service_tier="",
                reasoning=normalized_reasoning,
                extra_body=extra_body,
            )
        )
        payload_variants.append(
            _build_openai_analyze_payload(
                prepared=prepared,
                model=model,
                service_tier="",
                reasoning=None,
                extra_body=extra_body,
            )
        )

        deduped_variants = []
        seen_variants = set()
        for variant in payload_variants:
            serialized = repr(variant)
            if serialized in seen_variants:
                continue
            deduped_variants.append(variant)
            seen_variants.add(serialized)

        last_exc = None
        response = None
        for payload in deduped_variants:
            try:
                response = request(
                    "POST",
                    f"{_OPENAI_BASE_URL}/responses",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                    timeout_seconds=timeout_seconds,
                )
                break
            except ProviderResponseError as exc:
                last_exc = exc
                if exc.status_code != 400:
                    raise
                supported_reasoning = _extract_supported_reasoning_from_error(exc.response_text or "")
                if supported_reasoning:
                    fallback_reasoning = next(
                        (
                            effort
                            for effort in _OPENAI_REASONING_PREFERENCE
                            if effort in supported_reasoning
                        ),
                        supported_reasoning[0],
                    )
                    fallback_payload = _build_openai_analyze_payload(
                        prepared=prepared,
                        model=model,
                        service_tier="",
                        reasoning=fallback_reasoning,
                        extra_body=extra_body,
                    )
                    serialized = repr(fallback_payload)
                    if serialized not in seen_variants:
                        deduped_variants.append(fallback_payload)
                        seen_variants.add(serialized)
                continue

        if response is None and last_exc is not None:
            raise last_exc
        if response is None:
            raise ProviderResponseError("OpenAI analyze request did not produce a response.")
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

        cost = extract_openai_usage_cost(model, payload.get("usage")) or Decimal("0")
        output = extract_text_from_openai_style_response(payload).strip()
        return build_analyze_result(
            request_id=request_id,
            cost_usd=cost,
            input_text=prepared.prompt,
            output=output or "OpenAI did not return textual output for the analyze request.",
        )
    except Exception as exc:
        return build_analyze_result(
            input_text=prepared.prompt,
            output=provider_error_to_warning(exc),
        )
