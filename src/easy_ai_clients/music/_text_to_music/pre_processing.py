from urllib.parse import urljoin

CONTROL_KWARGS = {
    "base_url",
    "download_timeout",
    "endpoint_url",
    "headers",
    "max_polls",
    "operation_url",
    "params",
    "poll_interval",
    "response_url",
    "result_url",
    "retries",
    "status_url",
    "task_url",
    "timeout",
}

SECRET_MARKERS = (
    "api_key",
    "apikey",
    "api-token",
    "api_token",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "password",
    "secret",
    "signature",
    "token",
)


def prepare_text_to_music(prompt, kwargs=None):
    """Prepare a text-to-music prompt for provider payloads.

    Args:
        prompt: Required. Text prompt or music brief.
        kwargs: Optional. Provider keyword arguments.

    Returns:
        A dictionary with the normalized prompt.

    Raises:
        ValueError: If the prompt is empty.
    """
    if prompt is None:
        raise ValueError("prompt is required.")

    text = str(prompt).strip()
    if not text:
        raise ValueError("prompt must be a non-empty string.")

    return {"prompt": text}


def selected_model(kwargs, default=None, required=False, default_model=None):
    """Return the selected provider model.

    Args:
        kwargs: Required. Provider keyword arguments.
        default: Optional. Default model when documented.
        required: Optional. Whether a model must be available.
        default_model: Optional. Backwards-compatible default argument.

    Returns:
        The selected model.

    Raises:
        RuntimeError: If a required model is missing.
    """
    if default is None:
        default = default_model
    model = kwargs.pop("model", None) or default
    if required and not model:
        raise RuntimeError("model is required for this provider.")
    return model


def add_if_present(payload, kwargs, *keys):
    """Copy non-None kwargs into a payload.

    Args:
        payload: Required. Payload dictionary to update.
        kwargs: Required. Provider keyword arguments.
        *keys: Required. Keys to copy when present.

    Returns:
        The updated payload dictionary.
    """
    for key in keys:
        if key in kwargs and kwargs[key] is not None:
            payload[key] = kwargs[key]
    return payload


def safe_payload_kwargs(kwargs, handled=None):
    """Return kwargs that are safe to forward to a provider payload.

    Args:
        kwargs: Required. Provider keyword arguments.
        handled: Optional. Keys already handled by the explicit builder.

    Returns:
        A dictionary of provider-native kwargs.
    """
    handled = set(handled or ())
    payload = {}
    for key, value in dict(kwargs or {}).items():
        if value is None:
            continue
        if key in handled:
            continue
        if not _is_safe_payload_key(key):
            continue
        payload[key] = value
    return payload


def payload_kwargs(kwargs, exclude=None):
    """Return provider kwargs that should be sent in the request payload.

    Args:
        kwargs: Required. Provider kwargs.
        exclude: Optional. Extra keys to omit.

    Returns:
        A payload dictionary without transport/control kwargs.
    """
    omitted = set(CONTROL_KWARGS)
    omitted.update(exclude or ())
    return {
        key: value
        for key, value in dict(kwargs or {}).items()
        if key not in omitted and value is not None and _is_safe_payload_key(key)
    }


def prepared_prompt(prompt, kwargs=None, prompt_key="prompt", exclude=None):
    """Build a text-to-music payload with a prompt field.

    Args:
        prompt: Required. Text prompt supplied by the caller.
        kwargs: Optional. Provider kwargs.
        prompt_key: Optional. Provider payload key for the prompt.
        exclude: Optional. Extra keys to omit.

    Returns:
        A payload dictionary.
    """
    payload = payload_kwargs(kwargs, exclude=exclude)
    if prompt_key not in payload and prompt is not None:
        payload[prompt_key] = prompt
    return compact_payload(payload)


def compact_payload(payload):
    """Remove keys with `None` values.

    Args:
        payload: Required. Payload dictionary.

    Returns:
        A compact payload dictionary.
    """
    return {
        key: value
        for key, value in dict(payload or {}).items()
        if value is not None
    }


def pop_option(kwargs, *names, default=None):
    """Pop the first present option from kwargs.

    Args:
        kwargs: Required. Provider kwargs.
        *names: Required. Candidate option names.
        default: Optional. Fallback value.

    Returns:
        The option value.
    """
    for name in names:
        if name in kwargs:
            return kwargs.pop(name)
    return default


def request_timeout(kwargs, default=60):
    """Return a request timeout without forwarding it to the provider body.

    Args:
        kwargs: Required. Provider keyword arguments.
        default: Optional. Default timeout in seconds.

    Returns:
        Timeout value in seconds.
    """
    return kwargs.get("timeout", default)


def request_retries(kwargs, default=2):
    """Return a retry count without forwarding it to the provider body.

    Args:
        kwargs: Required. Provider keyword arguments.
        default: Optional. Default retry count.

    Returns:
        Retry count.
    """
    return kwargs.get("retries", default)


def http_options(kwargs):
    """Return common HTTP options.

    Args:
        kwargs: Required. Provider kwargs.

    Returns:
        A dictionary with timeout and retry options.
    """
    return {
        "timeout": request_timeout(kwargs),
        "retries": request_retries(kwargs),
    }


def poll_settings(kwargs, interval=5, max_polls=60):
    """Return polling settings without forwarding them to the provider body.

    Args:
        kwargs: Required. Provider keyword arguments.
        interval: Optional. Default seconds between polls.
        max_polls: Optional. Default maximum poll attempts.

    Returns:
        A tuple with interval and maximum polls.
    """
    return kwargs.get("poll_interval", interval), kwargs.get("max_polls", max_polls)


def poll_options(kwargs):
    """Return common polling options.

    Args:
        kwargs: Required. Provider kwargs.

    Returns:
        A dictionary with polling settings.
    """
    interval, max_polls = poll_settings(kwargs)
    return {
        "poll_interval": interval,
        "max_polls": max_polls,
    }


def endpoint_from_base(base_url, path):
    """Build an endpoint from a documented base URL and path.

    Args:
        base_url: Required. Provider base URL.
        path: Required. Endpoint path.

    Returns:
        A full endpoint URL.
    """
    if not base_url:
        return None
    base = str(base_url).rstrip("/") + "/"
    return urljoin(base, str(path).lstrip("/"))


def missing_endpoint_error(provider, detail):
    """Return a clear error for incomplete local endpoint configuration.

    Args:
        provider: Required. Provider identifier.
        detail: Required. Missing documentation detail.

    Returns:
        RuntimeError with an actionable message.
    """
    return RuntimeError(
        f"{provider} text_to_music requires caller-supplied endpoint controls "
        f"because this wrapper does not define {detail}."
    )


def _is_safe_payload_key(key):
    """Return whether a key can be forwarded to a provider payload.

    Args:
        key: Required. Payload key.

    Returns:
        True when the key is safe to forward.
    """
    normalized = _normalize_key(key)
    if normalized in CONTROL_KWARGS:
        return False
    return not _looks_secret(normalized)


def _looks_secret(normalized_key):
    """Return whether a normalized key looks credential-like.

    Args:
        normalized_key: Required. Normalized key.

    Returns:
        True when the key should not be forwarded.
    """
    return any(marker in normalized_key for marker in SECRET_MARKERS)


def _normalize_key(key):
    """Normalize a key for safety checks.

    Args:
        key: Required. Payload key.

    Returns:
        Lowercase key with separators normalized.
    """
    return str(key).strip().lower().replace("-", "_")
