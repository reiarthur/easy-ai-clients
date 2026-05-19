"""Small shared wrappers for provider image endpoints not covered elsewhere."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from typing import Any

from .._analyze.pre_processing import prepare_analyze_inputs
from .._edit.pre_processing import prepare_edit_inputs
from .._generate.pre_processing import prepare_generate_inputs
from .env_utils import get_provider_api_key
from .http_utils import request
from .image_utils import image_to_base64, image_to_data_url, image_to_png_bytes, multipart_image
from .provider_utils import (
    analyze_result,
    extract_image_output,
    extract_request_id,
    extract_text_from_openai_style_response,
    image_bytes_to_base64_png,
    image_result,
    provider_error_to_warning,
    response_json,
)


def openai_compatible_generate(
    *,
    provider_label: str,
    env_var: str,
    url: str,
    prompt: str,
    model: str,
    size: str = "1024x1024",
    quality: str | None = None,
    output_format: str = "png",
    timeout_seconds: int = 120,
    extra_body: Mapping[str, Any] | None = None,
):
    try:
        prepared = prepare_generate_inputs(prompt)
        payload = {
            "model": model,
            "prompt": prepared.prompt,
            "size": size,
            "response_format": "b64_json",
        }
        if quality:
            payload["quality"] = quality
        if output_format:
            payload["output_format"] = output_format
        if extra_body:
            payload.update(dict(extra_body))
        response = request(
            "POST",
            url,
            headers={"Authorization": f"Bearer {get_provider_api_key(provider_label, env_var)}"},
            json=payload,
            timeout_seconds=timeout_seconds,
        )
        raw = response_json(response)
        base64_value, warning = extract_image_output(raw, timeout_seconds=timeout_seconds)
        return image_result(
            base64_value=base64_value,
            warnings=warning,
            request_id=extract_request_id(response, raw),
            cost_source="unavailable",
            cost_is_estimated=False,
            cost_details={"model": model},
        )
    except Exception as exc:
        return image_result(warnings=provider_error_to_warning(exc))


def openai_compatible_edit(
    *,
    provider_label: str,
    env_var: str,
    url: str,
    prompt: str,
    image: str,
    model: str,
    mask: str | None = None,
    size: str = "1024x1024",
    quality: str | None = None,
    output_format: str = "png",
    timeout_seconds: int = 120,
    extra_body: Mapping[str, Any] | None = None,
):
    try:
        prepared = prepare_edit_inputs(prompt, image, provider="openai", mask=mask)
        data = {
            "model": model,
            "prompt": prepared.prompt,
            "size": size,
            "response_format": "b64_json",
        }
        if quality:
            data["quality"] = quality
        if output_format:
            data["output_format"] = output_format
        if extra_body:
            data.update(dict(extra_body))
        files = [
            multipart_image(
                "image",
                image_to_png_bytes(prepared.image),
                filename="image.png",
                mime_type="image/png",
            )
        ]
        if prepared.provider_mask_bytes:
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
            url,
            headers={"Authorization": f"Bearer {get_provider_api_key(provider_label, env_var)}"},
            data=data,
            files=files,
            timeout_seconds=timeout_seconds,
        )
        raw = response_json(response)
        base64_value, warning = extract_image_output(raw, timeout_seconds=timeout_seconds)
        return image_result(
            base64_value=base64_value,
            warnings=warning,
            request_id=extract_request_id(response, raw),
            cost_source="unavailable",
            cost_is_estimated=False,
            cost_details={"model": model},
        )
    except Exception as exc:
        return image_result(warnings=provider_error_to_warning(exc))


def huggingface_generate(
    *,
    prompt: str,
    model: str,
    timeout_seconds: int = 120,
    parameters: Mapping[str, Any] | None = None,
):
    try:
        prepared = prepare_generate_inputs(prompt)
        response = request(
            "POST",
            f"https://api-inference.huggingface.co/models/{model}",
            headers={
                "Authorization": f"Bearer {get_provider_api_key('Hugging Face', 'HUGGINGFACE_API_KEY')}",
                "Accept": "image/png",
            },
            json={"inputs": prepared.prompt, "parameters": dict(parameters or {})},
            timeout_seconds=timeout_seconds,
        )
        if response.headers.get("content-type", "").startswith("application/json"):
            raw = response_json(response)
            base64_value, warning = extract_image_output(raw, timeout_seconds=timeout_seconds)
            return image_result(base64_value=base64_value, warnings=warning, request_id=extract_request_id(response, raw))
        return image_result(
            base64_value=image_bytes_to_base64_png(response.content),
            request_id=extract_request_id(response, {}),
            cost_source="unavailable",
            cost_is_estimated=False,
            cost_details={"model": model},
        )
    except Exception as exc:
        return image_result(warnings=provider_error_to_warning(exc))


def huggingface_image_to_image(
    *,
    prompt: str,
    images: list[Any],
    model: str,
    timeout_seconds: int = 120,
    parameters: Mapping[str, Any] | None = None,
):
    try:
        payload = {
            "inputs": prompt,
            "parameters": {
                **dict(parameters or {}),
                "images": [image_to_base64(image) for image in images],
            },
        }
        response = request(
            "POST",
            f"https://api-inference.huggingface.co/models/{model}",
            headers={
                "Authorization": f"Bearer {get_provider_api_key('Hugging Face', 'HUGGINGFACE_API_KEY')}",
                "Accept": "image/png",
            },
            json=payload,
            timeout_seconds=timeout_seconds,
        )
        if response.headers.get("content-type", "").startswith("application/json"):
            raw = response_json(response)
            base64_value, warning = extract_image_output(raw, timeout_seconds=timeout_seconds)
            return image_result(base64_value=base64_value, warnings=warning, request_id=extract_request_id(response, raw))
        return image_result(
            base64_value=image_bytes_to_base64_png(response.content),
            request_id=extract_request_id(response, {}),
            cost_source="unavailable",
            cost_is_estimated=False,
            cost_details={"model": model},
        )
    except Exception as exc:
        return image_result(warnings=provider_error_to_warning(exc))


def openai_style_vision_analyze(
    *,
    provider_label: str,
    env_var: str,
    url: str,
    prompt: str,
    image: str,
    model: str,
    timeout_seconds: int = 60,
    extra_body: Mapping[str, Any] | None = None,
):
    input_text = prompt.strip() if isinstance(prompt, str) else ""
    try:
        prepared = prepare_analyze_inputs(prompt, image)
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prepared.prompt},
                        {"type": "image_url", "image_url": {"url": image_to_data_url(prepared.image)}},
                    ],
                }
            ],
        }
        if extra_body:
            payload.update(dict(extra_body))
        response = request(
            "POST",
            url,
            headers={
                "Authorization": f"Bearer {get_provider_api_key(provider_label, env_var)}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout_seconds=timeout_seconds,
        )
        raw = response_json(response)
        return analyze_result(
            request_id=extract_request_id(response, raw),
            input_text=input_text,
            output=extract_text_from_openai_style_response(raw),
            cost_source="provider_response" if _usage_cost(raw) is not None else "unavailable",
            cost_usd=_usage_cost(raw) or 0.0,
            cost_is_estimated=False,
            cost_details={"usage": raw.get("usage") or {}, "model": model},
        )
    except Exception as exc:
        return analyze_result(input_text=input_text, output=provider_error_to_warning(exc))


def huggingface_analyze(
    *,
    prompt: str,
    image: str,
    model: str,
    timeout_seconds: int = 60,
    parameters: Mapping[str, Any] | None = None,
):
    input_text = prompt.strip() if isinstance(prompt, str) else ""
    try:
        prepared = prepare_analyze_inputs(prompt, image)
        response = request(
            "POST",
            f"https://api-inference.huggingface.co/models/{model}",
            headers={
                "Authorization": f"Bearer {get_provider_api_key('Hugging Face', 'HUGGINGFACE_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "inputs": {
                    "text": prepared.prompt,
                    "image": base64.b64encode(prepared.image.raw_bytes).decode("ascii"),
                },
                "parameters": dict(parameters or {}),
            },
            timeout_seconds=timeout_seconds,
        )
        raw = response_json(response)
        output = raw.get("generated_text") or raw.get("answer") or raw.get("text") or str(raw)
        return analyze_result(
            request_id=extract_request_id(response, raw),
            input_text=input_text,
            output=str(output),
            cost_source="unavailable",
            cost_is_estimated=False,
            cost_details={"model": model},
        )
    except Exception as exc:
        return analyze_result(input_text=input_text, output=provider_error_to_warning(exc))


def _usage_cost(raw: Mapping[str, Any]) -> float | None:
    usage = raw.get("usage") or {}
    if not isinstance(usage, Mapping):
        return None
    for key in ("cost", "total_cost"):
        if usage.get(key) is not None:
            return float(usage[key])
    return None


__all__ = [
    "huggingface_analyze",
    "huggingface_generate",
    "huggingface_image_to_image",
    "openai_compatible_edit",
    "openai_compatible_generate",
    "openai_style_vision_analyze",
]
