"""Gated live music smoke test.

This module submits a real music generation only when both
`EASY_AI_CLIENTS_LIVE_MUSIC=1` and `EASY_AI_CLIENTS_LIVE_MUSIC_API` are set by
the caller. Normal local validation keeps this gate cleared.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

pytestmark = pytest.mark.live

ROOT = Path(__file__).resolve().parents[1]
LOCAL_ENV_FILE = ROOT.parent / ".env-easy-ai-clients"
LIVE_ENV = "EASY_AI_CLIENTS_LIVE_MUSIC"
API_ENV = "EASY_AI_CLIENTS_LIVE_MUSIC_API"
MODEL_ENV = "EASY_AI_CLIENTS_LIVE_MUSIC_MODEL"
ENV_FILE_ENV = "EASY_AI_CLIENTS_ENV_FILE"

PROVIDER_ENV = {
    "deapi": "DEAPI_API_KEY",
    "elevenlabs": "ELEVENLABS_API_KEY",
    "google": "GOOGLE_API_KEY",
    "runware": "RUNWARE_API_KEY",
}

PROVIDER_DURATION = {
    "deapi": 10,
    "elevenlabs": 3,
    "google": 30,
    "runware": 30,
}

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


def _require_live_enabled():
    if os.getenv(LIVE_ENV) != "1":
        pytest.skip(f"Set {LIVE_ENV}=1 to run a live music smoke test.")


def _load_credentials():
    if os.getenv(ENV_FILE_ENV):
        load_dotenv(os.environ[ENV_FILE_ENV], override=False)
    load_dotenv(LOCAL_ENV_FILE, override=False)


def _selected_api():
    from easy_ai_clients import music

    api = str(os.getenv(API_ENV) or "").strip()
    if not api:
        pytest.skip(f"Set {API_ENV} to one of: {', '.join(music.available_apis())}.")
    if api not in music.available_apis():
        pytest.skip(f"{API_ENV}={api!r} is not supported by easy_ai_clients.music.")
    return api


def _require_env(api):
    env_var = PROVIDER_ENV[api]
    if not os.getenv(env_var):
        pytest.skip(f"{env_var} is not configured for live music smoke tests.")


def test_live_music_generation_smoke():
    from easy_ai_clients import music

    _require_live_enabled()
    _load_credentials()
    api = _selected_api()
    _require_env(api)

    kwargs = {
        "lyrics": "[Verse]\nThe morning opens wide\n[Chorus]\nWe keep the light alive",
        "api": api,
        "prompt": "short hopeful acoustic pop with clear lead vocal",
        "duration": PROVIDER_DURATION[api],
    }
    model = str(os.getenv(MODEL_ENV) or "").strip()
    if model:
        kwargs["model"] = model

    generation = music.generate(**kwargs)

    assert set(generation) == PUBLIC_GENERATION_KEYS
    assert generation["provider"] == api
    assert generation["request_id"]
    assert generation["status"] in {"submitted", "running", "completed"}
    assert "raw_response" not in generation
