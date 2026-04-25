"""Cliente de geracao texto->texto para a API da Groq.

Ultima atualizacao: 2026-04-23
"""

from ..post_processing import calcular_custo_tokens, montar_resultado_chat_compativel
from ..pre_processing import (
    listar_modelos_compativeis,
)
from ._shared import (
    GROQ_PARAMETERS,
    build_chat_payload,
    execute_chat_request,
    validate_kwargs,
)

_PRECOS_MODELOS = {
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "qwen/qwen3-32b": {"input": 0.29, "output": 0.59},
    "openai/gpt-oss-20b": {"input": 0.075, "cached_input": 0.0375, "output": 0.30},
    "openai/gpt-oss-120b": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
    "moonshotai/kimi-k2-instruct-0905": {
        "input": 1.00,
        "cached_input": 0.50,
        "output": 3.00,
    },
    "meta-llama/llama-4-scout-17b-16e-instruct": {
        "input": 0.11,
        "output": 0.34,
    },
}


def generate(
    input_text,
    instruction=None,
    model="llama-3.1-8b-instant",
    **kwargs,
):
    """Generate text with Groq. Full details: text/docs/groq.md."""
    validate_kwargs(
        provider="groq",
        api="chat/completions",
        model=model,
        kwargs=kwargs,
        supported_parameters=GROQ_PARAMETERS,
    )
    corpo = build_chat_payload(
        input_text=input_text,
        instruction=instruction,
        model=model,
        kwargs=kwargs,
    )
    resposta_json, resposta_http = execute_chat_request(
        env_var="GROQ_API_KEY",
        url="https://api.groq.com/openai/v1/chat/completions",
        payload=corpo,
    )
    return montar_resultado_chat_compativel(
        provider="groq",
        model=model,
        input_text=input_text,
        instruction=instruction,
        resposta_json=resposta_json,
        resposta_http=resposta_http,
        resolvedor_custo=_resolver_custo,
    )


def list_models(api_key=None, timeout=180):
    """Lista os modelos atualmente visiveis pela conta da Groq."""
    return listar_modelos_compativeis(
        env_var="GROQ_API_KEY",
        url_modelos="https://api.groq.com/openai/v1/models",
        api_key=api_key,
        timeout=timeout,
        transformador=_transformar_modelos,
    )


def _resolver_custo(resultado, resposta_json, resposta_http):
    """Resolve o custo a partir do uso retornado pela Groq."""
    del resposta_json, resposta_http
    custo = _calcular_custo(resultado.get("model"), resultado.get("usage") or {})
    return custo, "usage_x_pricing_page"


def _calcular_custo(modelo, uso):
    """Calcula custo para modelos conhecidos da Groq."""
    precos = _resolver_preco_modelo(modelo)
    if not precos:
        return 0.0
    return calcular_custo_tokens(uso, precos)


def _resolver_preco_modelo(modelo):
    """Resolve aliases simples e retorna a tabela de precos do modelo."""
    modelo_normalizado = (modelo or "").lower()
    if modelo_normalizado in _PRECOS_MODELOS:
        return _PRECOS_MODELOS[modelo_normalizado]

    for chave, precos in _PRECOS_MODELOS.items():
        if chave in modelo_normalizado:
            return precos

    return None


def _transformar_modelos(resposta_json):
    """Normaliza a listagem de modelos do endpoint `/models`."""
    return resposta_json.get("data") or []


def _normalizar_service_tier(service_tier):
    """Normaliza o tier simplificado exposto pelo wrapper."""
    if service_tier is None:
        return None
    service_tier = str(service_tier).strip()
    if not service_tier or service_tier.lower() == "none":
        return None
    return service_tier
