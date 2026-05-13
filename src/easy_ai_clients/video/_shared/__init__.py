"""Shared helpers for provider wrappers.

The public SDK intentionally keeps provider modules small and explicit. Shared
helpers here cover only transport, environment, media preparation, validation,
polling, downloads, and result normalization.
"""

import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

FAL_QUEUE_BASE_URL = "https://queue.fal.run"
FAL_API_BASE_URL = "https://api.fal.ai/v1"
RUNWAY_BASE_URL = "https://api.dev.runwayml.com"
RUNWAY_API_VERSION = "2024-11-06"
GOOGLE_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def require_env(name, provider):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required for {provider} API requests.")
    return value


def clean_text(value, field_name):
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required.")
    return text


def normalize_output_path(output_path):
    if output_path is None:
        return None
    value = str(output_path).strip()
    if not value:
        return None
    path = Path(value)
    if not path.suffix:
        path = path.with_suffix(".mp4")
    return str(path)


def resolve_existing_file(path, field_name):
    value = str(path or "").strip()
    if not value:
        raise ValueError(f"{field_name} is required.")
    resolved = Path(value).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"{field_name} does not exist: {resolved}")
    return str(resolved)


def local_file_to_data_url(path):
    resolved = resolve_existing_file(path, "media_path")
    mime_type = mimetypes.guess_type(resolved)[0] or "application/octet-stream"
    with open(resolved, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return "data:" + mime_type + ";base64," + encoded


def local_file_to_base64_object(path):
    resolved = resolve_existing_file(path, "image_path")
    mime_type = mimetypes.guess_type(resolved)[0] or "image/png"
    with open(resolved, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return {"mimeType": mime_type, "bytesBase64Encoded": encoded}


def media_reference(path, url, path_name, url_name, allow_data_url=True):
    if path and url:
        raise ValueError(f"Provide either {path_name} or {url_name}, not both.")
    if url:
        value = str(url).strip()
        if not value:
            raise ValueError(f"{url_name} cannot be empty.")
        if not allow_data_url and value.startswith("data:"):
            raise ValueError(f"{url_name} cannot be a data URL for this provider.")
        return value
    if path:
        return local_file_to_data_url(path)
    return None


def http_json(method, url, headers=None, payload=None, timeout_seconds=None):
    request_headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(
        url,
        data=data,
        headers=request_headers,
        method=str(method).upper(),
    )
    timeout = float(timeout_seconds or 60)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            if not body:
                return {}
            return json.loads(body.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = compact_whitespace(body[:1200]) or str(exc)
        raise RuntimeError(f"HTTP {exc.code} from {url}: {message}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc.reason}") from exc


def download_file(url, output_path, headers=None, timeout_seconds=None):
    if not output_path:
        return None
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(str(url), headers=dict(headers or {}), method="GET")
    timeout = float(timeout_seconds or 120)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            with target.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = compact_whitespace(body[:1200]) or str(exc)
        raise RuntimeError(f"Download failed with HTTP {exc.code}: {message}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Download failed for {url}: {exc.reason}") from exc
    return str(target)


def normalize_result(provider, model, status=None, request_id=None, video_url=None, output_path=None, cost_usd=None, cost_is_estimated=True, cost_source=None, raw_response=None, extra=None):
    if cost_usd is None:
        raise RuntimeError(f"Cost calculation uncertainty for {provider} {model}.")
    if cost_source is None:
        raise RuntimeError(f"cost_source is required for {provider} {model}.")
    result = {
        "provider": provider,
        "model": model,
        "status": status or "completed",
        "request_id": request_id,
        "video_url": video_url,
        "output_path": output_path,
        "cost_usd": float(cost_usd),
        "cost_is_estimated": bool(cost_is_estimated),
        "cost_source": cost_source,
        "raw_response": raw_response or {},
    }
    if extra:
        result.update(dict(extra))
    return result


def validate_allowed_kwargs(kwargs, allowed_names, model, provider, context, common_names=None):
    common = set(common_names or [])
    unsupported = []
    for name in kwargs:
        if name in allowed_names or name in common:
            continue
        unsupported.append(name)
    if unsupported:
        joined = ", ".join(sorted(unsupported))
        raise ValueError(f"Unsupported parameter(s) for {provider} {context} model {model}: {joined}.")


def validate_enum(name, value, allowed_values, provider, model):
    if value is None:
        return
    if str(value) not in set(allowed_values):
        joined = ", ".join(str(item) for item in allowed_values)
        raise ValueError(f"Invalid {name} for {provider} model {model}: {value}. Allowed values: {joined}.")


def validate_number(name, value, minimum, maximum, provider, model):
    if value is None:
        return
    parsed = float(value)
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"Invalid {name} for {provider} model {model}: {value}. Expected {minimum} to {maximum}.")


def merge_extra_payload(payload, kwargs):
    extra_payload = kwargs.get("extra_payload")
    if extra_payload is None:
        return payload
    if not isinstance(extra_payload, dict):
        raise ValueError("extra_payload must be a dictionary when provided.")
    merged = dict(payload)
    merged.update(extra_payload)
    return merged


def compact_whitespace(value):
    return " ".join(str(value or "").split())


def fal_headers(api_key):
    return {"Authorization": "Key " + api_key, "Content-Type": "application/json"}


def fal_submit(model, payload, api_key, timeout_seconds=None):
    return http_json(
        "POST",
        FAL_QUEUE_BASE_URL + "/" + model,
        headers=fal_headers(api_key),
        payload=payload,
        timeout_seconds=timeout_seconds,
    )


def fal_status_url(model, request_id):
    return FAL_QUEUE_BASE_URL + "/" + model + "/requests/" + urllib.parse.quote(str(request_id), safe="") + "/status"


def fal_response_url(model, request_id):
    return FAL_QUEUE_BASE_URL + "/" + model + "/requests/" + urllib.parse.quote(str(request_id), safe="") + "/response"


def fal_get_status(model, request_id, api_key, timeout_seconds=None):
    return http_json("GET", fal_status_url(model, request_id) + "?logs=1", headers=fal_headers(api_key), timeout_seconds=timeout_seconds)


def fal_get_result(model, request_id, api_key, timeout_seconds=None):
    return http_json("GET", fal_response_url(model, request_id), headers=fal_headers(api_key), timeout_seconds=timeout_seconds)


def normalize_fal_status(value):
    status = str(value or "").upper()
    if status in ("COMPLETED", "OK"):
        return "completed"
    if status in ("IN_PROGRESS", "PROCESSING", "RUNNING"):
        return "running"
    if status in ("IN_QUEUE", "QUEUED"):
        return "queued"
    if status in ("CANCELED", "CANCELLED"):
        return "canceled"
    if status in ("FAILED", "ERROR", "REJECTED"):
        return "failed"
    return "submitted"


def fal_wait_for_result(model, request_id, api_key, timeout_seconds=None, poll_interval_seconds=None):
    deadline = time.monotonic() + float(timeout_seconds or 900)
    interval = float(poll_interval_seconds or 5)
    last_status = {}
    while time.monotonic() < deadline:
        last_status = fal_get_status(model, request_id, api_key, timeout_seconds=60)
        normalized = normalize_fal_status(last_status.get("status"))
        if normalized == "completed":
            result = fal_get_result(model, request_id, api_key, timeout_seconds=60)
            return {"status": last_status, "response": result}
        if normalized in ("failed", "canceled"):
            raise RuntimeError(f"fal.ai generation {request_id} ended with status {last_status}.")
        time.sleep(max(0.5, interval))
    raise TimeoutError(f"fal.ai generation {request_id} timed out. Last status: {last_status}")


def extract_video_url(response):
    if not isinstance(response, dict):
        return None
    video = response.get("video")
    if isinstance(video, str):
        return video
    if isinstance(video, dict) and video.get("url"):
        return video.get("url")
    videos = response.get("videos") or response.get("generated_videos")
    if isinstance(videos, list) and videos:
        first = videos[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            nested = first.get("video")
            if isinstance(nested, dict) and nested.get("url"):
                return nested.get("url")
            if first.get("url"):
                return first.get("url")
    output = response.get("output")
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            nested = first.get("video")
            if isinstance(nested, str):
                return nested
            if isinstance(nested, dict) and nested.get("url"):
                return nested.get("url")
            return first.get("url") or first.get("uri")
    if isinstance(output, str):
        return output
    if isinstance(output, dict):
        nested = output.get("video")
        if isinstance(nested, str):
            return nested
        if isinstance(nested, dict) and nested.get("url"):
            return nested.get("url")
        return output.get("url") or output.get("uri")
    return response.get("video_url") or response.get("url")


def runway_headers(api_key):
    return {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
        "X-Runway-Version": RUNWAY_API_VERSION,
    }


def runway_submit(endpoint, payload, api_key, timeout_seconds=None):
    return http_json(
        "POST",
        RUNWAY_BASE_URL + endpoint,
        headers=runway_headers(api_key),
        payload=payload,
        timeout_seconds=timeout_seconds,
    )


def runway_get_task(task_id, api_key, timeout_seconds=None):
    return http_json("GET", RUNWAY_BASE_URL + "/v1/tasks/" + urllib.parse.quote(str(task_id), safe=""), headers=runway_headers(api_key), timeout_seconds=timeout_seconds)


def normalize_runway_status(value):
    status = str(value or "").upper()
    if status == "SUCCEEDED":
        return "completed"
    if status in ("RUNNING", "THROTTLED"):
        return "running"
    if status in ("PENDING", "QUEUED"):
        return "queued"
    if status == "FAILED":
        return "failed"
    if status == "CANCELED":
        return "canceled"
    return "submitted"


def runway_wait_for_task(task_id, api_key, timeout_seconds=None, poll_interval_seconds=None):
    deadline = time.monotonic() + float(timeout_seconds or 900)
    interval = float(poll_interval_seconds or 5)
    last_status = {}
    while time.monotonic() < deadline:
        last_status = runway_get_task(task_id, api_key, timeout_seconds=60)
        normalized = normalize_runway_status(last_status.get("status"))
        if normalized == "completed":
            return last_status
        if normalized in ("failed", "canceled"):
            raise RuntimeError(f"Runway task {task_id} ended with status {last_status}.")
        time.sleep(max(1, interval))
    raise TimeoutError(f"Runway task {task_id} timed out. Last status: {last_status}")


def google_headers(api_key):
    return {"x-goog-api-key": api_key, "Content-Type": "application/json"}


def google_operation_url(operation_name):
    name = str(operation_name or "").lstrip("/")
    if name.startswith("https://"):
        return name
    return GOOGLE_GEMINI_BASE_URL + "/" + name


def google_get_operation(operation_name, api_key, timeout_seconds=None):
    return http_json("GET", google_operation_url(operation_name), headers=google_headers(api_key), timeout_seconds=timeout_seconds)


def google_extract_video_url(operation):
    response = operation.get("response") if isinstance(operation, dict) else None
    if not isinstance(response, dict):
        return None
    video_response = response.get("generateVideoResponse") or response.get("generate_video_response")
    if not isinstance(video_response, dict):
        return None
    samples = video_response.get("generatedSamples") or video_response.get("generated_samples") or []
    if not samples:
        return None
    first = samples[0]
    if not isinstance(first, dict):
        return None
    video = first.get("video") or {}
    if isinstance(video, dict):
        return video.get("uri") or video.get("url")
    return None


def google_wait_for_operation(operation_name, api_key, timeout_seconds=None, poll_interval_seconds=None):
    deadline = time.monotonic() + float(timeout_seconds or 900)
    interval = float(poll_interval_seconds or 10)
    last_status = {}
    while time.monotonic() < deadline:
        last_status = google_get_operation(operation_name, api_key, timeout_seconds=60)
        if last_status.get("done") is True:
            if last_status.get("error"):
                raise RuntimeError(f"Google Veo operation failed: {last_status.get('error')}")
            return last_status
        time.sleep(max(1, interval))
    raise TimeoutError(f"Google Veo operation {operation_name} timed out. Last status: {last_status}")
