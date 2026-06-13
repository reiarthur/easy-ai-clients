"""Music provider contract tests without live provider calls."""

from __future__ import annotations

import inspect
import os
import time

import pytest

PUBLIC_GENERATION_KEYS = {
    "provider",
    "model",
    "model_key",
    "status",
    "request_id",
    "output_path",
    "cost_usd",
    "cost_currency",
    "cost_source",
    "cost_is_estimated",
    "cost_details",
    "metadata",
}


@pytest.fixture(autouse=True)
def block_requests_network(monkeypatch):
    import requests

    def blocked(*args, **kwargs):
        raise AssertionError("network calls are disabled in music unit tests")

    monkeypatch.setattr(requests, "request", blocked)
    monkeypatch.setattr(requests, "get", blocked)
    monkeypatch.setattr(requests, "post", blocked)


def test_active_provider_and_model_matrix_is_explicit():
    from easy_ai_clients.music._apis import deapi, elevenlabs, google, runware
    from easy_ai_clients.music._model_registry import PROVIDERS

    assert PROVIDERS == ("deapi", "elevenlabs", "google", "runware")
    assert set(deapi.MODELS) == {"AceStep_1_5_Turbo", "AceStep_1_5_XL_Turbo_INT8"}
    assert set(elevenlabs.MODELS) == {"music_v1"}
    assert set(google.MODELS) == {"lyria-3-clip-preview", "lyria-3-pro-preview"}
    assert set(runware.MODELS) == {
        "runware:ace-step@v1.5-turbo",
        "runware:ace-step@v1.5-xl-base",
        "runware:ace-step@v1.5-xl-turbo",
        "runware:ace-step@v1.5-xl-sft",
    }


def test_provider_generate_signatures_use_kwargs_contract():
    import importlib

    from easy_ai_clients.music._model_registry import PROVIDERS

    for provider in PROVIDERS:
        module = importlib.import_module(f"easy_ai_clients.music._apis.{provider}")
        signature = inspect.signature(module.generate)

        assert "lyrics" in signature.parameters
        assert "model" in signature.parameters
        assert "kwargs" in signature.parameters
        assert "prompt" not in signature.parameters
        assert "negative_prompt" not in signature.parameters
        assert signature.parameters["kwargs"].kind == inspect.Parameter.VAR_KEYWORD


def test_standard_generation_uses_public_schema():
    from easy_ai_clients.music._common import standard_generation

    generation = standard_generation(
        provider="runware",
        model="runware:ace-step@v1.5-xl-turbo",
        request_id="req_123",
    )

    assert set(generation) == PUBLIC_GENERATION_KEYS
    assert generation["model_key"] == "ace_step_v1_5_xl_turbo"
    assert generation["output_path"] is None
    assert generation["cost_usd"] == 0.0
    assert generation["cost_currency"] == "USD"
    assert generation["cost_source"] == "unavailable"
    assert generation["cost_is_estimated"] is False
    assert generation["cost_details"] == {}
    assert generation["metadata"] == {}


def test_wrappers_reject_removed_public_parameters_before_network():
    from easy_ai_clients.music._apis import deapi, elevenlabs, google, runware

    cases = [
        (deapi, {"output_format": "mp3"}, "Unsupported kwargs"),
        (deapi, {"seed": -1}, "Unsupported kwargs"),
        (elevenlabs, {"output_format": "mp3_44100_128"}, "Unsupported kwargs"),
        (google, {"output_format": "mp3"}, "Unsupported kwargs"),
        (runware, {"output_type": "URL"}, "Unsupported kwargs"),
        (runware, {"include_cost": True}, "Unsupported kwargs"),
        (runware, {"seed": 12345}, "Unsupported kwargs"),
        (deapi, {"negative_prompt": None}, "not supported"),
        (elevenlabs, {"negative_prompt": None}, "not supported"),
        (google, {"negative_prompt": None}, "not supported"),
        (runware, {"negative_prompt": None}, "not supported"),
    ]

    for module, extra, pattern in cases:
        with pytest.raises(ValueError, match=pattern):
            module.generate(
                lyrics="Minha letra tem mais de dez caracteres.",
                prompt="Brazilian gospel with expressive vocal.",
                **extra,
            )


