"""Cliente de geracao texto->texto para o router da Hugging Face.

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
    HUGGINGFACE_PARAMETERS,
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
    model="Qwen/Qwen3-4B-Instruct-2507",
    **kwargs,
):
    """Generate text through the Hugging Face router. Full details: text/docs/huggingface.md."""
    validate_kwargs(
        provider="huggingface",
        api="chat/completions",
        model=model,
        kwargs=kwargs,
        supported_parameters=HUGGINGFACE_PARAMETERS,
    )
    _aquecer_catalogo_modelos_async()
    corpo = build_chat_payload(
        input_text=input_text,
        instruction=instruction,
        model=model,
        kwargs=kwargs,
    )
    resposta_json, resposta_http = execute_chat_request(
        env_var="HUGGINGFACE_API_KEY",
        url="https://router.huggingface.co/v1/chat/completions",
        payload=corpo,
    )
    return montar_resultado_chat_compativel(
        provider="huggingface",
        model=model,
        input_text=input_text,
        instruction=instruction,
        resposta_json=resposta_json,
        resposta_http=resposta_http,
        resolvedor_custo=_resolver_custo,
    )


def list_models(api_key=None, timeout=180):
    """Lista o catalogo live do router da Hugging Face."""
    return listar_modelos_compativeis(
        env_var="HUGGINGFACE_API_KEY",
        url_modelos="https://router.huggingface.co/v1/models",
        api_key=api_key,
        timeout=timeout,
        transformador=_transformar_modelos,
    )


def _resolver_custo(resultado, resposta_json, resposta_http):
    """Resolve o custo com base em `providers[].pricing` do catalogo."""
    del resposta_json, resposta_http
    custo = _calcular_custo(
        modelo=resultado.get("model"),
        uso=resultado.get("usage") or {},
    )
    return custo, "usage_x_models_endpoint"


def _calcular_custo(modelo, uso):
    """Calcula custo a partir do modelo, provider efetivo e tokens usados."""
    item = _obter_modelo_catalogo(modelo)
    if not item:
        return 0.0

    provider = _resolver_provider(item, modelo, uso)
    pricing = _obter_pricing_provider(item, provider)
    if not pricing:
        return 0.0

    return calcular_custo_tokens(
        uso,
        {
            "input": pricing.get("input"),
            "output": pricing.get("output"),
        },
    )


def _obter_modelo_catalogo(modelo):
    """Retorna os metadados do modelo base no catalogo live."""
    modelo_base = _extrair_modelo_base(modelo)
    return (_carregar_catalogo_modelos().get("por_id") or {}).get(modelo_base)


def _resolver_provider(item, modelo, uso):
    """Resolve o provider efetivo usado no roteamento."""
    provider_header = (uso or {}).get("provider_header")
    if provider_header:
        return provider_header

    modelo = modelo or ""
    if ":" in modelo:
        sufixo = modelo.rsplit(":", 1)[1]
        if sufixo != "cheapest":
            return sufixo

    providers = item.get("_providers_com_preco") or []
    if not providers:
        return None

    return item.get("_provider_mais_barato")


def _obter_pricing_provider(item, provider_nome):
    """Retorna a estrutura `pricing` do provider escolhido."""
    provider = (item.get("_providers_por_nome") or {}).get(provider_nome) or {}
    return provider.get("pricing") or None


def _extrair_modelo_base(modelo):
    """Remove o sufixo `:<provider>` do modelo quando houver."""
    if ":" not in (modelo or ""):
        return modelo
    return modelo.rsplit(":", 1)[0]


def _carregar_catalogo_modelos():
    """Carrega o catalogo da Hugging Face apenas uma vez por processo."""
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
    """Organiza o catalogo para lookup rapido por modelo e provider."""
    itens = [_enriquecer_modelo(item) for item in modelos]
    return {
        "lista": itens,
        "por_id": {item.get("id"): item for item in itens if item.get("id")},
    }


def _enriquecer_modelo(item):
    """Preprocessa os providers do item para reduzir scans repetidos."""
    providers_por_nome = {}
    providers_com_preco = []

    for provider in item.get("providers") or []:
        provider_nome = provider.get("provider")
        if not provider_nome:
            continue

        provider_copiado = dict(provider)
        providers_por_nome[provider_nome] = provider_copiado
        if provider_copiado.get("pricing"):
            providers_com_preco.append(provider_copiado)

    item_enriquecido = dict(item)
    item_enriquecido["_providers_por_nome"] = providers_por_nome
    item_enriquecido["_providers_com_preco"] = providers_com_preco
    item_enriquecido["_provider_mais_barato"] = _resolver_provider_mais_barato(
        providers_com_preco
    )
    return item_enriquecido


def _resolver_provider_mais_barato(providers):
    """Resolve o provider com menor custo conhecido no catalogo."""
    if not providers:
        return None

    provider_mais_barato = min(
        providers,
        key=lambda provider: (
            _preco_catalogo_para_float((provider.get("pricing") or {}).get("output")),
            _preco_catalogo_para_float((provider.get("pricing") or {}).get("input")),
        ),
    )
    return provider_mais_barato.get("provider")


def _buscar_catalogo_modelos_background():
    """Busca o catalogo em sessao dedicada para nao concorrer com o POST."""
    chave = obter_chave_api("HUGGINGFACE_API_KEY")
    with requests.Session() as sessao:
        sessao.headers.update({"User-Agent": "easy-ai-clients-text/1.0"})
        resposta = sessao.get(
            "https://router.huggingface.co/v1/models",
            headers={"Authorization": f"Bearer {chave}"},
            timeout=180,
        )
        resposta.raise_for_status()
        return _transformar_modelos(resposta.json())


def _preco_catalogo_para_float(valor):
    """Converte valores textuais de `pricing` para comparacao numerica."""
    if valor in (None, ""):
        return 10**9
    return float(valor)


def _transformar_modelos(resposta_json):
    """Normaliza a listagem retornada pelo endpoint `/v1/models`."""
    return resposta_json.get("data") or []
