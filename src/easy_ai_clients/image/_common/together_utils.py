"""Helpers da Together AI para operações de imagem e visão.

Última atualização: 2026-04-23
"""

from __future__ import annotations

import re
import time
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

_TOGETHER_BASE_URL = "https://api.together.xyz/v1"
_TOGETHER_MODELS_CACHE: dict[str, object] = {"fetched_at": 0.0, "models": []}
_TOGETHER_MODELS_TTL_SECONDS = 3600.0


def _together_response_payload(response):
    """Retorna o payload bruto do Together, aceitando lista ou dict."""

    try:
        return response.json()
    except Exception:
        return {}


def _get_together_models(*, api_key: str, timeout_seconds: int) -> list[dict]:
    """Retorna o catálogo vivo de modelos do Together com cache em memória."""

    now = time.time()
    if now - float(_TOGETHER_MODELS_CACHE["fetched_at"]) < _TOGETHER_MODELS_TTL_SECONDS:
        return list(_TOGETHER_MODELS_CACHE["models"])

    response = request(
        "GET",
        f"{_TOGETHER_BASE_URL}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout_seconds=timeout_seconds,
    )
    payload = _together_response_payload(response)
    models = payload if isinstance(payload, list) else payload.get("data", [])
    if not isinstance(models, list):
        models = []
    _TOGETHER_MODELS_CACHE["fetched_at"] = now
    _TOGETHER_MODELS_CACHE["models"] = models
    return list(models)


def _get_together_model_metadata(
    *,
    api_key: str,
    model: str,
    timeout_seconds: int,
) -> dict | None:
    """Busca os metadados de um modelo do Together no catálogo vivo."""

    return next(
        (
            item
            for item in _get_together_models(api_key=api_key, timeout_seconds=timeout_seconds)
            if isinstance(item, dict) and item.get("id") == model
        ),
        None,
    )


def _megapixels(width: int, height: int) -> Decimal:
    """Converte dimensões em custo por megapixel."""

    return (Decimal(width) * Decimal(height)) / Decimal("1000000")