def test_runware_sft_accepts_negative_prompt_in_payload(monkeypatch):
    from easy_ai_clients.music._apis import runware

    captured = {}

    def fake_request_json(method, url, headers=None, json_payload=None, timeout=None):
        captured["payload"] = json_payload[0]
        return {"data": [{"taskUUID": "task-1", "status": "submitted"}]}

    monkeypatch.setattr(runware, "_headers", lambda: {"Authorization": "Bearer fake"})
    monkeypatch.setattr(runware, "request_json", fake_request_json)

    result = runware.generate(
        lyrics="Minha letra tem mais de dez caracteres.",
        model="runware:ace-step@v1.5-xl-sft",
        prompt="Brazilian gospel with expressive vocal.",
        negative_prompt="avoid spoken word",
    )

    assert result["status"] == "submitted"
    assert captured["payload"]["negativePrompt"] == "avoid spoken word"
    assert captured["payload"]["model"] == "runware:ace-step@v1.5-xl-sft"


def test_model_registry_resolves_standard_keys_and_defaults():
    from easy_ai_clients.music._model_registry import resolve_model

    cases = [
        ("deapi", "ace_step_v1_5_turbo", "AceStep_1_5_Turbo"),
        ("deapi", "ace_step_1_5_xl_turbo_int8", "AceStep_1_5_XL_Turbo_INT8"),
        ("elevenlabs", "eleven_music", "music_v1"),
        ("google", "lyria_3_clip_preview", "lyria-3-clip-preview"),
        ("google", "lyria_3_pro_preview", "lyria-3-pro-preview"),
        ("runware", "ace_step_v1_5_turbo", "runware:ace-step@v1.5-turbo"),
        ("runware", "ace_step_v1_5_xl_base", "runware:ace-step@v1.5-xl-base"),
        ("runware", "ace_step_v1_5_xl_sft", "runware:ace-step@v1.5-xl-sft"),
        ("runware", "ace_step_v1_5_xl_turbo", "runware:ace-step@v1.5-xl-turbo"),
    ]

    for provider, model_key, native_model in cases:
        assert resolve_model(provider, model_key) == (native_model, model_key)
        assert resolve_model(provider, native_model) == (native_model, model_key)

    assert resolve_model("deapi", None) == ("AceStep_1_5_Turbo", "ace_step_v1_5_turbo")
    assert resolve_model("elevenlabs", None) == ("music_v1", "eleven_music")
    assert resolve_model("google", None) == (
        "lyria-3-clip-preview",
        "lyria_3_clip_preview",
    )
    assert resolve_model("runware", None) == (
        "runware:ace-step@v1.5-xl-turbo",
        "ace_step_v1_5_xl_turbo",
    )


def test_local_job_helpers_update_and_clear_completed_jobs(tmp_path, monkeypatch):
    from easy_ai_clients.music._common import (
        complete_local_job_generation,
        get_local_job,
        start_local_job,
        update_local_job_generation,
    )

    monkeypatch.chdir(tmp_path)

    def worker(output_path):
        return None

    generation = start_local_job("google", "lyria-3-clip-preview", worker)
    _wait_for_local_status(generation["request_id"], "completed")

    update_local_job_generation(generation)
    assert generation["status"] == "completed"
    assert generation["output_path"].endswith(".mp3")
    assert str(tmp_path / "outputs" / "music" / "temp") in generation["output_path"]

    complete_local_job_generation(generation)
    with pytest.raises(KeyError):
        get_local_job(generation["request_id"])


def test_common_http_error_formatting_redacts_env_secret(monkeypatch):
    from easy_ai_clients.music._common import format_response_error

    monkeypatch.setenv("MUSIC_TEST_API_KEY", "secret-token")

    class Response:
        status_code = 500
        url = "https://example.test/music"
        text = ""

        def json(self):
            return {"error": "Authorization failed for secret-token"}

    message = format_response_error(Response())

    assert "HTTP 500 from https://example.test/music" in message
    assert "secret-token" not in message
    assert "<redacted>" in message


