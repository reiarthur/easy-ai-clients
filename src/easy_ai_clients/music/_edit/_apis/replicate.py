import os

from ..._common import operation_utils as _ops

PROVIDER = "replicate"
ENV_NAME = "REPLICATE_API_TOKEN"
DEFAULT_MODEL = None


def edit_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Run a Replicate-hosted music edit model.

    Args:
        audio: Required. Source audio or melody/reference input.
        prompt: Optional. Edit or continuation prompt.
        output_path: Optional. Destination path for a final URL.
        sync: Optional. Use synchronous `replicate.run` when true.
        **kwargs: Optional. Provider-native model input fields.

    Returns:
        A normalized music result.
    """
    token = _token()
    model = _model(kwargs)
    payload = _build_payload(audio, prompt=prompt, **kwargs)
    raw_response = _run_replicate(model, payload, token, sync=sync, **kwargs)
    return _ops.result(
        PROVIDER,
        model,
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response, payload),
        metadata=_ops.provider_metadata(
            raw_response,
            audio,
            extra={"edit_flow": "replicate_model", "model": model},
        ),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get Replicate prediction status.

    Args:
        request_id: Required. Replicate prediction ID.
        **kwargs: Optional. Client controls.

    Returns:
        A normalized music result.
    """
    raw_response = _client().predictions.get(request_id)
    return _ops.result(PROVIDER, _ops.resolve_model(kwargs), raw_response, cost=_cost(raw_response))


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get Replicate prediction result.

    Args:
        request_id: Required. Replicate prediction ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Client controls.

    Returns:
        A normalized music result.
    """
    raw_response = _client().predictions.get(request_id)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs),
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download a completed Replicate prediction output.

    Args:
        request_id: Required. Replicate prediction ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Client controls.

    Returns:
        A normalized music result.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, prompt=None, **kwargs):
    """Build the Replicate model input.

    Args:
        audio: Required. Source audio.
        prompt: Optional. Edit prompt.
        **kwargs: Optional. Provider-native model fields.

    Returns:
        A model input dictionary.
    """
    payload = _ops.forwarded_payload(
        kwargs,
        exclude=("model", "model_id", "version", "webhook"),
    )
    _ops.add_prompt(payload, prompt)
    _ops.add_audio_input(payload, audio, url_key="input_audio", generic_key="audio")
    return payload


def _run_replicate(model, payload, token, sync=True, **kwargs):
    """Run Replicate with the Python client.

    Args:
        model: Required. Replicate model identifier.
        payload: Required. Model input.
        token: Required. Replicate API token.
        sync: Optional. Whether to block for output.
        **kwargs: Optional. Prediction controls.

    Returns:
        Raw Replicate output or prediction object.
    """
    if sync and model:
        try:
            import replicate
        except ImportError as exc:
            raise RuntimeError("The 'replicate' package is required for Replicate.") from exc
        os.environ.setdefault("REPLICATE_API_TOKEN", token)
        return replicate.run(model, input=payload)

    version = kwargs.get("version")
    if not version:
        raise RuntimeError("version is required for asynchronous Replicate predictions.")

    prediction_kwargs = {"version": version, "input": payload}
    if kwargs.get("webhook"):
        prediction_kwargs["webhook"] = kwargs["webhook"]
    return _client(token).predictions.create(**prediction_kwargs)


def _client(token=None):
    """Return the Replicate Python client.

    Args:
        token: Optional. Replicate API token.

    Returns:
        A Replicate client.
    """
    try:
        import replicate
    except ImportError as exc:
        raise RuntimeError("The 'replicate' package is required for Replicate.") from exc
    return replicate.Client(api_token=token or _token())


def _token():
    """Return the Replicate token from the environment.

    Returns:
        The API token.
    """
    return _ops.env_utils.require_env_var(ENV_NAME)


def _model(kwargs):
    """Return the Replicate model identifier.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        A model identifier.
    """
    model = kwargs.get("model") or kwargs.get("model_id") or DEFAULT_MODEL
    if not model and not kwargs.get("version"):
        raise RuntimeError("model, model_id, or version is required for Replicate.")
    return model


def _cost(raw_response=None, payload=None):
    """Return Replicate cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "Replicate cost is model-specific unless output count pricing is known."}
    )
