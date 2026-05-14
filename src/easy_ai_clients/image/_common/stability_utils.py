"""Helpers da Stability AI para operações públicas de imagem.

Última atualização: 2026-04-23
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from .http_utils import request
from .image_utils import image_to_png_bytes, multipart_image
from .provider_utils import (
    extract_request_id,
    image_bytes_to_base64_png,
    join_warnings,
    normalize_base64_image_to_png,
    provider_error_to_warning,
)
from .types import (
    ImageOperationResult,
    PreparedEditInputs,
    PreparedGenerateInputs,
    PreparedRemixInputs,
)

_STABILITY_BASE_URL = "https://api.stability.ai/v2beta/stable-image"
_STABILITY_GENERATE_MODELS = {
    "stable-image-core": {
        "path": "generate/core",
        "cost": Decimal("0.03"),
    },
    "stable-image-ultra": {
        "path": "generate/ultra",
        "cost": Decimal("0.065"),
    },
}
_STABILITY_EDIT_MODELS = {
    "stable-image-inpaint": {
        "path": "edit/inpaint",
        "cost": Decimal("0.05"),
    }
}
_STABILITY_REMIX_MODELS = {
    "stable-image-style": {
        "path": "control/style",
        "cost": Decimal("0.05"),
    },
    "stable-image-structure": {
        "path": "control/structure",
        "cost": Decimal("0.05"),
    },
}


def _handle_stability_image_response(response, *, operation):
    """Normaliza a resposta de imagem da Stability AI."""

    finish_reason = (
        response.headers.get("finish-reason")
        or response.headers.get("Finish-Reason")
        or ""
    ).lower()
    if any(token in finish_reason for token in ("filtered", "blocked", "moderated")):
        return "", f"Stability {operation} was blocked by provider policy: {finish_reason}."
    content_type = (response.headers.get("content-type") or "").lower()
    if content_type.startswith("image/"):
        return image_bytes_to_base64_png(response.content), ""
    payload = response.json() if response.text else {}
    if isinstance(payload, dict) and payload.get("image"):
        return normalize_base64_image_to_png(str(payload["image"])), ""
    if isinstance(payload, dict) and payload.get("errors"):
        return "", "; ".join(str(item) for item in payload["errors"])
    return "", f"Stability {operation} did not return an image payload."


def _stability_model_config(model_map, model, operation):
    """Resolve documented endpoint/cost metadata without blocking unknown models."""

    config = model_map.get(model)
    if config is None:
        return {"path": str(model).strip(), "cost": Decimal("0")}, ""
    return config, ""


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
    negative_prompt: str | None = None,
    extra_form: dict | None = None,
) -> ImageOperationResult:
    """Executa geração de imagem na Stability AI."""

    config, warning = _stability_model_config(_STABILITY_GENERATE_MODELS, model, "generate")
    if config is None:
        return build_result(warnings=warning)

    multipart_form = [
        ("prompt", (None, prepared.prompt)),
        ("aspect_ratio", (None, aspect_ratio)),
        ("output_format", (None, output_format)),
    ]
    if seed is not None:
        multipart_form.append(("seed", (None, str(seed))))
    if negative_prompt:
        multipart_form.append(("negative_prompt", (None, negative_prompt)))
    if extra_form:
        for key, value in extra_form.items():
            if value is not None:
                multipart_form.append((key, (None, str(value))))
    try:
        response = request(
            "POST",
            f"{_STABILITY_BASE_URL}/{config['path']}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "image/*",
            },
            files=multipart_form,
            timeout_seconds=timeout_seconds,
        )
        base64_value, response_warning = _handle_stability_image_response(
            response,
            operation="generate",
        )
        return build_result(
            base64_value=base64_value,
            warnings=response_warning,
            request_id=extract_request_id(response),
            cust_usd=config["cost"],
        )
    except Exception as exc:
        return build_result(warnings=provider_error_to_warning(exc))


def edit_image(
    *,
    api_key: str,
    prepared: PreparedEditInputs,
    model: str,
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    seed: int | None = None,
    extra_form: dict | None = None,
) -> ImageOperationResult:
    """Executa edição de imagem via inpaint na Stability AI."""

    config, warning = _stability_model_config(_STABILITY_EDIT_MODELS, model, "edit")
    if config is None:
        return build_result(warnings=join_warnings(prepared.preprocess_warnings, warning))

    files = [
        multipart_image(
            "image",
            image_to_png_bytes(prepared.image),
            filename="image.png",
            mime_type="image/png",
        ),
        multipart_image(
            "mask",
            prepared.provider_mask_bytes or b"",
            filename=prepared.provider_mask_filename or "mask.png",
            mime_type=prepared.provider_mask_mime_type or "image/png",
        ),
    ]
    form = {
        "prompt": prepared.prompt,
        "output_format": output_format,
    }
    if seed is not None:
        form["seed"] = str(seed)
    if extra_form:
        form.update({key: str(value) for key, value in extra_form.items() if value is not None})
    try:
        response = request(
            "POST",
            f"{_STABILITY_BASE_URL}/{config['path']}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "image/*",
            },
            data=form,
            files=files,
            timeout_seconds=timeout_seconds,
        )
        base64_value, response_warning = _handle_stability_image_response(response, operation="edit")
        return build_result(
            base64_value=base64_value,
            warnings=join_warnings(prepared.preprocess_warnings, response_warning),
            request_id=extract_request_id(response),
            cust_usd=config["cost"],
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
    extra_form: dict | None = None,
) -> ImageOperationResult:
    """Executa geração guiada por referência na Stability AI."""

    config, warning = _stability_model_config(_STABILITY_REMIX_MODELS, model, "remix")
    if config is None:
        return build_result(warnings=warning)

    if prepared.base_image is not None:
        return build_result(
            warnings=(
                "Stability remix with separate base_image plus reference_images is not clearly documented for the current public API surface."
            )
        )

    warnings = ""
    reference = prepared.reference_images[0]
    if len(prepared.reference_images) > 1:
        warnings = (
            "Stability image control currently uses a single reference image in this implementation, so only the first reference was used."
        )
    files = [
        multipart_image(
            "image",
            image_to_png_bytes(reference),
            filename="style_reference.png",
            mime_type="image/png",
        )
    ]
    form = {
        "prompt": prepared.prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
    }
    if seed is not None:
        form["seed"] = str(seed)
    if extra_form:
        form.update({key: str(value) for key, value in extra_form.items() if value is not None})
    try:
        response = request(
            "POST",
            f"{_STABILITY_BASE_URL}/{config['path']}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "image/*",
            },
            data=form,
            files=files,
            timeout_seconds=timeout_seconds,
        )
        base64_value, response_warning = _handle_stability_image_response(response, operation="remix")
        return build_result(
            base64_value=base64_value,
            warnings=join_warnings(warnings, response_warning),
            request_id=extract_request_id(response),
            cust_usd=config["cost"],
        )
    except Exception as exc:
        return build_result(warnings=provider_error_to_warning(exc))
