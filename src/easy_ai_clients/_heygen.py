"""Shared HeyGen v3 transport and payload helpers."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.heygen.com"
ENV_NAME = "HEYGEN_KEY"
ALT_ENV_NAME = "HEYGEN_API_KEY"
PROVIDER = "heygen"
USER_AGENT = "easy-ai-clients/heygen-v3"


def require_api_key() -> str:
    """Return the configured HeyGen API key without exposing it in messages."""

    load_dotenv()
    value = os.getenv(ENV_NAME) or os.getenv(ALT_ENV_NAME)
    if not value:
        raise RuntimeError(f"{ENV_NAME} is required for HeyGen API requests.")
    return value


def api_base_url() -> str:
    """Return the HeyGen API base URL, allowing tests to override it."""

    return str(os.getenv("HEYGEN_API_BASE") or BASE_URL).rstrip("/")


def api_headers(api_key: str | None = None, *, content_type: str | None = "application/json") -> dict[str, str]:
    """Build HeyGen v3 request headers."""

    headers = {
        "x-api-key": api_key or require_api_key(),
        "User-Agent": USER_AGENT,
        "X-HeyGen-Source": "easy-ai-clients",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def compact_whitespace(value: Any) -> str:
    return " ".join(str(value or "").split())


def clean_payload(value: Any) -> Any:
    """Drop only None values from request payloads while preserving falsey data."""

    if isinstance(value, Mapping):
        return {
            str(key): clean_payload(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list | tuple):
        return [clean_payload(item) for item in value if item is not None]
    return value


def quote_path(value: Any) -> str:
    return quote(str(value), safe="")


def data(raw: Mapping[str, Any] | Any) -> Any:
    """Return the HeyGen response data envelope when present."""

    if isinstance(raw, Mapping) and "data" in raw:
        return raw["data"]
    return raw


def request_json(
    method: str,
    path: str,
    *,
    payload: Mapping[str, Any] | None = None,
    params: Mapping[str, Any] | None = None,
    api_key: str | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Execute a HeyGen JSON request and return the decoded response body."""

    url = path if str(path).startswith(("http://", "https://")) else api_base_url() + path
    body = None if payload is None else clean_payload(payload)
    response = requests.request(
        str(method).upper(),
        url,
        headers=api_headers(api_key),
        params=clean_payload(params or {}),
        json=body,
        timeout=float(timeout_seconds or 60),
    )
    if response.status_code >= 400:
        raise RuntimeError(_error_message(response, url))
    if not response.content:
        return {}
    try:
        parsed = response.json()
    except ValueError as error:
        raise RuntimeError(f"HeyGen returned non-JSON response from {url}.") from error
    if not isinstance(parsed, dict):
        return {"data": parsed}
    return parsed


def request_text(
    method: str,
    path: str,
    *,
    params: Mapping[str, Any] | None = None,
    api_key: str | None = None,
    timeout_seconds: float | None = None,
) -> str:
    """Execute a HeyGen request that may return text instead of JSON."""

    url = path if str(path).startswith(("http://", "https://")) else api_base_url() + path
    response = requests.request(
        str(method).upper(),
        url,
        headers=api_headers(api_key, content_type=None),
        params=clean_payload(params or {}),
        timeout=float(timeout_seconds or 60),
    )
    if response.status_code >= 400:
        raise RuntimeError(_error_message(response, url))
    return response.text


def download_url(url: str, *, timeout_seconds: float | None = None) -> bytes:
    response = requests.get(str(url), timeout=float(timeout_seconds or 120))
    if response.status_code >= 400:
        raise RuntimeError(_error_message(response, str(url)))
    return bytes(response.content or b"")


def upload_asset(file_path: str | os.PathLike[str], *, timeout_seconds: float | None = None) -> dict[str, Any]:
    """Upload a local file to HeyGen assets and return the raw response."""

    resolved = resolve_file(file_path, "file")
    with open(resolved, "rb") as handle:
        response = requests.post(
            api_base_url() + "/v3/assets",
            headers=api_headers(content_type=None),
            files={
                "file": (
                    Path(resolved).name,
                    handle,
                    mimetypes.guess_type(resolved)[0] or "application/octet-stream",
                )
            },
            timeout=float(timeout_seconds or 120),
        )
    if response.status_code >= 400:
        raise RuntimeError(_error_message(response, api_base_url() + "/v3/assets"))
    if not response.content:
        return {}
    parsed = response.json()
    return parsed if isinstance(parsed, dict) else {"data": parsed}


