"""Cliente de geracao texto->texto para a API da DeepInfra.

Ultima atualizacao: 2026-04-23
"""

from ..post_processing import calcular_custo_tokens, montar_resultado_chat_compativel
from ..pre_processing import (
    listar_modelos_compativeis,
)
from ._shared import (
    DEEPINFRA_PARAMETERS,
    build_chat_payload,
    execute_chat_request,
    validate_kwargs,
)

_PRECOS_FALLBACK = {
    "stepfun-ai/step-3.5-flash": {"input": 0.10, "output": 0.30},
    "qwen/qwen3.5-0.8b": {"input": 0.01, "output": 0.05},
    "qwen/qwen3.5-2b": {"input": 0.02, "output": 0.10},
    "qwen/qwen3.5-4b": {"input": 0.03, "output": 0.15},
    "qwen/qwen3.5-9b": {"input": 0.04, "output": 0.20},
    "qwen/qwen3.6-35b-a3b": {"input": 0.20, "output": 1.00},
    "zai-org/glm-5.1": {"input": 1.40, "output": 4.40},
}


def generate(
    input_text,
    instruction=None,
    model="Qwen/Qwen3.5-0.8B",
    **kwargs,
):
    """Generate text with DeepInfra. Full details: text/docs/deepinfra.md."""
    validate_kwargs(
        provider="deepinfra",
        api="chat/completions",
        model=model,
        kwargs=kwargs,
        supported_parameters=DEEPINFRA_PARAMETERS,
    )
    corpo = build_chat_payload(
        input_text=input_text,
        instruction=instruction,
        model=model,
        kwargs=kwargs,
    )
    resposta_json, resposta_http = execute_chat_request(
        env_var="DEEPINFRA_API_KEY",
        url="https://api.deepinfra.com/v1/openai/chat/completions",
        payload=corpo,
    )
    return montar_resultado_chat_compativel(
        provider="deepinfra",
        model=model,
        input_text=input_text,
        instruction=instruction,
        resposta_json=resposta_json,
        resposta_http=resposta_http,
        resolvedor_custo=_resolver_custo,
    )


def list_models(api_key=None, timeout=180):
    """Lista os modelos OpenAI-compatible expostos pela DeepInfra."""
    return listar_modelos_compativeis(
        env_var="DEEPINFRA_API_KEY",
        url_modelos="https://api.deepinfra.com/v1/openai/models",
        api_key=api_key,
        timeout=timeout,
        transformador=_transformar_modelos,
    )


def _resolver_custo(resultado, resposta_json, resposta_http):
    """Resolve o custo usando o proprio campo `estimated_cost` da resposta."""
    del resposta_json, resposta_http
    custo = _calcular_custo(resultado.get("model"), resultado.get("usage") or {})
    origem = _resolver_origem_custo(resultado.get("usage") or {})
    return custo, origem


def _calcular_custo(modelo, uso):
    """Calcula custo por `estimated_cost` ou por uma tabela fallback."""
    estimated_cost = uso.get("estimated_cost")
    if estimated_cost not in (None, ""):
        return float(estimated_cost)

    modelo_normalizado = (modelo or "").lower()
    precos = _PRECOS_FALLBACK.get(modelo_normalizado)
    if not precos:
        return 0.0

    return calcular_custo_tokens(uso, precos)


def _transformar_modelos(resposta_json):
    """Normaliza a listagem de modelos da DeepInfra."""
    return resposta_json.get("data") or []


def _resolver_origem_custo(uso):
    """Resolve a origem do custo da DeepInfra."""
    if (uso or {}).get("estimated_cost") not in (None, ""):
        return "estimated_cost"
    return "usage_x_pricing_page"