def test_common_http_error_formatting_redacts_url_query():
    from easy_ai_clients.music._common import format_response_error

    class Response:
        status_code = 500
        url = "https://example.test/music?token=query-secret"
        text = ""

        def json(self):
            return {
                "audio_url": "https://example.test/audio.mp3?signature=signed-secret",
            }

    message = format_response_error(Response())

    assert "https://example.test/music?<redacted>" in message
    assert "query-secret" not in message
    assert "signed-secret" not in message
    assert "<redacted-url>" in message


def test_runware_provider_error_message_is_sanitized(monkeypatch):
    from easy_ai_clients.music._apis import runware

    def fake_request_json(method, url, headers=None, json_payload=None, timeout=None):
        return {
            "errors": [
                {
                    "status": "error",
                    "message": (
                        "failed for secret-token at "
                        "https://example.test/audio.mp3?token=query-secret"
                    ),
                }
            ]
        }

    monkeypatch.setenv("RUNWARE_API_KEY", "secret-token")
    monkeypatch.setattr(runware, "_headers", lambda: {"Authorization": "Bearer secret-token"})
    monkeypatch.setattr(runware, "request_json", fake_request_json)

    with pytest.raises(RuntimeError) as exc_info:
        runware.generate(
            lyrics="Minha letra tem mais de dez caracteres.",
            prompt="Brazilian gospel with expressive vocal.",
        )

    message = str(exc_info.value)
    assert "secret-token" not in message
    assert "query-secret" not in message
    assert "https://example.test/audio.mp3" not in message
    assert "<redacted-url>" in message


def test_load_env_preserves_existing_environment(monkeypatch, tmp_path):
    from easy_ai_clients.music._common import load_env

    env_path = tmp_path / ".env"
    env_path.write_text(
        "DEAPI_API_KEY=file-value\nRUNWARE_API_KEY=runware-file-value\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DEAPI_API_KEY", "process-value")
    monkeypatch.delenv("RUNWARE_API_KEY", raising=False)

    loaded = load_env(env_path)

    assert loaded == {"DEAPI_API_KEY", "RUNWARE_API_KEY"}
    assert os.environ["DEAPI_API_KEY"] == "process-value"
    assert os.environ["RUNWARE_API_KEY"] == "runware-file-value"


def test_music_api_timeout_uses_process_env_over_dotenv(monkeypatch, tmp_path):
    from easy_ai_clients.music._common import api_timeout

    env_path = tmp_path / ".env"
    env_path.write_text("MUSIC_API_TIMEOUT=17\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MUSIC_API_TIMEOUT", raising=False)

    assert api_timeout(120) == 17

    monkeypatch.setenv("MUSIC_API_TIMEOUT", "23")

    assert api_timeout(120) == 23


def test_music_api_timeout_rejects_invalid_values(monkeypatch):
    from easy_ai_clients.music._common import api_timeout

    monkeypatch.setenv("MUSIC_API_TIMEOUT", "not-a-number")

    with pytest.raises(ValueError, match="MUSIC_API_TIMEOUT must be a positive integer"):
        api_timeout()


def test_deapi_price_lookup_uses_short_bounded_timeout(monkeypatch):
    from easy_ai_clients.music._apis import deapi

    captured = {}

    def fake_request_json(method, url, headers=None, json_payload=None, timeout=None):
        captured["timeout"] = timeout
        return {"cost": 0.01}

    monkeypatch.setenv("MUSIC_API_TIMEOUT", "120")
    monkeypatch.setattr(deapi, "_headers", lambda: {"Authorization": "Bearer fake"})
    monkeypatch.setattr(deapi, "request_json", fake_request_json)

    assert deapi._calculate_cost(  # noqa: SLF001
        {
            "model": "AceStep_1_5_Turbo",
            "duration": 60,
            "inference_steps": 8,
        }
    ) == 0.01
    assert captured["timeout"] == 15


def _wait_for_local_status(request_id, expected_status):
    from easy_ai_clients.music._common import get_local_job

    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if get_local_job(request_id)["status"] == expected_status:
            return
        time.sleep(0.01)
    raise AssertionError(f"local job did not reach status {expected_status}")
