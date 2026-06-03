from ..._common import cost_utils, env_utils, http_utils, result_utils
from .. import post_processing, pre_processing

PROVIDER = "cloudflare"
ENV_NAME = "CLOUDFLARE_API_TOKEN"
ACCOUNT_ENV_NAME = "CLOUDFLARE_ACCOUNT_ID"
DEFAULT_MODEL = "minimax/music-2.6"
COST_SOURCE = "cloudflare_workers_ai_billing"


def _selected_model(kwargs):
    return pre_processing.selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    input_payload = dict(prepared)
    return pre_processing.compact_payload({
        "model": str(model).removeprefix("@cf/"),
        "input": pre_processing.payload_kwargs(
            input_payload,
            exclude=("model", "model_id"),
        ),
    })


def _cost(model, kwargs):
    return cost_utils.unavailable_cost_metadata(
        source=COST_SOURCE,
        details={
            "model": model,
            "format": kwargs.get("format"),
            "sample_rate": kwargs.get("sample_rate"),
        },
    )


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    options = dict(kwargs)
    model = _selected_model(options)
    prepared = pre_processing.prepared_prompt(prompt, options)
    payload = _build_payload(model, prepared, options)
    cost = _cost(model, payload)

    try:
        response = http_utils.request_json(
            "POST",
            _endpoint(options),
            headers=_headers(),
            json=payload,
            **pre_processing.http_options(options),
        )
        return post_processing.normalize_response(
            PROVIDER,
            model,
            response,
            output_path=output_path,
            cost=cost,
            download_timeout=options.get("download_timeout", 60),
        )
    except Exception as exc:
        return _failure(model, exc, output_path=output_path)


def _headers():
    token = env_utils.require_env_var(ENV_NAME)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _endpoint(kwargs):
    if kwargs.get("endpoint_url"):
        return kwargs["endpoint_url"]
    account_id = env_utils.require_env_var(ACCOUNT_ENV_NAME)
    base_url = kwargs.get("base_url", "https://api.cloudflare.com/client/v4").rstrip("/")
    return f"{base_url}/accounts/{account_id}/ai/run"


def _failure(model, exc, request_id=None, output_path=None):
    return result_utils.failure_result(
        provider=PROVIDER,
        model=model,
        operation="text_to_music",
        exc=exc,
        request_id=request_id,
        output_path=output_path,
    )
