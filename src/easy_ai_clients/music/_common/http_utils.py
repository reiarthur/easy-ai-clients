import time

from ..._error_utils import error_message

TRANSIENT_STATUS_CODES = (408, 425, 429, 500, 502, 503, 504)


def _requests():
    """Import requests lazily so importing the package has no network setup.

    Returns:
        The imported requests module.
    """
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("The 'requests' package is required for HTTP provider calls.") from exc
    return requests


def response_json(response):
    """Return JSON from a response, or raise a clear error.

    Args:
        response: Required. requests response object.

    Returns:
        Parsed JSON content.

    Raises:
        RuntimeError: If the response body is not valid JSON.
    """
    try:
        return response.json()
    except ValueError as exc:
        text = getattr(response, "text", "")
        if len(text) > 500:
            text = text[:500] + "..."
        text = error_message(RuntimeError(text))
        raise RuntimeError(f"Response did not contain valid JSON: {text}") from exc


def request_json(method, url, headers=None, params=None, json=None, data=None, timeout=60,
                 retries=2, transient_status_codes=None, **kwargs):
    """Send a JSON-style HTTP request with basic retry behavior.

    Args:
        method: Required. HTTP method.
        url: Required. Request URL.
        headers: Optional. Request headers.
        params: Optional. Query parameters.
        json: Optional. JSON request body.
        data: Optional. Form request body.
        timeout: Optional. Request timeout in seconds. Defaults to 60.
        retries: Optional. Number of retries for transient status codes.
            Defaults to 2.
        transient_status_codes: Optional. Status codes that should be retried.
        **kwargs: Optional. Extra arguments passed to requests.

    Returns:
        Parsed JSON response.
    """
    response = request(
        method,
        url,
        headers=headers,
        params=params,
        json=json,
        data=data,
        timeout=timeout,
        retries=retries,
        transient_status_codes=transient_status_codes,
        **kwargs,
    )
    return response_json(response)


def multipart_request(method, url, files, headers=None, data=None, timeout=60,
                      retries=2, transient_status_codes=None, **kwargs):
    """Send a multipart HTTP request with basic retry behavior.

    Args:
        method: Required. HTTP method.
        url: Required. Request URL.
        files: Required. Multipart files mapping for requests.
        headers: Optional. Request headers.
        data: Optional. Form fields.
        timeout: Optional. Request timeout in seconds. Defaults to 60.
        retries: Optional. Number of retries for transient status codes.
            Defaults to 2.
        transient_status_codes: Optional. Status codes that should be retried.
        **kwargs: Optional. Extra arguments passed to requests.

    Returns:
        The requests response object.
    """
    return request(
        method,
        url,
        headers=headers,
        data=data,
        files=files,
        timeout=timeout,
        retries=retries,
        transient_status_codes=transient_status_codes,
        **kwargs,
    )


def request(method, url, headers=None, timeout=60, retries=2,
            transient_status_codes=None, **kwargs):
    """Send an HTTP request and raise for non-success responses.

    Args:
        method: Required. HTTP method.
        url: Required. Request URL.
        headers: Optional. Request headers.
        timeout: Optional. Request timeout in seconds. Defaults to 60.
        retries: Optional. Number of retries for transient status codes.
            Defaults to 2.
        transient_status_codes: Optional. Status codes that should be retried.
        **kwargs: Optional. Extra arguments passed to requests.

    Returns:
        The requests response object.
    """
    requests = _requests()
    transient_status_codes = transient_status_codes or TRANSIENT_STATUS_CODES
    attempts = retries + 1

    for attempt in range(attempts):
        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
        if response.status_code not in transient_status_codes or attempt == attempts - 1:
            response.raise_for_status()
            return response
        time.sleep(min(2 ** attempt, 8))

    return response
