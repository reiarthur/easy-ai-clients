"""Cliente de geracao texto->texto para a API da Together AI.

Ultima atualizacao: 2026-04-23
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import requests

from ..post_processing import calcular_custo_tokens, montar_resultado_chat_compativel
from ..pre_processing import (
    listar_modelos_compativeis,
    obter_chave_api,
)
from ._shared import (
    TOGETHER_PARAMETERS,
    build_chat_payload,
    execute_chat_request,
    validate_kwargs,
)

_CACHE_MODELOS = None
_FUTURO_CATALOGO = None
_LOCK_CACHE_MODELOS = Lock()
_EXECUTOR_CATALOGO = ThreadPoolExecutor(max_workers=1)


def generate(
    input_text,
    instruction=None,
    model="google/gemma-3n-E4B-it",
    **kwargs,
):
    """Generate text with Together AI. Full details: text/docs/together.md."""
    validate_kwargs(
        provider="together",
        api="chat/completions",
        model=model,
        kwargs=kwargs,
        supported_parameters=TOGETHER_PARAMETERS,
    )
    _aquecer_catalogo_modelos_async()
    corpo = build_chat_payload(
        input_text=input_text,
        instruction=instruction,
        model=model,
        kwargs=kwargs,
    )
    resposta_json, resposta_http = execute_chat_request(
        env_var="TOGETHER_API_KEY",
        url="https://api.together.xyz/v1/chat/completions",
        payload=corpo,
    )
    return montar_resultado_chat_compativel(
        provider="together",
        model=model,
        input_text=input_text,
        instruction=instruction,
        resposta_json=resposta_json,
        resposta_http=resposta_http,
        resolvedor_custo=_resolver_custo,
    )


def list_models(api_key=None, timeout=180):
    """Lista os modelos expostos pela Together AI."""
    return listar_modelos_compativeis(
        env_var="TOGETHER_API_KEY",
        url_modelos="https://api.together.xyz/v1/models",
        api_key=api_key,
        timeout=timeout,
        transformador=_transformar_modelos,
    )


def _resolver_custo(resultado, resposta_json, resposta_http):
    """Resolve o custo com base na tabela `pricing` do endpoint de modelos."""
    del resposta_json, resposta_http
    custo = _calcular_custo(resultado.get("model"), resultado.get("usage") or {})
    return custo, "usage_x_models_endpoint"


def _calcular_custo(modelo, uso):
    """Calcula custo a partir do preco dinamico retornado pela Together."""
    item = _obter_modelo_catalogo(modelo)
    if not item:
        return 0.0

    pricing = item.get("pricing") or {}
    if pricing.get("input") is None or pricing.get("output") is None:
        return 0.0

    return calcular_custo_tokens(
        uso,
        {
            "input": pricing.get("input"),
            "output": pricing.get("output"),
        },
    )


def _obter_modelo_catalogo(modelo):
    """Retorna o metadata do modelo diretamente do catalogo da Together."""
    return (_carregar_catalogo_modelos().get("por_id") or {}).get(modelo)


def _carregar_catalogo_modelos():
    """Carrega o catalogo de modelos apenas uma vez por processo."""
    global _CACHE_MODELOS, _FUTURO_CATALOGO
    if _CACHE_MODELOS is not None:
        return _CACHE_MODELOS

    with _LOCK_CACHE_MODELOS:
        if _CACHE_MODELOS is not None:
            return _CACHE_MODELOS

        if _FUTURO_CATALOGO is not None:
            try:
                modelos = _FUTURO_CATALOGO.result()
            except Exception:
                modelos = None
            _FUTURO_CATALOGO = None
            if modelos is not None:
                _CACHE_MODELOS = _montar_cache_modelos(modelos)
                return _CACHE_MODELOS

        _CACHE_MODELOS = _montar_cache_modelos(list_models())

    return _CACHE_MODELOS


def _aquecer_catalogo_modelos_async():
    """Inicia o carregamento do catalogo em paralelo quando o cache esta frio."""
    global _FUTURO_CATALOGO
    if _CACHE_MODELOS is not None or _FUTURO_CATALOGO is not None:
        return

    with _LOCK_CACHE_MODELOS:
        if _CACHE_MODELOS is None and _FUTURO_CATALOGO is None:
            _FUTURO_CATALOGO = _EXECUTOR_CATALOGO.submit(
                _buscar_catalogo_modelos_background
            )


def _montar_cache_modelos(modelos):
    """Organiza a lista de modelos em estruturas otimizadas para lookup."""
    return {
        "lista": modelos,
        "por_id": {item.get("id"): item for item in modelos if item.get("id")},
    }


def _buscar_catalogo_modelos_background():
    """Busca o catalogo em sessao dedicada para nao concorrer com o POST."""
    chave = obter_chave_api("TOGETHER_API_KEY")
    with requests.Session() as sessao:
        sessao.headers.update({"User-Agent": "easy-ai-clients-text/1.0"})
        resposta = sessao.get(
            "https://api.together.xyz/v1/models",
            headers={"Authorization": f"Bearer {chave}"},
            timeout=180,
        )
        resposta.raise_for_status()
        return _transformar_modelos(resposta.json())


def _transformar_modelos(resposta_json):
    """Normaliza a listagem de modelos da Together."""
    return resposta_json if isinstance(resposta_json, list) else []
