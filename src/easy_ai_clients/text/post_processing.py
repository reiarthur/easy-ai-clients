"""Rotinas compartilhadas de pos-processamento para integracoes texto->texto.

Centraliza extracao de texto, normalizacao de uso, calculo de custo e montagem
do contrato final retornado pelos provedores.

Ultima atualizacao: 2026-04-23
"""

from decimal import Decimal

from requests import exceptions as requests_exceptions


def extrair_request_id(resposta_json, resposta_http=None):
    """Extrai o identificador da requisicao a partir do corpo ou cabecalhos."""
    for chave in ("id", "responseId", "request_id", "requestId"):
        valor = resposta_json.get(chave)
        if valor:
            return valor

    if resposta_http is None:
        return None

    for chave in (
        "x-generation-id",
        "x-request-id",
        "request-id",
        "openai-request-id",
        "anthropic-request-id",
        "x-amzn-requestid",
    ):
        valor = resposta_http.headers.get(chave)
        if valor:
            return valor

    return None


def extrair_texto_lista_conteudo(conteudos):
    """Concatena blocos textuais heterogeneos em uma unica string."""
    partes = []

    for item in conteudos or []:
        if isinstance(item, str):
            partes.append(item)
            continue

        if not isinstance(item, dict):
            continue

        texto = item.get("text")
        if texto:
            partes.append(texto)
            continue

        subpartes = item.get("parts")
        if subpartes:
            partes.append(extrair_texto_lista_conteudo(subpartes))
            continue

        if item.get("type") == "output_text" and item.get("text"):
            partes.append(item["text"])

    return "".join(parte for parte in partes if parte)


def extrair_texto_openai_compativel(resposta_json):
    """Extrai o texto principal de respostas no formato OpenAI-compatible."""
    escolhas = resposta_json.get("choices") or []
    if not escolhas:
        return ""

    mensagem = escolhas[0].get("message") or {}
    conteudo = mensagem.get("content")

    if isinstance(conteudo, str):
        if conteudo:
            return conteudo

    if isinstance(conteudo, list):
        texto = extrair_texto_lista_conteudo(conteudo)
        if texto:
            return texto

    return mensagem.get("reasoning_content") or ""


def extrair_texto_openai_responses(resposta_json):
    """Extrai o texto principal da Responses API da OpenAI."""
    if resposta_json.get("output_text"):
        return resposta_json["output_text"]

    saidas = resposta_json.get("output") or []
    for item in saidas:
        if item.get("type") != "message":
            continue
        conteudos = item.get("content") or []
        texto = extrair_texto_lista_conteudo(conteudos)
        if texto:
            return texto

    return ""


def extrair_texto_anthropic(resposta_json):
    """Extrai o texto principal do formato Messages da Anthropic."""
    return extrair_texto_lista_conteudo(resposta_json.get("content") or [])


def extrair_texto_google(resposta_json):
    """Extrai o texto principal do formato `generateContent` do Gemini."""
    candidatos = resposta_json.get("candidates") or []
    if not candidatos:
        return ""

    conteudo = candidatos[0].get("content") or {}
    return extrair_texto_lista_conteudo(conteudo.get("parts") or [])


def extrair_texto_cohere(resposta_json):
    """Extrai o texto principal do formato Chat v2 da Cohere."""
    mensagem = resposta_json.get("message") or {}
    return extrair_texto_lista_conteudo(mensagem.get("content") or [])


