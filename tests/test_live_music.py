import os
from decimal import Decimal, InvalidOperation

import pytest

from easy_ai_clients import music
from easy_ai_clients.music._common import env_utils

pytestmark = pytest.mark.live

LIVE_GATE = "EASY_AI_CLIENTS_LIVE_MUSIC"
PAID_CALL_GATE = "EASY_AI_CLIENTS_LIVE_MUSIC_PAID_CALL"
MAX_USD_ENV = "EASY_AI_CLIENTS_LIVE_MUSIC_MAX_USD"
DEFAULT_MAX_USD = Decimal("1.00")
DEFAULT_ESTIMATED_SMOKE_USD = Decimal("0.05")

if os.environ.get(LIVE_GATE) != "1":
    pytest.skip(
        f"Set {LIVE_GATE}=1 to enable gated live music tests.",
        allow_module_level=True,
    )


def _max_usd():
    raw_value = os.environ.get(MAX_USD_ENV, str(DEFAULT_MAX_USD))
    try:
        return Decimal(raw_value)
    except InvalidOperation:
        pytest.fail(f"{MAX_USD_ENV} must be a decimal USD amount.")


def _estimated_smoke_usd():
    raw_value = os.environ.get(
        "EASY_AI_CLIENTS_LIVE_MUSIC_ESTIMATED_USD",
        str(DEFAULT_ESTIMATED_SMOKE_USD),
    )
    try:
        return Decimal(raw_value)
    except InvalidOperation:
        pytest.fail("EASY_AI_CLIENTS_LIVE_MUSIC_ESTIMATED_USD must be a decimal USD amount.")


def _live_provider():
    return os.environ.get("EASY_AI_CLIENTS_LIVE_MUSIC_PROVIDER", "elevenlabs").lower()


def _require_credentials(provider):
    names = env_utils.env_var_names(provider)
    if not names:
        pytest.skip(f"No credential mapping exists for provider '{provider}'.")

    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        pytest.skip(
            "Missing provider credential environment variable(s): "
            + ", ".join(missing)
        )


def _require_paid_call_gate():
    if os.environ.get(PAID_CALL_GATE) != "1":
        pytest.skip(
            f"Set {PAID_CALL_GATE}=1 to allow a paid provider smoke call."
        )


def _require_cost_ceiling():
    ceiling = _max_usd()
    estimated = _estimated_smoke_usd()
    if ceiling < estimated:
        pytest.skip(
            f"{MAX_USD_ENV}={ceiling} is below estimated smoke cost {estimated}."
        )
    return ceiling


def _live_kwargs():
    kwargs = {
        "sync": False,
        "music_length_ms": 10000,
        "duration": 10,
        "duration_seconds": 10,
        "output_format": "mp3",
    }
    model = os.environ.get("EASY_AI_CLIENTS_LIVE_MUSIC_MODEL")
    if model:
        kwargs["model"] = model
    return kwargs


def test_live_music_credentials_are_configured_when_gate_is_enabled():
    provider = _live_provider()

    assert _max_usd() >= Decimal("0")
    _require_credentials(provider)


def test_live_lyrics_to_song_paid_smoke(tmp_path):
    _require_paid_call_gate()
    _require_cost_ceiling()

    provider = _live_provider()
    _require_credentials(provider)
    if provider not in music.available_lyrics_to_song_apis():
        pytest.skip(f"Provider '{provider}' is not available for lyrics_to_song.")

    prompt = os.environ.get(
        "EASY_AI_CLIENTS_LIVE_MUSIC_PROMPT",
        "short simple acoustic test",
    )
    lyrics = os.environ.get(
        "EASY_AI_CLIENTS_LIVE_MUSIC_LYRICS",
        "[Verse]\nThis is a short live smoke test.",
    )

    result = music.lyrics_to_song(
        lyrics,
        prompt=prompt,
        api=provider,
        output_path=str(tmp_path / "live-music.mp3"),
        **_live_kwargs(),
    )

    assert result["provider"] == provider
    assert result["operation"] == "lyrics_to_song"
    assert result["status"] in {"submitted", "completed"}
    assert result["error"] if result["status"] == "failed" else True
