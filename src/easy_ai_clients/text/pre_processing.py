"""Rotinas compartilhadas de pre-processamento para integracoes texto->texto.

Centraliza carregamento de ambiente, preparo de payloads, execucao HTTP e
helpers genericos usados antes da interpretacao da resposta dos provedores.

Ultima atualizacao: 2026-04-22
"""

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests import exceptions as requests_exceptions

_CAMINHO_ENV = Path.cwd() / ".env"
_TIMEOUT_PADRAO = 180
_USER_AGENT = "easy-ai-clients-text/1.0"
_TENTATIVAS_GET = 3
_BACKOFF_INICIAL_GET = 0.4
_STATUS_HTTP_RETRIAVEIS = {408, 429, 500, 502, 503, 504}
_DOTENV_CARREGADO = False
_SESSAO = requests.Session()
_SESSAO.headers.update({"User-Agent": _USER_AGENT})


def carregar_variaveis_ambiente():
    """Carrega o arquivo `.env` da raiz do projeto quando ele existir."""
    global _DOTENV_CARREGADO
    if _DOTENV_CARREGADO:
        return

    if _CAMINHO_ENV.exists():
        load_dotenv(_CAMINHO_ENV, override=False)

    _DOTENV_CARREGADO = True


def obter_chave_api(nome_variavel, api_key=None):
    """Retorna a chave de API a partir do ambiente ou do argumento recebido.

    ### Parâmetros:
    - nome_variavel (str): Nome da variavel de ambiente que guarda a chave.
    - api_key (str | None): Chave explicitamente informada na chamada.

    ### Retorna:
    - str: Chave de API pronta para uso.

    ### Exceções:
    - RuntimeError: Quando nenhuma chave e encontrada.
    """
    carregar_variaveis_ambiente()
    chave = api_key or os.getenv(nome_variavel)
    if chave:
        return chave.strip()

    raise RuntimeError(
        f"A variavel de ambiente `{nome_variavel}` nao foi encontrada."
    )


def remover_nulos(dados):
    """Retorna um dicionario sem chaves cujo valor seja `None`."""
    return {chave: valor for chave, valor in dados.items() if valor is not None}


def montar_mensagens_chat(input_text, instruction=None, historico=None):
    """Monta a lista padrao de mensagens para APIs estilo chat."""
    mensagens = []

    if instruction:
        mensagens.append({"role": "system", "content": instruction})

    if historico:
        mensagens.extend(historico)

    mensagens.append({"role": "user", "content": input_text})
    return mensagens


def requisicao_json(
    metodo,
    url,
    headers=None,
    params=None,
    payload=None,
    timeout=None,
):
    """Executa uma requisicao HTTP JSON com tratamento de erro consistente.

    ### Parâmetros:
    - metodo (str): Metodo HTTP, como `GET` ou `POST`.
    - url (str): URL completa do endpoint.
    - headers (dict | None): Cabecalhos HTTP adicionais.
    - params (dict | None): Query string da requisicao.
    - payload (dict | list | None): Corpo JSON enviado.
    - timeout (int | float | None): Timeout em segundos.

    ### Retorna:
    - tuple[dict | list, requests.Response]: Corpo JSON parseado e resposta.

    ### Exceções:
    - RuntimeError: Quando a API responde com erro ou JSON invalido.
    """
    metodo_normalizado = metodo.upper()
    timeout_final = timeout or _TIMEOUT_PADRAO
    tentativas = _TENTATIVAS_GET if metodo_normalizado == "GET" else 1

    for tentativa in range(1, tentativas + 1):
        try:
            resposta = _SESSAO.request(
                method=metodo_normalizado,
                url=url,
                headers=headers,
                params=params,
                json=payload,
                timeout=timeout_final,
            )
        except (
            requests_exceptions.ChunkedEncodingError,
            requests_exceptions.ConnectionError,
            requests_exceptions.ReadTimeout,
        ):
            if tentativa >= tentativas:
                raise
            _aguardar_retry_get(tentativa)
            continue

        if resposta.ok:
            try:
                return resposta.json(), resposta
            except ValueError as erro:
                raise RuntimeError(
                    f"A resposta de `{url}` nao retornou JSON valido."
                ) from erro

        if (
            metodo_normalizado == "GET"
            and resposta.status_code in _STATUS_HTTP_RETRIAVEIS
            and tentativa < tentativas
        ):
            _aguardar_retry_get(tentativa)
            continue

        trecho = resposta.text[:1500]
        raise RuntimeError(
            f"Falha na requisicao para `{url}`: {resposta.status_code} - {trecho}"
        )

    raise RuntimeError(f"Falha inesperada ao consultar `{url}`.")


def montar_corpo_chat(
    input_text,
    instruction=None,
    historico=None,
    model=None,
    max_tokens=None,
    temperature=None,
    top_p=None,
    top_k=None,
    seed=None,
    stop=None,
    tools=None,
    tool_choice=None,
    response_format=None,
    frequency_penalty=None,
    presence_penalty=None,
    parallel_tool_calls=None,
    top_logprobs=None,
    service_tier=None,
    store=None,
    reasoning=None,
    parametros_extras=None,
):
    """Monta um corpo padrao para endpoints `chat/completions`."""
    corpo = remover_nulos(
        {
            "model": model,
            "messages": montar_mensagens_chat(
                input_text=input_text,
                instruction=instruction,
                historico=historico,
            ),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "seed": seed,
            "stop": stop,
            "tools": tools,
            "tool_choice": tool_choice,
            "response_format": response_format,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "parallel_tool_calls": parallel_tool_calls,
            "top_logprobs": top_logprobs,
            "service_tier": service_tier,
            "store": store,
            "reasoning": reasoning,
        }
    )

    if parametros_extras:
        corpo.update(parametros_extras)

    return corpo


def executar_requisicao_chat_compativel(
    env_var,
    url_chat,
    corpo,
    api_key=None,
    timeout=None,
    cabecalho_autorizacao="Authorization",
    prefixo_autorizacao="Bearer ",
    headers_extras=None,
):
    """Executa uma chamada de chat OpenAI-compatible e retorna a resposta bruta."""
    chave = obter_chave_api(env_var, api_key=api_key)
    headers = {"Content-Type": "application/json"}

    if headers_extras:
        headers.update(headers_extras)

    headers[cabecalho_autorizacao] = f"{prefixo_autorizacao}{chave}"

    return requisicao_json(
        metodo="POST",
        url=url_chat,
        headers=headers,
        payload=corpo,
        timeout=timeout or _TIMEOUT_PADRAO,
    )


def listar_modelos_compativeis(
    env_var,
    url_modelos,
    api_key=None,
    timeout=None,
    cabecalho_autorizacao="Authorization",
    prefixo_autorizacao="Bearer ",
    headers_extras=None,
    transformador=None,
):
    """Lista modelos a partir de um endpoint OpenAI-compatible."""
    chave = obter_chave_api(env_var, api_key=api_key)
    headers = {}

    if headers_extras:
        headers.update(headers_extras)

    headers[cabecalho_autorizacao] = f"{prefixo_autorizacao}{chave}"

    resposta_json, _ = requisicao_json(
        metodo="GET",
        url=url_modelos,
        headers=headers,
        timeout=timeout or _TIMEOUT_PADRAO,
    )

    if transformador:
        return transformador(resposta_json)

    return resposta_json


def _aguardar_retry_get(tentativa):
    """Aguarda o backoff exponencial usado em retries de GET."""
    time.sleep(_BACKOFF_INICIAL_GET * (2 ** (tentativa - 1)))