def normalizar_uso(uso):
    """Normaliza objetos de uso distintos para um formato minimo comum."""
    if not uso:
        return {}

    tokens = uso.get("tokens") or {}
    billed_units = uso.get("billed_units") or {}
    prompt_details = uso.get("prompt_tokens_details") or {}
    input_details = uso.get("input_tokens_details") or {}
    completion_details = uso.get("completion_tokens_details") or {}
    output_details = uso.get("output_tokens_details") or {}

    prompt_tokens_details_lista = uso.get("promptTokensDetails") or []
    prompt_tokens_texto = 0
    if prompt_tokens_details_lista:
        prompt_tokens_texto = sum(
            item.get("tokenCount", 0) for item in prompt_tokens_details_lista
        )

    cache_tokens_details_lista = uso.get("cacheTokensDetails") or []
    cached_content_token_count = uso.get("cachedContentTokenCount")
    if cached_content_token_count is None and cache_tokens_details_lista:
        cached_content_token_count = sum(
            item.get("tokenCount", 0) for item in cache_tokens_details_lista
        )

    prompt_cache_hit_tokens = uso.get("prompt_cache_hit_tokens")
    prompt_cache_miss_tokens = uso.get("prompt_cache_miss_tokens")
    input_tokens = (
        uso.get("input_tokens")
        or uso.get("prompt_tokens")
        or uso.get("promptTokenCount")
        or tokens.get("input_tokens")
    )
    if input_tokens is None and (
        prompt_cache_hit_tokens is not None or prompt_cache_miss_tokens is not None
    ):
        input_tokens = (prompt_cache_hit_tokens or 0) + (prompt_cache_miss_tokens or 0)

    output_tokens = (
        uso.get("output_tokens")
        or uso.get("completion_tokens")
        or uso.get("candidatesTokenCount")
        or tokens.get("output_tokens")
    )
    total_tokens = (
        uso.get("total_tokens")
        or uso.get("totalTokenCount")
        or tokens.get("total_tokens")
    )
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    dados = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_tokens": (
            uso.get("cached_content_token_count")
            or cached_content_token_count
            or input_details.get("cached_tokens")
            or prompt_details.get("cached_tokens")
            or uso.get("cache_read_input_tokens")
            or uso.get("cached_tokens")
            or prompt_cache_hit_tokens
            or 0
        ),
        "cache_write_tokens": (
            uso.get("cache_write_tokens")
            or uso.get("input_cache_write_tokens")
            or
            uso.get("cache_creation_input_tokens")
            or prompt_details.get("cache_write_tokens")
            or 0
        ),
        "reasoning_tokens": (
            uso.get("reasoning_tokens")
            or
            uso.get("thoughtsTokenCount")
            or output_details.get("reasoning_tokens")
            or completion_details.get("reasoning_tokens")
            or 0
        ),
        "billed_input_tokens": (
            billed_units.get("input_tokens")
            or uso.get("billed_input_tokens")
        ),
        "billed_output_tokens": (
            billed_units.get("output_tokens")
            or uso.get("billed_output_tokens")
        ),
        "estimated_cost": uso.get("estimated_cost"),
        "cost_in_usd_ticks": uso.get("cost_in_usd_ticks"),
        "provider_cost": uso.get("cost"),
        "provider_name": uso.get("provider_name"),
        "provider_header": uso.get("provider_header"),
        "prompt_tokens_texto": prompt_tokens_texto or None,
        "web_search_requests": uso.get("web_search_requests"),
    }

    return remover_nulos(dados)


def usd_ticks_para_float(valor_ticks):
    """Converte `cost_in_usd_ticks` para dolares."""
    if valor_ticks in (None, ""):
        return 0.0
    return _decimal_para_float(Decimal(str(valor_ticks)) / Decimal("10000000000"))


def calcular_custo_tokens(uso, precos):
    """Calcula o custo em USD a partir do uso e de uma tabela de precos.

    ### Parâmetros:
    - uso (dict): Estrutura de uso retornada pela API.
    - precos (dict): Tabela em USD por 1M de tokens. Aceita as chaves
      `input`, `output`, `cached_input`, `cache_write`, `cache_read`,
      `reasoning`, `billed_input` e `billed_output`.

    ### Retorna:
    - float: Valor em USD convertido para `float` nativo.
    """
    uso_normalizado = normalizar_uso(uso)
    custo = Decimal("0")

    billed_input = uso_normalizado.get("billed_input_tokens")
    billed_output = uso_normalizado.get("billed_output_tokens")
    if billed_input is not None and billed_output is not None:
        custo += _custo_por_milhao(
            billed_input, precos.get("billed_input", precos.get("input"))
        )
        custo += _custo_por_milhao(
            billed_output, precos.get("billed_output", precos.get("output"))
        )
        return _decimal_para_float(custo)

    cache_write_tokens = uso_normalizado.get("cache_write_tokens", 0) or 0
    cache_read_tokens = uso_normalizado.get("cached_tokens", 0) or 0
    input_tokens = uso_normalizado.get("input_tokens", 0) or 0
    output_tokens = uso_normalizado.get("output_tokens", 0) or 0
    reasoning_tokens = uso_normalizado.get("reasoning_tokens", 0) or 0

    if precos.get("cache_write") is not None:
        custo += _custo_por_milhao(cache_write_tokens, precos.get("cache_write"))
        custo += _custo_por_milhao(cache_read_tokens, precos.get("cache_read"))
        custo += _custo_por_milhao(input_tokens, precos.get("input"))
    else:
        input_nao_cacheado = max(input_tokens - cache_read_tokens, 0)
        custo += _custo_por_milhao(input_nao_cacheado, precos.get("input"))
        custo += _custo_por_milhao(
            cache_read_tokens,
            precos.get("cached_input", precos.get("input")),
        )

    if precos.get("reasoning") is not None and reasoning_tokens:
        output_sem_reasoning = max(output_tokens - reasoning_tokens, 0)
        custo += _custo_por_milhao(output_sem_reasoning, precos.get("output"))
        custo += _custo_por_milhao(reasoning_tokens, precos.get("reasoning"))
    else:
        custo += _custo_por_milhao(output_tokens, precos.get("output"))

    return _decimal_para_float(custo)


