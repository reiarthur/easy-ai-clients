"""Helpers for Black Forest Labs image operations."""

from __future__ import annotations

import base64
import time
from collections.abc import Callable
from decimal import Decimal

from .http_utils import request
from .image_utils import image_to_data_url
from .provider_utils import (
    detect_block,
    download_image_as_base64_png,
    extract_request_id,
    join_warnings,
    provider_error_to_warning,
    response_json,
)
from .types import (
    ImageOperationResult,
    PreparedEditInputs,
    PreparedGenerateInputs,
    PreparedRemixInputs,
)

_BFL_BASE_URL = "https://api.bfl.ai/v1"


def _poll_bfl(*, polling_url: str, api_key: str, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: dict = {}
    while time.time() < deadline:
        response = request(
            "GET",
            polling_url,
            headers={"x-key": api_key, "accept": "application/json"},
            timeout_seconds=timeout_seconds,
        )
        last_payload = response_json(response)
        status = str(last_payload.get("status") or "").lower()
        if status not in {"pending", "processing", "queued", "running"}:
            return last_payload
        time.sleep(2.0)
    return last_payload


def _extract_bfl_sample_url(payload: dict) -> str:
    result = payload.get("result") or {}
    if isinstance(result, dict):
        if result.get("sample"):
            return str(result["sample"])
        if result.get("image"):
            return str(result["image"])
    if payload.get("preview"):
        return str(payload["preview"])
    return ""


def generate_image(
    *,
    api_key: str,
    prepared: PreparedGenerateInputs,
    model: str,
    width: int,
    height: int,
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    seed: int | None = None,
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute text-to-image generation on Black Forest Labs."""

    body = {
        "prompt": prepared.prompt,
        "width": width,
        "height": height,
        "output_format": output_format,
    }
    if seed is not None:
        body["seed"] = seed
    if extra_body:
        body.update(extra_body)
    try:
        response = request(
            "POST",
            f"{_BFL_BASE_URL}/{model}",
            headers={"x-key": api_key, "Content-Type": "application/json"},
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
        poll_url = payload.get("polling_url")
        if not poll_url:
            return build_result(
                warnings="BFL did not return a polling_url for generation.",
                request_id=request_id,
            )
        final_payload = _poll_bfl(
            polling_url=str(poll_url),
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        final_block = detect_block(final_payload, operation="generate")
        if final_block is not None:
            return build_result(
                warnings=final_block.warning,
                request_id=request_id or final_block.request_id,
                cust_usd=Decimal(str(payload.get("cost") or "0")),
            )
        sample_url = _extract_bfl_sample_url(final_payload)
        if not sample_url:
            return build_result(
                warnings=(
                    f"BFL polling did not reach a downloadable image. Final status: {final_payload.get('status') or 'unknown'}."
                ),
                request_id=request_id,
                cust_usd=Decimal(str(payload.get("cost") or "0")),
            )
        return build_result(
            base64_value=download_image_as_base64_png(
                str(sample_url),
                timeout_seconds=timeout_seconds,
            ),
            warnings="",
            request_id=request_id,
            cust_usd=Decimal(str(payload.get("cost") or "0")),
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
    steps: int = 28,
    guidance: float = 2.5,
    seed: int | None = None,
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute Black Forest Labs image editing."""

    try:
        if prepared.mask is not None and model != "flux-pro-1.0-fill":
            return build_result(
                warnings=join_warnings(
                    prepared.preprocess_warnings,
                    "BFL uploaded-mask editing is only implemented for model `flux-pro-1.0-fill`.",
                )
            )

        if prepared.mask is not None:
            body = {
                "prompt": prepared.prompt,
                "image": base64.b64encode(prepared.image.raw_bytes).decode("ascii"),
                "mask": base64.b64encode(prepared.provider_mask_bytes or b"").decode("ascii"),
                "steps": steps,
                "guidance": guidance,
                "output_format": output_format,
            }
            if seed is not None:
                body["seed"] = seed
            if extra_body:
                body.update(extra_body)
            response = request(
                "POST",
                f"{_BFL_BASE_URL}/flux-pro-1.0-fill",
                headers={"x-key": api_key, "Content-Type": "application/json"},
                json=body,
                timeout_seconds=timeout_seconds,
            )
        else:
            body = {
                "prompt": prepared.prompt,
                "input_image": image_to_data_url(prepared.image),
                "output_format": output_format,
            }
            if seed is not None:
                body["seed"] = seed
            if extra_body:
                body.update(extra_body)
            response = request(
                "POST",
                f"{_BFL_BASE_URL}/{model}",
                headers={"x-key": api_key, "Content-Type": "application/json"},
                json=body,
                timeout_seconds=timeout_seconds,
            )

        payload = response_json(response)
        blocked = detect_block(payload, operation="edit")
        request_id = extract_request_id(response, payload)
        if blocked is not None:
            return build_result(
                warnings=join_warnings(prepared.preprocess_warnings, blocked.warning),
                request_id=request_id or blocked.request_id,
                cust_usd=blocked.cust_usd,
            )
        poll_url = payload.get("polling_url")
        if not poll_url:
            return build_result(
                warnings=join_warnings(
                    prepared.preprocess_warnings,
                    "BFL did not return a polling_url for edit.",
                ),
                request_id=request_id,
            )
        final_payload = _poll_bfl(
            polling_url=str(poll_url),
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        final_block = detect_block(final_payload, operation="edit")
        if final_block is not None:
            return build_result(
                warnings=join_warnings(prepared.preprocess_warnings, final_block.warning),
                request_id=request_id or final_block.request_id,
                cust_usd=Decimal(str(payload.get("cost") or "0")),
            )
        sample_url = _extract_bfl_sample_url(final_payload)
        if not sample_url:
            return build_result(
                warnings=join_warnings(
                    prepared.preprocess_warnings,
                    f"BFL polling did not reach a downloadable image. Final status: {final_payload.get('status') or 'unknown'}.",
                ),
                request_id=request_id,
                cust_usd=Decimal(str(payload.get("cost") or "0")),
            )
        return build_result(
            base64_value=download_image_as_base64_png(
                str(sample_url),
                timeout_seconds=timeout_seconds,
            ),
            warnings=prepared.preprocess_warnings,
            request_id=request_id,
            cust_usd=Decimal(str(payload.get("cost") or "0")),
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
    output_format: str,
    timeout_seconds: int,
    build_result: Callable[..., ImageOperationResult],
    seed: int | None = None,
    extra_body: dict | None = None,
) -> ImageOperationResult:
    """Execute Black Forest Labs reference-guided image generation."""

    try:
        warnings = ""
        if prepared.base_image is not None:
            input_image = image_to_data_url(prepared.base_image)
            references = prepared.reference_images
        else:
            input_image = image_to_data_url(prepared.reference_images[0])
            references = prepared.reference_images[1:]
            warnings = (
                "BFL FLUX.2 requires an input_image anchor, so the first reference image was treated as the editable base."
            )

        body: dict[str, str | int] = {
            "prompt": prepared.prompt,
            "input_image": input_image,
            "output_format": output_format,
        }
        if seed is not None:
            body["seed"] = seed
        if extra_body:
            body.update(extra_body)
        for index, image in enumerate(references, start=2):
            body[f"input_image_{index}"] = image_to_data_url(image)

        response = request(
            "POST",
            f"{_BFL_BASE_URL}/{model}",
            headers={"x-key": api_key, "Content-Type": "application/json"},
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
        poll_url = payload.get("polling_url")
        if not poll_url:
            return build_result(
                warnings="BFL did not return a polling_url for remix.",
                request_id=request_id,
            )
        final_payload = _poll_bfl(
            polling_url=str(poll_url),
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        final_block = detect_block(final_payload, operation="remix")
        if final_block is not None:
            return build_result(
                warnings=join_warnings(warnings, final_block.warning),
                request_id=request_id or final_block.request_id,
                cust_usd=Decimal(str(payload.get("cost") or "0")),
            )
        sample_url = _extract_bfl_sample_url(final_payload)
        if not sample_url:
            return build_result(
                warnings=join_warnings(
                    warnings,
                    f"BFL polling did not reach a downloadable image. Final status: {final_payload.get('status') or 'unknown'}.",
                ),
                request_id=request_id,
                cust_usd=Decimal(str(payload.get("cost") or "0")),
            )
        return build_result(
            base64_value=download_image_as_base64_png(
                str(sample_url),
                timeout_seconds=timeout_seconds,
            ),
            warnings=warnings,
            request_id=request_id,
            cust_usd=Decimal(str(payload.get("cost") or "0")),
        )
    except Exception as exc:
        return build_result(warnings=provider_error_to_warning(exc))