def asset_input(value: Any, *, field_name: str = "asset", allow_base64: bool = True) -> dict[str, Any] | None:
    """Build a HeyGen AssetInput object from a URL, asset id, data URL, dict, or local file."""

    if value is None:
        return None
    if isinstance(value, Mapping):
        return clean_payload(dict(value))

    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty.")
    lower = text.lower()
    if lower.startswith(("http://", "https://")):
        return {"type": "url", "url": text}
    if lower.startswith("data:"):
        if not allow_base64:
            raise ValueError(f"{field_name} does not accept data URLs.")
        return _data_url_to_asset_input(text)
    path = Path(text).expanduser()
    if path.exists() and path.is_file():
        if not allow_base64:
            uploaded = data(upload_asset(path))
            if not isinstance(uploaded, Mapping) or not uploaded.get("asset_id"):
                raise RuntimeError(f"HeyGen asset upload for {field_name} did not return asset_id.")
            return {"type": "asset_id", "asset_id": uploaded["asset_id"]}
        return _file_to_asset_input(path)

    return {"type": "asset_id", "asset_id": text}


def resolve_file(file_path: str | os.PathLike[str], field_name: str) -> str:
    value = str(file_path or "").strip()
    if not value:
        raise ValueError(f"{field_name} is required.")
    resolved = Path(value).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"{field_name} does not exist: {resolved}")
    return str(resolved)


def media_url_or_asset_fields(
    *,
    path: Any = None,
    url: Any = None,
    asset_id: Any = None,
    url_key: str,
    asset_id_key: str,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Return direct *_url / *_asset_id fields for endpoints that do not use unions."""

    present = [item is not None for item in (path, url, asset_id)].count(True)
    if present > 1:
        raise ValueError(f"Provide only one of path, url, or asset_id for {url_key}.")
    if asset_id is not None:
        return {asset_id_key: str(asset_id)}
    if url is not None:
        return {url_key: str(url)}
    if path is not None:
        uploaded = data(upload_asset(path, timeout_seconds=timeout_seconds))
        if not isinstance(uploaded, Mapping) or not uploaded.get("asset_id"):
            raise RuntimeError(f"HeyGen asset upload for {path} did not return asset_id.")
        return {asset_id_key: uploaded["asset_id"]}
    return {}


def normalize_status(value: Any) -> str:
    status = str(value or "").strip().lower()
    if status in {"completed", "complete", "success", "succeeded", "ready"}:
        return "completed"
    if status in {"failed", "fail", "error", "rejected"}:
        return "failed"
    if status in {"processing", "running", "generating", "thinking", "reviewing"}:
        return "running"
    if status in {"pending", "waiting", "queued"}:
        return "queued"
    if status in {"cancelled", "canceled"}:
        return "canceled"
    return "submitted"


def wait_for_result(
    getter: Callable[[], Mapping[str, Any]],
    *,
    timeout_seconds: float | None = None,
    poll_interval_seconds: float | None = None,
) -> dict[str, Any]:
    """Poll a HeyGen detail endpoint until it reaches a terminal status."""

    deadline = time.monotonic() + float(timeout_seconds or 1800)
    interval = float(poll_interval_seconds or 10)
    last_raw: Mapping[str, Any] = {}
    while time.monotonic() < deadline:
        last_raw = getter()
        item = data(last_raw)
        status = normalize_status(item.get("status") if isinstance(item, Mapping) else None)
        if status == "completed":
            return dict(last_raw)
        if status in {"failed", "canceled"}:
            raise RuntimeError(f"HeyGen job ended with status {item}.")
        time.sleep(max(1.0, interval))
    raise TimeoutError(f"HeyGen job timed out. Last status: {last_raw}")


def response_id(payload: Any, *names: str) -> str | None:
    item = data(payload)
    if not isinstance(item, Mapping):
        return None
    for name in names:
        value = item.get(name)
        if value:
            return str(value)
    return None


def _file_to_asset_input(path: Path) -> dict[str, str]:
    media_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    with path.open("rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return {"type": "base64", "media_type": media_type, "data": encoded}


def _data_url_to_asset_input(value: str) -> dict[str, str]:
    prefix, _, encoded = value.partition(",")
    media_type = "application/octet-stream"
    if prefix.startswith("data:"):
        media_type = prefix[5:].split(";", 1)[0] or media_type
    if not encoded:
        raise ValueError("data URL did not include a base64 payload.")
    return {"type": "base64", "media_type": media_type, "data": encoded}


def _error_message(response: requests.Response, url: str) -> str:
    request_id = response.headers.get("X-Request-Id") or response.headers.get("x-request-id")
    details = ""
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, Mapping):
        error = payload.get("error")
        if isinstance(error, Mapping):
            pieces = [
                str(error.get("code") or "").strip(),
                str(error.get("message") or "").strip(),
                str(error.get("param") or "").strip(),
            ]
            details = compact_whitespace(" ".join(piece for piece in pieces if piece))
        else:
            details = compact_whitespace(json.dumps(payload, ensure_ascii=True)[:1200])
    if not details:
        details = compact_whitespace(response.text[:1200]) or response.reason
    if request_id:
        return f"HTTP {response.status_code} from {url} request_id={request_id}: {details}"
    return f"HTTP {response.status_code} from {url}: {details}"
