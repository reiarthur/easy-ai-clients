"""Cliente de geracao texto->texto para o roteador OpenRouter via fal.ai.

Ultima atualizacao: 2026-04-23
"""

from ..post_processing import (
    calcular_custo_catalogo_por_token,
    montar_resultado_chat_compativel,
)
from ..pre_processing import (
    listar_modelos_compativeis,
)
from ._shared import (
    FAL_PARAMETERS,
    build_chat_payload,
    execute_chat_request,
    validate_kwargs,
)

_CACHE_MODELOS = None


def generate(
    input_text,
    instruction=None,
    model="google/gemini-2.5-flash",
    **kwargs,
):
    """Generate text through fal.ai. Full details: text/docs/fal.md."""
    validate_kwargs(
        provider="fal",
        api="openrouter/router/openai/v1/chat/completions",
        model=model,
        kwargs=kwargs,
        supported_parameters=FAL_PARAMETERS,
    )
    corpo = build_chat_payload(
        input_text=input_text,
        instruction=instruction,
        model=model,
        kwargs=kwargs,
    )
    if "usage" not in corpo:
        corpo["usage"] = {"include": True}

    resposta_json, resposta_http = execute_chat_request(
        env_var="FAL_KEY",
        url="https://fal.run/openrouter/router/openai/v1/chat/completions",
        payload=corpo,
        auth_header="Authorization",
        auth_prefix="Key ",
    )
    return montar_resultado_chat_compativel(
        provider="fal",
        model=model,
        input_text=input_text,
        instruction=instruction,
        resposta_json=resposta_json,
        resposta_http=resposta_http,
        resolvedor_custo=_resolver_custo,
    )


def list_models():
    """Retorna o catalogo upstream da OpenRouter usado pela fal.ai."""
    return listar_modelos_compativeis(
        env_var="OPENROUTER_API_KEY",
        url_modelos="https://openrouter.ai/api/v1/models",
        transformador=_transformar_modelos,
    )


def _resolver_custo(resultado, resposta_json, resposta_http):
    """Resolve o custo imediato quando a resposta incluir usage accounting."""
    del resposta_json, resposta_http
    uso = resultado.get("usage") or {}
    provider_cost = uso.get("provider_cost")
    if provider_cost is not None:
        return float(provider_cost), "usage_immediate"

    custo = _calcular_custo_catalogo(resultado.get("model"), uso)
    return custo, "usage_x_openrouter_catalog"


def _calcular_custo_catalogo(modelo, uso):
    """Calcula custo com base no catalogo upstream da OpenRouter."""
    item = _obter_modelo_catalogo(modelo)
    if not item:
        return 0.0

    return calcular_custo_catalogo_por_token(uso, item.get("pricing") or {})


def _obter_modelo_catalogo(modelo):
    """Retorna o item correspondente ao modelo no catalogo upstream."""
    return (_carregar_catalogo_modelos().get("por_id") or {}).get(modelo)


def _carregar_catalogo_modelos():
    """Carrega o catalogo apenas uma vez por processo."""
    global _CACHE_MODELOS
    if _CACHE_MODELOS is None:
        _CACHE_MODELOS = _montar_cache_modelos(list_models())
    return _CACHE_MODELOS


def _montar_cache_modelos(modelos):
    """Organiza o catalogo upstream em lookup rapido por `id`."""
    return {
        "lista": modelos,
        "por_id": {item.get("id"): item for item in modelos if item.get("id")},
    }


def _transformar_modelos(resposta_json):
    """Normaliza a listagem retornada pelo endpoint `/models`."""
    return resposta_json.get("data") or []
