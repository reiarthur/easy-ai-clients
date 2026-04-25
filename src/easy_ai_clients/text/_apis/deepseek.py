"""Cliente de geracao texto->texto para a API da DeepSeek.

Ultima atualizacao: 2026-04-23
"""

from ..post_processing import calcular_custo_tokens, montar_resultado_chat_compativel
from ..pre_processing import (
    listar_modelos_compativeis,
)
from ._shared import (
    DEEPSEEK_PARAMETERS,
    build_chat_payload,
    execute_chat_request,
    validate_kwargs,
)

_PRECOS = {
    "deepseek-chat": {"input": 0.28, "cached_input": 0.028, "output": 0.42},
    "deepseek-reasoner": {"input": 0.28, "cached_input": 0.028, "output": 0.42},
    "deepseek-v4-flash": {"input": 0.28, "cached_input": 0.028, "output": 0.42},
}


def generate(
    input_text,
    instruction=None,
    model="deepseek-v4-flash",
    **kwargs,
):
    """Generate text with DeepSeek. Full details: text/docs/deepseek.md."""
    validate_kwargs(
        provider="deepseek",
        api="chat/completions",
        model=model,
        kwargs=kwargs,
        supported_parameters=DEEPSEEK_PARAMETERS,
    )
    corpo = build_chat_payload(
        input_text=input_text,
        instruction=instruction,
        model=model,
        kwargs=kwargs,
    )
    resposta_json, resposta_http = execute_chat_request(
        env_var="DEEPSEEK_API_KEY",
        url="https://api.deepseek.com/chat/completions",
        payload=corpo,
    )
    return montar_resultado_chat_compativel(
        provider="deepseek",
        model=model,
        input_text=input_text,
        instruction=instruction,
        resposta_json=resposta_json,
        resposta_http=resposta_http,
        resolvedor_custo=_resolver_custo,
    )


def list_models(api_key=None, timeout=180):
    """Lista os modelos de chat disponiveis na DeepSeek."""
    return listar_modelos_compativeis(
        env_var="DEEPSEEK_API_KEY",
        url_modelos="https://api.deepseek.com/models",
        api_key=api_key,
        timeout=timeout,
        transformador=_transformar_modelos,
    )


def _resolver_custo(resultado, resposta_json, resposta_http):
    """Resolve o custo da chamada DeepSeek."""
    del resposta_json, resposta_http
    custo = _calcular_custo(resultado.get("model"), resultado.get("usage") or {})
    return custo, "usage_x_pricing_page"


def _calcular_custo(modelo, uso):
    """Calcula o custo com base nos tokens normalizados da resposta."""
    precos = _PRECOS.get(modelo)
    if not precos:
        return 0.0
    return calcular_custo_tokens(uso, precos)


def _transformar_modelos(resposta_json):
    """Normaliza a listagem de modelos da DeepSeek."""
    return resposta_json.get("data") or []


def _montar_reasoning(reasoning):
    """Converte o nivel simplificado em um booleano aceito pelo payload."""
    if reasoning is None:
        return None
    reasoning = str(reasoning).strip().lower()
    if not reasoning or reasoning == "none":
        return None
    if reasoning in {"low", "medium", "high"}:
        return {"enabled": True}
    raise ValueError("`reasoning` must be one of: low, medium, high, none, or None.")