def _parse_together_image_cost(
    *,
    api_key: str,
    model: str,
    width: int,
    height: int,
    steps: int | None,
    input_images_count: int,
    timeout_seconds: int,
) -> tuple[Decimal | None, str]:
    """Calcula o custo de imagem do Together a partir do catálogo vivo."""

    metadata = _get_together_model_metadata(
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    if metadata is None:
        return None, f"Together AI model `{model}` was not found in the live models catalog."

    pricing = metadata.get("pricing") or {}
    image_pixel = pricing.get("image_pixel")
    if isinstance(image_pixel, dict) and image_pixel.get("price_per_megapixel") is not None:
        base_cost = _megapixels(width, height) * Decimal(str(image_pixel["price_per_megapixel"]))
        min_steps = int(image_pixel.get("min_steps") or 0)
        if min_steps and steps and steps > min_steps:
            base_cost *= Decimal(steps) / Decimal(min_steps)
        return base_cost, ""

    image_pricing = pricing.get("image")
    if not isinstance(image_pricing, dict) or image_pricing.get("example_price") is None:
        return None, (
            f"Together AI did not expose enough live pricing metadata to calculate cost for model `{model}`."
        )

    example_price = Decimal(str(image_pricing["example_price"]))
    description = str(image_pricing.get("example_description") or "").strip().lower()
    if not description:
        return example_price, ""
    if any(
        description == value
        for value in (
            "per image",
            "per text-to-image",
            "per text-to-image image",
        )
    ):
        return example_price, ""

    exact_size_match = re.search(r"(\d+)x(\d+)", description)
    if exact_size_match:
        desc_width = int(exact_size_match.group(1))
        desc_height = int(exact_size_match.group(2))
        if {width, height} == {desc_width, desc_height}:
            extra_cost = Decimal("0")
            surcharge_match = re.search(r"additional \$([0-9.]+)", description)
            if surcharge_match and input_images_count > 0:
                extra_cost = Decimal(str(input_images_count)) * Decimal(surcharge_match.group(1))
            return example_price + extra_cost, ""
        return None, (
            f"Together AI only exposed example pricing for `{model}` at {desc_width}x{desc_height}; "
            f"received {width}x{height}."
        )

    if "1080p" in description or "2k" in description or "4k" in description:
        larger_side = max(width, height)
        if larger_side <= 2048:
            return example_price, ""
        four_k_match = re.search(r"4k resolutions costs \$([0-9.]+)", description)
        if four_k_match and larger_side <= 4096:
            return Decimal(four_k_match.group(1)), ""
        return None, f"Together AI did not expose an exact price bucket for {width}x{height} on `{model}`."

    if "starting price" in description:
        return None, (
            f"Together AI only exposed a starting price for `{model}`, not an exact request price."
        )

    return example_price, ""


def _together_supports_image_url(model):
    """Retorna se o modelo documenta `image_url` no endpoint de imagens."""

    normalized = (model or "").lower()
    return normalized in {
        "black-forest-labs/flux.1-kontext-pro",
        "black-forest-labs/flux.1-kontext-max",
    }


def _together_supports_reference_images(model):
    """Retorna se o modelo documenta `reference_images` no endpoint de imagens."""

    normalized = (model or "").lower()
    if normalized in {
        "black-forest-labs/flux.2-pro",
        "black-forest-labs/flux.2-dev",
        "black-forest-labs/flux.2-flex",
        "google/gemini-3-pro-image",
        "google/flash-image-2.5",
        "google/flash-image-3.1",
    }:
        return True
    return False


def _together_supports_steps(model):
    """Retorna se o modelo costuma aceitar `steps` no endpoint de imagens."""

    normalized = (model or "").lower()
    return normalized in {
        "black-forest-labs/flux.1-schnell",
        "black-forest-labs/flux.1-kontext-pro",
        "black-forest-labs/flux.1-kontext-max",
        "black-forest-labs/flux.1-krea-dev",
        "black-forest-labs/flux.1.1-pro",
        "black-forest-labs/flux.2-dev",
        "black-forest-labs/flux.2-flex",
        "rundiffusion/juggernaut-lightning-flux",
        "rundiffusion/juggernaut-pro-flux",
    }


def _together_error_is_unsupported_steps(payload):
    """Retorna se o payload do Together indica que `steps` não é suportado."""

    message = str(((payload or {}).get("error") or {}).get("message") or "").lower()
    return "steps" in message and "support" in message


def _post_together_image_request(
    *,
    api_key: str,
    body: dict,
    timeout_seconds: int,
) -> tuple[object, dict, int | None]:
    """Executa a request de imagem do Together com fallback para `steps`."""

    used_steps = body.get("steps")
    response = request(
        "POST",
        f"{_TOGETHER_BASE_URL}/images/generations",
        headers={"Authorization": f"Bearer {api_key}"},
        json=body,
        timeout_seconds=timeout_seconds,
    )
    payload = response_json(response)
    if used_steps is not None and _together_error_is_unsupported_steps(payload):
        fallback_body = dict(body)
        fallback_body.pop("steps", None)
        response = request(
            "POST",
            f"{_TOGETHER_BASE_URL}/images/generations",
            headers={"Authorization": f"Bearer {api_key}"},
            json=fallback_body,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        used_steps = None
    return response, payload, used_steps


def generate_image(
    *,
    api_key: str,
    prepared: PreparedGenerateInputs,
    model: str,
    width: int,
    height: int,
    steps: int,
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    seed: int | None = None,
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute Together text-to-image generation."""

    body = {
        "prompt": prepared.prompt,
        "model": model,
        "width": width,
        "height": height,
        "response_format": "base64",
        "output_format": output_format,
    }
    if _together_supports_steps(model):
        body["steps"] = steps
    if seed is not None:
        body["seed"] = seed
    if extra_body:
        body.update(extra_body)
    try:
        response, payload, used_steps = _post_together_image_request(
            api_key=api_key,
            body=body,
            timeout_seconds=timeout_seconds,
        )
        blocked = detect_block(payload, operation="generate")
        request_id = extract_request_id(response, payload)
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        base64_value, warning = extract_image_output(payload, timeout_seconds=timeout_seconds)
        cost, cost_warning = _parse_together_image_cost(
            api_key=api_key,
            model=model,
            width=width,
            height=height,
            steps=used_steps,
            input_images_count=0,
            timeout_seconds=timeout_seconds,
        )
        return build_result(
            base64_value=base64_value,
            warnings=join_warnings(warning, cost_warning),
            request_id=request_id,
            cust_usd=cost or Decimal("0"),
        )
    except Exception as exc:
        return build_result(warnings=provider_error_to_warning(exc))


def edit_image(
    *,
    api_key: str,
    prepared: PreparedEditInputs,
    model: str,
    width: int,
    height: int,
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    seed: int | None = None,
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute Together image editing with a single anchor image."""

    if prepared.mask is not None:
        return build_result(
            warnings=join_warnings(
                prepared.preprocess_warnings,
                "Together AI does not currently document explicit uploaded mask support for this image edit surface.",
            )
        )
    body = {
        "prompt": prepared.prompt,
        "model": model,
        "width": width,
        "height": height,
        "response_format": "base64",
        "output_format": output_format,
    }
    if _together_supports_reference_images(model):
        body["reference_images"] = [image_to_data_url(prepared.image)]
    elif _together_supports_image_url(model):
        body["image_url"] = image_to_data_url(prepared.image)
    else:
        body["reference_images"] = [image_to_data_url(prepared.image)]
    if seed is not None:
        body["seed"] = seed
    if extra_body:
        body.update(extra_body)
    try:
        response, payload, _ = _post_together_image_request(
            api_key=api_key,
            body=body,
            timeout_seconds=timeout_seconds,
        )
        blocked = detect_block(payload, operation="edit")
        request_id = extract_request_id(response, payload)
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        base64_value, warning = extract_image_output(payload, timeout_seconds=timeout_seconds)
        cost, cost_warning = _parse_together_image_cost(
            api_key=api_key,
            model=model,
            width=width,
            height=height,
            steps=None,
            input_images_count=1,
            timeout_seconds=timeout_seconds,
        )
        return build_result(
            base64_value=base64_value,
            warnings=join_warnings(prepared.preprocess_warnings, warning, cost_warning),
            request_id=request_id,
            cust_usd=cost or Decimal("0"),
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
    width: int,
    height: int,
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    seed: int | None = None,
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute Together reference-guided generation via ordered `reference_images`."""

    reference_images = [image_to_data_url(image) for image in prepared.reference_images]
    warnings = ""
    body = {
        "prompt": prepared.prompt,
        "model": model,
        "width": width,
        "height": height,
        "response_format": "base64",
        "output_format": output_format,
    }
    if _together_supports_reference_images(model):
        if prepared.base_image is not None:
            reference_images = [image_to_data_url(prepared.base_image), *reference_images]
            warnings = (
                "Together sent `base_image` as the first `reference_images` item because the provider does not expose a separate public base-image field on this surface."
            )
        body["reference_images"] = reference_images
    elif _together_supports_image_url(model):
        ordered_images = []
        if prepared.base_image is not None:
            ordered_images.append(image_to_data_url(prepared.base_image))
        ordered_images.extend(reference_images)
        if len(ordered_images) != 1:
            return build_result(
                warnings=(
                    f"Together AI model `{model}` only documents a single `image_url` input, so multi-image remix is not supported."
                )
            )
        body["image_url"] = ordered_images[0]
    else:
        if prepared.base_image is not None:
            reference_images = [image_to_data_url(prepared.base_image), *reference_images]
        body["reference_images"] = reference_images
    if seed is not None:
        body["seed"] = seed
    if extra_body:
        body.update(extra_body)
    try:
        response, payload, _ = _post_together_image_request(
            api_key=api_key,
            body=body,
            timeout_seconds=timeout_seconds,
        )
        blocked = detect_block(payload, operation="remix")
        request_id = extract_request_id(response, payload)
        if blocked is not None:
            return build_result(
                warnings=blocked.warning,
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        base64_value, warning = extract_image_output(payload, timeout_seconds=timeout_seconds)
        cost, cost_warning = _parse_together_image_cost(
            api_key=api_key,
            model=model,
            width=width,
            height=height,
            steps=None,
            input_images_count=len(reference_images),
            timeout_seconds=timeout_seconds,
        )
        return build_result(
            base64_value=base64_value,
            warnings=join_warnings(
                warnings,
                warning,
                cost_warning,
            ),
            request_id=request_id,
            cust_usd=cost or Decimal("0"),
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
    """Executa análise de imagem usando a superfície compatível com OpenAI."""

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
            f"{_TOGETHER_BASE_URL}/chat/completions",
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
            cost_usd=Decimal("0"),
            input_text=prepared.prompt,
            output=output or "Together AI did not return textual output for the analyze request.",
        )
    except Exception as exc:
        return build_analyze_result(
            input_text=prepared.prompt,
            output=provider_error_to_warning(exc),
        )
