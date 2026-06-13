"""Music style adapter and preset export tests."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from easy_ai_clients.music import _style_adapter as style_adapter

STYLE_DIR = Path(style_adapter.__file__).resolve().parent / "styles"
TEST_LYRICS = "Minha letra tem mais de dez caracteres para validacao local."

REQUIRED_FIELDS = {
    "id",
    "description",
    "style_family",
    "style_prompt",
    "default_language",
    "default_vocal",
    "tempo_bpm",
    "key_scale",
    "time_signature",
    "duration_seconds",
    "generation_controls",
    "instrumentation",
    "arrangement",
    "energy",
    "mood",
    "mix_target",
    "negative_traits",
}

FORBIDDEN_ARTIST_NAMES = {
    "Adele",
    "Beyonce",
    "Beyoncé",
    "Drake",
    "Taylor Swift",
    "Bad Bunny",
    "Anitta",
    "Queen",
    "The Beatles",
    "Elvis Presley",
}

PROMPT_FACING_FIELDS = (
    "description",
    "style_family",
    "style_prompt",
    "default_vocal",
    "instrumentation",
    "arrangement",
    "energy",
    "mood",
    "mix_target",
    "negative_traits",
)


def test_list_styles_returns_exact_file_stems():
    stems = sorted(path.stem for path in STYLE_DIR.glob("*.py") if path.name != "__init__.py")

    assert style_adapter.list_styles() == stems
    assert len(stems) == 30


def test_resolve_style_uses_exact_matching():
    assert style_adapter.resolve_style("sertanejo")["style_source"] == "preset"
    assert style_adapter.resolve_style("hip_hop_rap_trap")["style_source"] == "preset"
    assert style_adapter.resolve_style(None)["style_source"] == "none"

    with pytest.raises(ValueError, match="Unknown style"):
        style_adapter.resolve_style("Hip Hop Rap Trap")
    with pytest.raises(ValueError, match="Unknown style"):
        style_adapter.resolve_style("hip-hop-rap-trap")


def test_preset_request_contains_stable_prompt_fragments():
    request = style_adapter.build_generation_request(
        provider="deapi",
        model="AceStep_1_5_Turbo",
        lyrics=TEST_LYRICS,
        style="sertanejo",
    )

    assert request["style_source"] == "preset"
    assert "Brazilian sertanejo" in request["kwargs"]["prompt"]
    assert "duet lead vocal" in request["kwargs"]["prompt"]
    assert "Brazilian Portuguese" in request["kwargs"]["prompt"]
    assert "92 BPM" in request["kwargs"]["prompt"]
    assert "E major" in request["kwargs"]["prompt"]
    assert "acoustic guitar" in request["kwargs"]["prompt"]


def test_prompt_kwarg_replaces_preset_prompt():
    request = style_adapter.build_generation_request(
        provider="deapi",
        model="AceStep_1_5_Turbo",
        lyrics=TEST_LYRICS,
        style="sertanejo",
        prompt="extra romantic lift",
    )

    assert request["kwargs"]["prompt"] == "extra romantic lift"
    assert request["kwargs"]["duration"] == 60


def test_caller_kwargs_override_generated_kwargs():
    request = style_adapter.build_generation_request(
        provider="deapi",
        model="AceStep_1_5_Turbo",
        lyrics=TEST_LYRICS,
        style="sertanejo",
        kwargs={"duration": 45, "bpm": 100},
    )

    assert request["kwargs"]["duration"] == 45
    assert request["kwargs"]["bpm"] == 100
    assert request["kwargs"]["key_scale"] == "E major"


def test_language_override_updates_prompt_and_ace_vocal_language():
    request = style_adapter.build_generation_request(
        provider="runware",
        model="runware:ace-step@v1.5-xl-turbo",
        lyrics=TEST_LYRICS,
        style="hip_hop_rap_trap",
        kwargs={"language": "pt-BR"},
    )

    assert "Brazilian Portuguese lyrics" in request["kwargs"]["prompt"]
    assert request["kwargs"]["vocal_language"] == "pt"
    assert "language" not in request["kwargs"]


def test_language_override_is_prompt_only_for_non_ace_providers():
    provider_cases = [
        ("elevenlabs", "music_v1"),
        ("google", "lyria-3-pro-preview"),
    ]

    for provider, model in provider_cases:
        request = style_adapter.build_generation_request(
            provider=provider,
            model=model,
            lyrics=TEST_LYRICS,
            style="rock",
            kwargs={"language": "pt-BR"},
        )

        assert "Brazilian Portuguese lyrics" in request["kwargs"]["prompt"]
        assert "language" not in request["kwargs"]
        assert "vocal_language" not in request["kwargs"]


def test_language_override_rejects_unknown_language():
    with pytest.raises(ValueError, match="language must be one of"):
        style_adapter.build_generation_request(
            provider="runware",
            model="runware:ace-step@v1.5-xl-turbo",
            lyrics=TEST_LYRICS,
            style="rock",
            kwargs={"language": "pt-BR-extra"},
        )


def test_unsupported_negative_prompt_is_preserved_for_wrapper_rejection():
    request = style_adapter.build_generation_request(
        provider="deapi",
        model="AceStep_1_5_Turbo",
        lyrics=TEST_LYRICS,
        style="sertanejo",
        kwargs={"negative_prompt": "avoid noisy mix"},
    )

    assert request["kwargs"]["negative_prompt"] == "avoid noisy mix"
    assert "Negative Prompt:" not in request["kwargs"]["prompt"]


def test_runware_sft_receives_preset_negative_traits():
    request = style_adapter.build_generation_request(
        provider="runware",
        model="runware:ace-step@v1.5-xl-sft",
        lyrics=TEST_LYRICS,
        style="sertanejo",
    )

    assert "weak chorus" in request["kwargs"]["negative_prompt"]
    assert "no duet blend" in request["kwargs"]["negative_prompt"]


def test_runware_xl_turbo_does_not_receive_preset_negative_traits():
    request = style_adapter.build_generation_request(
        provider="runware",
        model="runware:ace-step@v1.5-xl-turbo",
        lyrics=TEST_LYRICS,
        style="sertanejo",
    )

    assert "negative_prompt" not in request["kwargs"]


def test_runware_sft_user_negative_prompt_replaces_preset_negative_traits():
    request = style_adapter.build_generation_request(
        provider="runware",
        model="runware:ace-step@v1.5-xl-sft",
        lyrics=TEST_LYRICS,
        style="sertanejo",
        kwargs={"negative_prompt": "avoid spoken word"},
    )

    assert request["kwargs"]["negative_prompt"] == "avoid spoken word"


def test_runware_sft_null_negative_prompt_disables_preset_negative_traits():
    request = style_adapter.build_generation_request(
        provider="runware",
        model="runware:ace-step@v1.5-xl-sft",
        lyrics=TEST_LYRICS,
        style="sertanejo",
        kwargs={"negative_prompt": None},
    )

    assert "negative_prompt" not in request["kwargs"]


def test_style_none_preserves_prompt_negative_prompt_and_kwargs():
    request = style_adapter.build_generation_request(
        provider="runware",
        model="runware:ace-step@v1.5-xl-sft",
        lyrics=TEST_LYRICS,
        style=None,
        prompt="modern romantic sertanejo",
        kwargs={
            "negative_prompt": "avoid spoken word",
            "duration": 90,
        },
    )

    assert request["style_source"] == "none"
    assert request["kwargs"]["prompt"] == "modern romantic sertanejo"
    assert request["kwargs"]["negative_prompt"] == "avoid spoken word"
    assert request["kwargs"]["duration"] == 90


def test_get_style_presets_returns_full_deep_copied_presets():
    presets = style_adapter.get_style_presets()

    assert len(presets) == 30
    assert "sertanejo" in presets
    assert "description" in presets["sertanejo"]

    presets["sertanejo"]["description"]["en"] = "mutated"
    fresh = style_adapter.get_style_presets(styles="sertanejo")

    assert fresh["sertanejo"]["description"]["en"] != "mutated"


def test_get_style_presets_filters_fields_without_automatic_id():
    presets = style_adapter.get_style_presets(
        fields=["description", "style_family"],
        styles="sertanejo",
    )

    assert list(presets) == ["sertanejo"]
    assert list(presets["sertanejo"]) == ["description", "style_family"]
    assert "id" not in presets["sertanejo"]


def test_get_style_presets_filters_styles_and_fields_in_caller_order():
    presets = style_adapter.get_style_presets(
        fields=["mix_target", "description", "id"],
        styles=["gospel_br", "sertanejo"],
    )

    assert list(presets) == ["gospel_br", "sertanejo"]
    assert list(presets["gospel_br"]) == ["mix_target", "description", "id"]
    assert list(presets["sertanejo"]) == ["mix_target", "description", "id"]


def test_get_style_presets_uses_exact_matching():
    result = style_adapter.get_style_presets(
        fields="Description",
        styles="Sertanejo",
    )

    error = result["error"]
    assert error["invalid_fields"] == ["Description"]
    assert error["invalid_styles"] == ["Sertanejo"]


def test_get_style_presets_reports_invalid_filter_shapes():
    result = style_adapter.get_style_presets(
        fields=["id", 1, ""],
        styles=[],
    )

    error = result["error"]
    assert error["message"] == "Invalid style preset filters."
    assert error["usage"]["fields"] == "Use None, a string field name, or a list of string field names."
    assert "<non-string item: int>" in error["invalid_fields"]
    assert "<empty string>" in error["invalid_fields"]
    assert error["invalid_styles"] == ["<empty list>"]
    assert error["accepted_fields"][:3] == ["id", "description", "style_family"]
    assert error["accepted_styles"] == style_adapter.list_styles()


def test_get_style_presets_reports_invalid_parameter_types():
    result = style_adapter.get_style_presets(
        fields={"id": True},
        styles=object(),
    )

    error = result["error"]
    assert error["invalid_fields"] == ["<invalid type: dict>"]
    assert error["invalid_styles"] == ["<invalid type: object>"]


def test_style_package_has_expected_files():
    files = sorted(path.name for path in STYLE_DIR.glob("*.py"))

    assert len(files) == 31
    assert "__init__.py" in files
    assert len([name for name in files if name != "__init__.py"]) == 30


def test_all_style_modules_import_and_expose_valid_presets():
    for style in style_adapter.list_styles():
        module = importlib.import_module(f"easy_ai_clients.music.styles.{style}")
        assert hasattr(module, "STYLE_PRESET")
        preset = module.STYLE_PRESET

        assert set(preset) == REQUIRED_FIELDS
        assert preset["id"] == style
        assert set(preset["description"]) == {"pt", "en"}
        for language in ("pt", "en"):
            assert isinstance(preset["description"][language], str)
            assert preset["description"][language].strip()
            assert preset["description"][language] == preset["description"][language].strip()
            assert "\n" not in preset["description"][language]
            assert "\r" not in preset["description"][language]
        assert set(preset["default_vocal"]) == {"description"}
        assert "lyrics" not in preset
        assert "seed" not in preset
        assert not _contains_exact_key(preset, "seed")
        assert isinstance(preset["tempo_bpm"], int)
        assert 30 <= preset["tempo_bpm"] <= 300
        assert preset["time_signature"] in {2, 3, 4, 6}
        assert set(preset["generation_controls"]) == {"instrumental"}
        assert isinstance(preset["generation_controls"]["instrumental"], bool)
        assert_prompt_fields_have_no_artist_names(preset)


def assert_prompt_fields_have_no_artist_names(preset):
    prompt_text = " ".join(_flatten(preset[field]) for field in PROMPT_FACING_FIELDS)
    for artist_name in FORBIDDEN_ARTIST_NAMES:
        assert artist_name.lower() not in prompt_text.lower()


def _contains_exact_key(value, target_key):
    if isinstance(value, dict):
        if target_key in value:
            return True
        return any(_contains_exact_key(item, target_key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_exact_key(item, target_key) for item in value)
    return False


def _flatten(value):
    if isinstance(value, dict):
        return " ".join(_flatten(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten(item) for item in value)
    return str(value)

