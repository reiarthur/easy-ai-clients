"""Read-only music generation option catalog tests."""

from __future__ import annotations

from unittest.mock import Mock

REMOVED_PUBLIC_PARAMETERS = {
    "seed",
    "output_format",
    "output_type",
    "include_cost",
    "number_results",
    "audio_settings",
    "ttl",
}


def test_full_catalog_contains_all_models_and_shared_keys():
    from easy_ai_clients import music

    catalog = music.get_generation_options()

    assert "ace_step_1_5_xl_turbo_int8" in catalog
    assert "eleven_music" in catalog
    assert "lyria_3_clip_preview" in catalog
    assert "ace_step_v1_5_xl_sft" in catalog
    assert "duration" in catalog["ace_step_v1_5_turbo"]["deapi"]
    assert "language" in catalog["ace_step_v1_5_turbo"]["deapi"]


def test_language_option_is_documented_as_style_adapter_control():
    from easy_ai_clients import music

    catalog = music.get_generation_options()

    for model_key, api_options in catalog.items():
        for api, parameters in api_options.items():
            language = parameters["language"]
            assert language["provider_field"] == "easy_ai_clients.music._style_adapter"
            assert "pt-BR" in language["accepted_values"], (model_key, api)


def test_filter_by_api():
    from easy_ai_clients import music

    catalog = music.get_generation_options(api="runware")

    assert list(catalog) == [
        "ace_step_v1_5_turbo",
        "ace_step_v1_5_xl_base",
        "ace_step_v1_5_xl_sft",
        "ace_step_v1_5_xl_turbo",
    ]
    for model_options in catalog.values():
        assert list(model_options) == ["runware"]


def test_filter_by_model():
    from easy_ai_clients import music

    catalog = music.get_generation_options(model="ace_step_1_5_xl_turbo_int8")

    assert list(catalog) == ["ace_step_1_5_xl_turbo_int8"]
    assert list(catalog["ace_step_1_5_xl_turbo_int8"]) == ["deapi"]


def test_filter_by_api_and_model():
    from easy_ai_clients import music

    catalog = music.get_generation_options(api="runware", model="ace_step_v1_5_xl_sft")

    assert list(catalog) == ["ace_step_v1_5_xl_sft"]
    assert list(catalog["ace_step_v1_5_xl_sft"]) == ["runware"]
    assert "negative_prompt" in catalog["ace_step_v1_5_xl_sft"]["runware"]


def test_summary_mode():
    from easy_ai_clients import music

    summary = music.get_generation_options(api=True, model=True)

    assert summary == {
        "models": [
            "ace_step_v1_5_turbo",
            "ace_step_1_5_xl_turbo_int8",
            "eleven_music",
            "lyria_3_clip_preview",
            "lyria_3_pro_preview",
            "ace_step_v1_5_xl_base",
            "ace_step_v1_5_xl_sft",
            "ace_step_v1_5_xl_turbo",
        ],
        "apis": ["deapi", "elevenlabs", "google", "runware"],
        "model_apis": {
            "ace_step_v1_5_turbo": ["deapi", "runware"],
            "ace_step_1_5_xl_turbo_int8": ["deapi"],
            "eleven_music": ["elevenlabs"],
            "lyria_3_clip_preview": ["google"],
            "lyria_3_pro_preview": ["google"],
            "ace_step_v1_5_xl_base": ["runware"],
            "ace_step_v1_5_xl_sft": ["runware"],
            "ace_step_v1_5_xl_turbo": ["runware"],
        },
        "default_models": {
            "deapi": "ace_step_v1_5_turbo",
            "elevenlabs": "eleven_music",
            "google": "lyria_3_clip_preview",
            "runware": "ace_step_v1_5_xl_turbo",
        },
    }


def test_invalid_filters_return_summary():
    from easy_ai_clients import music

    summary = music.get_generation_options(api=True, model=True)

    assert music.get_generation_options(api="unknown") == summary
    assert music.get_generation_options(model="unknown") == summary
    assert music.get_generation_options(model="music_v1") == summary
    assert (
        music.get_generation_options(api="google", model="ace_step_v1_5_turbo")
        == summary
    )


def test_google_duration_is_accepted_but_ignored():
    from easy_ai_clients import music

    catalog = music.get_generation_options(api="google")

    for model_options in catalog.values():
        duration = model_options["google"]["duration"]
        assert "ignored" in duration["accepted_values"]
        assert duration["provider_field"] == "Not sent"


def test_negative_prompt_only_appears_for_runware_xl_sft():
    from easy_ai_clients import music

    catalog = music.get_generation_options()

    for model_key, api_options in catalog.items():
        for api, parameters in api_options.items():
            has_negative_prompt = "negative_prompt" in parameters
            assert has_negative_prompt == (
                api == "runware" and model_key == "ace_step_v1_5_xl_sft"
            )


def test_internal_and_removed_parameters_do_not_appear():
    from easy_ai_clients import music

    catalog = music.get_generation_options()
    catalog_text = repr(catalog)

    for api_options in catalog.values():
        for parameters in api_options.values():
            assert "_force_instrumental" not in parameters
            assert REMOVED_PUBLIC_PARAMETERS.isdisjoint(parameters)
    assert "_force_instrumental" not in catalog_text
    for parameter in REMOVED_PUBLIC_PARAMETERS:
        assert parameter not in catalog_text


def test_helper_does_not_import_provider_modules(monkeypatch):
    from easy_ai_clients import music
    from easy_ai_clients.music import _router

    import_module = Mock(side_effect=AssertionError("provider import attempted"))

    monkeypatch.setattr(_router.importlib, "import_module", import_module)
    catalog = music.get_generation_options()

    assert "ace_step_v1_5_turbo" in catalog
    import_module.assert_not_called()
