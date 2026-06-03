from ..._common import cost_utils, env_utils, http_utils
from .. import post_processing, pre_processing

PROVIDER = "segmind"
ENV_NAME = "SEGMIND_API_KEY"
DEFAULT_MODEL = "ace-step-music"
COST_SOURCE = "segmind_model_credits"


def _selected_model(kwargs):
    return pre_processing.selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    payload = dict(prepared)
    if _is_ace_step_model(model):
        if "output_seconds" not in payload:
            payload["output_seconds"] = payload.pop("duration", 30)
        return pre_processing.compact_payload(payload)
    return pre_processing.compact_payload(payload)


def _cost(model, kwargs):
    return cost_utils.unavailable_cost_metadata(
        source=COST_SOURCE,
        details={
            "model": model,
            "output_seconds": kwargs.get("output_seconds") or kwargs.get("duration"),
            "steps": kwargs.get("steps"),
        },
    )


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    options = dict(kwargs)
    model = _selected_model(options)
    prompt_key = "genres" if _is_ace_step_model(model) else "prompt"
    prepared = pre_processing.prepared_prompt(prompt, options, prompt_key=prompt_key)
    payload = _build_payload(model, prepared, options)
    cost = _cost(model, payload)

    try:
        key = env_utils.require_env_var(ENV_NAME)
        response = http_utils.request(
            "POST",
            _endpoint(model, options),
            headers={"x-api-key": key},
            json=payload,
            **pre_processing.http_options(options),
        )
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type.lower():
            raw_response = http_utils.response_json(response)
            return post_processing.normalize_response(
                PROVIDER,
                model,
                raw_response,
                output_path=output_path,
                cost=cost,
                download_timeout=options.get("download_timeout", 60),
            )

        return post_processing.normalize_response(
            PROVIDER,
            model,
            {"status": "completed"},
            output_path=output_path,
            cost=cost,
            audio=response.content,
            download_timeout=options.get("download_timeout", 60),
        )
    except Exception as exc:
        return _failure(model, exc, output_path=output_path)


def _endpoint(model, kwargs):
    endpoint_url = kwargs.get("endpoint_url")
    if endpoint_url:
        return endpoint_url

    model_path = str(model).strip("/")
    if not model_path.startswith("v1/"):
        model_path = f"v1/{model_path}"
    return f"{kwargs.get('base_url', 'https://api.segmind.com').rstrip('/')}/{model_path}"


def _is_ace_step_model(model):
    return "ace" in str(model).lower()


def _failure(model, exc, output_path=None):
    return post_processing.result_utils.failure_result(
        provider=PROVIDER,
        model=model,
        operation="text_to_music",
        exc=exc,
        output_path=output_path,
    )