def calcular_custo_catalogo_por_token(uso, pricing):
    """Calcula custo usando metadados de catalogo precificados por token."""
    uso_normalizado = normalizar_uso(uso)

    input_preco = Decimal(str(pricing.get("prompt") or 0))
    output_preco = Decimal(str(pricing.get("completion") or 0))
    cache_read_preco = Decimal(
        str(pricing.get("input_cache_read") or pricing.get("prompt") or 0)
    )
    cache_write_preco = Decimal(
        str(pricing.get("input_cache_write") or pricing.get("prompt") or 0)
    )
    reasoning_preco = Decimal(
        str(pricing.get("internal_reasoning") or pricing.get("completion") or 0)
    )
    request_preco = Decimal(str(pricing.get("request") or 0))
    web_search_preco = Decimal(str(pricing.get("web_search") or 0))

    input_tokens = Decimal(str(uso_normalizado.get("input_tokens", 0) or 0))
    output_tokens = Decimal(str(uso_normalizado.get("output_tokens", 0) or 0))
    cached_tokens = Decimal(str(uso_normalizado.get("cached_tokens", 0) or 0))
    cache_write_tokens = Decimal(
        str(uso_normalizado.get("cache_write_tokens", 0) or 0)
    )
    reasoning_tokens = Decimal(
        str(uso_normalizado.get("reasoning_tokens", 0) or 0)
    )
    web_search_requests = Decimal(
        str(uso_normalizado.get("web_search_requests", 0) or 0)
    )

    input_nao_cacheado = max(
        input_tokens - cached_tokens - cache_write_tokens,
        Decimal("0"),
    )
    output_sem_reasoning = max(output_tokens - reasoning_tokens, Decimal("0"))

    custo = (input_nao_cacheado * input_preco) + (cached_tokens * cache_read_preco)
    custo += cache_write_tokens * cache_write_preco
    custo += output_sem_reasoning * output_preco
    custo += reasoning_tokens * reasoning_preco
    custo += request_preco
    custo += web_search_requests * web_search_preco
    return _decimal_para_float(custo)


def montar_resultado(
    provider,
    model,
    input_text,
    output_text,
    request_id,
    instruction=None,
    cost_usd=0.0,
    usage=None,
    extra=None,
):
    """Monta o dicionario padrao retornado pelas funcoes `generate`."""
    resultado = {
        "provider": provider,
        "model": model,
        "input_text": input_text,
        "output_text": output_text,
        "cost_usd": _decimal_para_float(Decimal(str(cost_usd or 0))),
        "request_id": request_id,
    }

    if instruction is not None:
        resultado["instruction"] = instruction

    if usage is not None:
        resultado["usage"] = usage

    if extra:
        resultado.update(extra)

    return resultado


def montar_resultado_chat_compativel(
    provider,
    model,
    input_text,
    instruction,
    resposta_json,
    resposta_http,
    extrator_texto=None,
    extra_resultado=None,
    resolvedor_custo=None,
):
    """Monta o resultado padronizado para respostas OpenAI-compatible."""
    uso_normalizado = normalizar_uso(resposta_json.get("usage") or {})
    provider_header = resposta_http.headers.get("x-inference-provider")
    if provider_header:
        uso_normalizado["provider_header"] = provider_header

    output_text = (extrator_texto or extrair_texto_openai_compativel)(resposta_json)
    resultado = montar_resultado(
        provider=provider,
        model=model,
        input_text=input_text,
        output_text=output_text,
        request_id=extrair_request_id(resposta_json, resposta_http),
        instruction=instruction,
        usage=uso_normalizado,
        extra=extra_resultado,
    )

    if resolvedor_custo:
        try:
            custo, origem = resolvedor_custo(
                resultado=resultado,
                resposta_json=resposta_json,
                resposta_http=resposta_http,
            )
        except (RuntimeError, requests_exceptions.RequestException):
            atualizar_custo_no_resultado(
                resultado,
                0.0,
                origem="cost_lookup_failed",
            )
        else:
            atualizar_custo_no_resultado(resultado, custo, origem=origem)

    return normalizar_resultado_publico(resultado)


def atualizar_custo_no_resultado(resultado, cost_usd, origem=None):
    """Atualiza o custo de um dicionario de resultado mantendo a estrutura."""
    resultado["cost_usd"] = _decimal_para_float(Decimal(str(cost_usd or 0)))
    if origem:
        resultado["cost_source"] = origem
    return resultado


def normalizar_resultado_publico(resultado):
    """Retorna apenas o contrato publico final, na ordem padronizada."""
    resultado_publico = {
        "request_id": resultado.get("request_id"),
        "cost_source": resultado.get("cost_source") or "cost_lookup_failed",
        "cost_usd": _decimal_para_float(Decimal(str(resultado.get("cost_usd") or 0))),
        "input_text": resultado.get("input_text"),
    }

    if resultado.get("instruction") is not None:
        resultado_publico["instruction"] = resultado.get("instruction")

    resultado_publico["output_text"] = resultado.get("output_text") or ""
    return resultado_publico


def remover_nulos(dados):
    """Retorna um dicionario sem chaves cujo valor seja `None`."""
    return {chave: valor for chave, valor in dados.items() if valor is not None}


def _custo_por_milhao(quantidade_tokens, preco_por_milhao):
    if quantidade_tokens in (None, 0) or preco_por_milhao in (None, 0):
        return Decimal("0")
    return (Decimal(str(quantidade_tokens)) * Decimal(str(preco_por_milhao))) / Decimal(
        "1000000"
    )


def _decimal_para_float(valor):
    if valor in (None, ""):
        return 0.0
    return float(Decimal(str(valor)))
