"""Exceções tipadas compartilhadas entre o núcleo interno e a API pública.

Última atualização: 2026-04-18
"""

from __future__ import annotations


class EasyAiClientError(Exception):
    """Erro base de toda falha pública ou interna de easy-ai-clients."""


class ConfigurationError(EasyAiClientError):
    """Configuração de runtime ausente ou inconsistente."""


class MissingCredentialError(ConfigurationError):
    """Credenciais obrigatórias do provider ausentes em variáveis ou credenciais explícitas.

    Attributes:
        provider: Nome canônico do provider que exige credenciais.
        env_vars: Nomes das variáveis de ambiente que precisam ser definidas.
    """

    def __init__(self, provider: str, env_vars: str | tuple[str, ...], *, detail: str | None = None) -> None:
        normalized = (env_vars,) if isinstance(env_vars, str) else tuple(env_vars)
        self.provider = provider
        self.env_vars = normalized
        expected = ", ".join(normalized)
        hint = (
            f"Set {expected} in your environment or pass them through "
            f"`credentials={{...}}` when calling easy-ai-clients."
        )
        message = detail or (
            f"Provider {provider!r} requires credential environment variable(s): "
            f"{expected}. {hint}"
        )
        super().__init__(message)


class UnsupportedProviderError(EasyAiClientError):
    """Alias de provider desconhecido."""


class UnsupportedModelError(EasyAiClientError):
    """Combinação provider/modelo não suportada pelo contrato da biblioteca."""


class InvalidParameterError(EasyAiClientError):
    """Parâmetro aceito recebeu valor inválido."""


class IncompatibleParameterError(EasyAiClientError):
    """Conjunto de parâmetros mutuamente incompatível."""


class PricingUnavailableError(EasyAiClientError):
    """Custo exato não pode ser calculado para o par provider/modelo informado."""


class ProviderTimeoutError(EasyAiClientError):
    """Timeout de HTTP ou de polling em chamada ao provider."""


class JobFailedError(EasyAiClientError):
    """Job longo do provider finalizou em estado de falha."""


class TemporaryDownloadError(EasyAiClientError):
    """URL temporária de ativo não pôde ser baixada com segurança."""


class InvalidProviderResponseError(EasyAiClientError):
    """Provider retornou uma forma de resposta não parseável pelo adapter."""


# Aliases internos em português usados pela camada de providers portada.
NovaIntegracaoError = EasyAiClientError
ConfiguracaoAmbienteError = ConfigurationError
ApiNaoSuportadaError = UnsupportedProviderError
ModeloNaoSuportadoError = UnsupportedModelError
ParametroInvalidoError = InvalidParameterError
ParametroIncompativelError = IncompatibleParameterError
PricingIndisponivelError = PricingUnavailableError
TimeoutProvedorError = ProviderTimeoutError
JobFalhouError = JobFailedError
DownloadTemporarioError = TemporaryDownloadError
RespostaInvalidaProviderError = InvalidProviderResponseError
