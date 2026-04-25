"""Official provider catalog discovery helpers."""

from __future__ import annotations

from typing import Any

from .http_utils import request
from .provider_utils import response_json


def fetch_openai_models(api_key: str, *, timeout_seconds: int = 60) -> list[dict[str, Any]]:
    """Return the live OpenAI model catalog visible to the account."""

    response = request(
        "GET",
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout_seconds=timeout_seconds,
    )
    data = response_json(response).get("data", [])
    return data if isinstance(data, list) else []


def fetch_anthropic_models(api_key: str, *, timeout_seconds: int = 60) -> list[dict[str, Any]]:
    """Return the live Anthropic model catalog visible to the account."""

    response = request(
        "GET",
        "https://api.anthropic.com/v1/models",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        timeout_seconds=timeout_seconds,
    )
    data = response_json(response).get("data", [])
    return data if isinstance(data, list) else []


def fetch_gemini_models(api_key: str, *, timeout_seconds: int = 60) -> list[dict[str, Any]]:
    """Return the live Gemini model catalog visible to the account."""

    response = request(
        "GET",
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": api_key},
        timeout_seconds=timeout_seconds,
    )
    data = response_json(response).get("models", [])
    return data if isinstance(data, list) else []


def fetch_groq_models(api_key: str, *, timeout_seconds: int = 60) -> list[dict[str, Any]]:
    """Return the live Groq OpenAI-compatible model catalog."""

    response = request(
        "GET",
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout_seconds=timeout_seconds,
    )
    data = response_json(response).get("data", [])
    return data if isinstance(data, list) else []


def fetch_openrouter_models(*, timeout_seconds: int = 60) -> list[dict[str, Any]]:
    """Return the public OpenRouter model catalog with modality metadata."""

    response = request(
        "GET",
        "https://openrouter.ai/api/v1/models?output_modalities=all",
        timeout_seconds=timeout_seconds,
    )
    data = response_json(response).get("data", [])
    return data if isinstance(data, list) else []


def fetch_together_models(api_key: str, *, timeout_seconds: int = 60) -> list[dict[str, Any]]:
    """Return the live Together AI model catalog visible to the account."""

    response = request(
        "GET",
        "https://api.together.xyz/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout_seconds=timeout_seconds,
    )
    payload = response_json(response)
    if isinstance(payload, list):
        return payload
    data = payload.get("data", [])
    return data if isinstance(data, list) else []


def fetch_fireworks_models(api_key: str, *, timeout_seconds: int = 60) -> list[dict[str, Any]]:
    """Return the live Fireworks model catalog visible to the account."""

    response = request(
        "GET",
        "https://api.fireworks.ai/inference/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout_seconds=timeout_seconds,
    )
    data = response_json(response).get("data", [])
    return data if isinstance(data, list) else []


def fetch_xai_models(api_key: str, *, timeout_seconds: int = 60) -> list[dict[str, Any]]:
    """Return the live xAI model catalog visible to the account."""

    response = request(
        "GET",
        "https://api.x.ai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout_seconds=timeout_seconds,
    )
    data = response_json(response).get("data", [])
    return data if isinstance(data, list) else []


def fetch_falai_models(
    api_key: str,
    *,
    category: str | None = None,
    timeout_seconds: int = 60,
    max_pages: int = 20,
) -> list[dict[str, Any]]:
    """Return paginated fal.ai model catalog entries for an optional category."""

    models: list[dict[str, Any]] = []
    cursor: str | None = None
    for _ in range(max_pages):
        params: dict[str, Any] = {}
        if category:
            params["category"] = category
        if cursor:
            params["cursor"] = cursor
        response = request(
            "GET",
            "https://api.fal.ai/v1/models",
            headers={"Authorization": f"Key {api_key}"},
            params=params,
            timeout_seconds=timeout_seconds,
        )
        payload = response_json(response)
        data = payload.get("models") or payload.get("data") or payload.get("results") or []
        if isinstance(data, list):
            models.extend(item for item in data if isinstance(item, dict))
        cursor = payload.get("next_cursor") or payload.get("cursor")
        if not payload.get("has_more") or not cursor:
            break
    return models


def model_ids(models: list[dict[str, Any]]) -> list[str]:
    """Return sorted model ids from heterogeneous provider catalog rows."""

    ids: set[str] = set()
    for item in models:
        value = item.get("id") or item.get("name") or item.get("model_id")
        if value:
            ids.add(str(value))
    return sorted(ids)
