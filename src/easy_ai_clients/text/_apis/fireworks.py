"""Cliente de geracao texto->texto para a API da Fireworks AI.

Ultima atualizacao: 2026-04-23
"""

from ..post_processing import calcular_custo_tokens, montar_resultado_chat_compativel
from ..pre_processing import (
    listar_modelos_compativeis,
)
from ._shared import (
    FIREWORKS_PARAMETERS,
    build_chat_payload,
    execute_chat_request,
    validate_kwargs,
)

_PRECOS_MODELOS = {
    "accounts/fireworks/models/deepseek-v3p2": {
        "input": 0.56,
        "cached_input": 0.28,
        "output": 1.68,
    },
    "accounts/fireworks/models/deepseek-v3p1": {
        "input": 0.56,
        "cached_input": 0.28,
        "output": 1.68,
    },
    "accounts/fireworks/models/kimi-k2p5": {
        "input": 0.60,
        "cached_input": 0.10,
        "output": 3.00,
    },
    "accounts/fireworks/models/kimi-k2p5-turbo": {
        "input": 0.99,
        "cached_input": 0.16,
        "output": 4.94,
    },
    "accounts/fireworks/models/glm-5": {
        "input": 1.00,
        "cached_input": 0.20,
        "output": 3.20,
    },
    "accounts/fireworks/models/glm-5p1": {
        "input": 1.40,
        "cached_input": 0.26,
        "output": 4.40,
    },
    "accounts/fireworks/models/minimax-m2p7": {
        "input": 0.30,
        "cached_input": 0.06,
        "output": 1.20,
    },
    "accounts/fireworks/models/minimax-m2p5": {
        "input": 0.30,
        "cached_input": 0.03,
        "output": 1.20,
    },
    "accounts/fireworks/models/gpt-oss-120b": {
        "input": 0.15,
        "cached_input": 0.075,
        "output": 0.60,
    },
    "accounts/fireworks/models/gpt-oss-20b": {
        "input": 0.07,
        "cached_input": 0.035,
        "output": 0.30,
    },
}


def generate(
    input_text,
    instruction=None,
    model="accounts/fireworks/models/gpt-oss-20b",
    **kwargs,
):
    """Generate text with Fireworks. Full details: text/docs/fireworks.md."""
    validate_kwargs(
        provider="fireworks",
        api="chat/completions",
        model=model,
        kwargs=kwargs,
        supported_parameters=FIREWORKS_PARAMETERS,
    )
    corpo = build_chat_payload(
        input_text=input_text,
        instruction=instruction,
        model=model,
        kwargs=kwargs,
    )
    resposta_json, resposta_http = execute_chat_request(
        env_var="FIREWORKS_API_KEY",
        url="https://api.fireworks.ai/inference/v1/chat/completions",
        payload=corpo,
    )
    return montar_resultado_chat_compativel(
        provider="fireworks",
        model=model,
        input_text=input_text,
        instruction=instruction,
        resposta_json=resposta_json,
        resposta_http=resposta_http,
        resolvedor_custo=_resolver_custo,
    )


def list_models(api_key=None, timeout=180):
    """Lista os modelos atuais da Fireworks que suportam chat."""
    return listar_modelos_compativeis(
        env_var="FIREWORKS_API_KEY",
        url_modelos="https://api.fireworks.ai/inference/v1/models",
        api_key=api_key,
        timeout=timeout,
        transformador=_transformar_modelos,
    )


def _resolver_custo(resultado, resposta_json, resposta_http):
    """Resolve o custo da Fireworks via uso de tokens."""
    del resposta_json, resposta_http
    custo = _calcular_custo(resultado.get("model"), resultado.get("usage") or {})
    return custo, "usage_x_pricing_page"


def _calcular_custo(modelo, uso):
    """Calcula custo monetario para modelos conhecidos da Fireworks."""
    precos = _resolver_preco_modelo(modelo)
    if not precos:
        return 0.0
    return calcular_custo_tokens(uso, precos)


def _resolver_preco_modelo(modelo):
    """Resolve aliases simples da Fireworks."""
    modelo_normalizado = (modelo or "").lower()
    for chave, precos in sorted(_PRECOS_MODELOS.items(), key=lambda item: -len(item[0])):
        if chave in modelo_normalizado:
            return precos
    return None


def _transformar_modelos(resposta_json):
    """Filtra apenas modelos com suporte a chat."""
    modelos = resposta_json.get("data") or []
    return [item for item in modelos if item.get("supports_chat")]
