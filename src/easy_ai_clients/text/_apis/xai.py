"""Cliente de geracao texto->texto para a API da xAI.

Ultima atualizacao: 2026-04-23
"""

from ..post_processing import (
    calcular_custo_tokens,
    montar_resultado_chat_compativel,
    usd_ticks_para_float,
)
from ..pre_processing import (
    listar_modelos_compativeis,
)
from ._shared import (
    XAI_PARAMETERS,
    build_chat_payload,
    execute_chat_request,
    validate_kwargs,
)

_PRECOS_FALLBACK = {
    "grok-code-fast-1": {"input": 0.20, "output": 1.50},
    "grok-4-fast-reasoning": {"input": 0.20, "output": 0.50},
    "grok-4-fast-non-reasoning": {"input": 0.20, "output": 0.50},
    "grok-4-1-fast-reasoning": {"input": 0.20, "output": 0.50},
    "grok-4-1-fast-non-reasoning": {"input": 0.20, "output": 0.50},
    "grok-3-mini": {"input": 0.30, "output": 0.50},
    "grok-3": {"input": 3.00, "output": 15.00},
    "grok-4-0709": {"input": 3.00, "output": 15.00},
}


def generate(
    input_text,
    instruction=None,
    model="grok-4-fast-non-reasoning",
    **kwargs,
):
    """Generate text with xAI. Full details: text/docs/xai.md."""
    validate_kwargs(
        provider="xai",
        api="chat/completions",
        model=model,
        kwargs=kwargs,
        supported_parameters=XAI_PARAMETERS,
    )
    corpo = build_chat_payload(
        input_text=input_text,
        instruction=instruction,
        model=model,
        kwargs=kwargs,
    )
    resposta_json, resposta_http = execute_chat_request(
        env_var="XAI_API_KEY",
        url="https://api.x.ai/v1/chat/completions",
        payload=corpo,
    )
    return montar_resultado_chat_compativel(
        provider="xai",
        model=model,
        input_text=input_text,
        instruction=instruction,
        resposta_json=resposta_json,
        resposta_http=resposta_http,
        resolvedor_custo=_resolver_custo,
    )


def list_models(api_key=None, timeout=180):
    """Lista os modelos disponiveis para a conta na xAI."""
    return listar_modelos_compativeis(
        env_var="XAI_API_KEY",
        url_modelos="https://api.x.ai/v1/models",
        api_key=api_key,
        timeout=timeout,
        transformador=_transformar_modelos,
    )


def _resolver_custo(resultado, resposta_json, resposta_http):
    """Resolve o custo a partir do campo `cost_in_usd_ticks` da xAI."""
    del resposta_json, resposta_http
    custo = _calcular_custo(resultado.get("model"), resultado.get("usage") or {})
    origem = _resolver_origem_custo(resultado.get("usage") or {})
    return custo, origem


def _calcular_custo(modelo, uso):
    """Calcula custo usando ticks ou um fallback de tabela publica."""
    ticks = uso.get("cost_in_usd_ticks")
    if ticks not in (None, ""):
        return usd_ticks_para_float(ticks)

    precos = _PRECOS_FALLBACK.get(modelo)
    if not precos:
        return 0.0
    return calcular_custo_tokens(uso, precos)


def _transformar_modelos(resposta_json):
    """Normaliza a listagem de modelos da xAI."""
    return resposta_json.get("data") or []


def _resolver_origem_custo(uso):
    """Resolve a origem do custo da resposta da xAI."""
    if (uso or {}).get("cost_in_usd_ticks") not in (None, ""):
        return "usage_ticks"
    return "usage_x_pricing_page"


def _normalizar_service_tier(service_tier):
    """Normaliza o tier simplificado exposto pelo wrapper."""
    if service_tier is None:
        return None
    service_tier = str(service_tier).strip()
    if not service_tier or service_tier.lower() == "none":
        return None
    return service_tier
