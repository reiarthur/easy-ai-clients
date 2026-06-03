from .._common import result_utils


def build_result(provider, model=None, raw_response=None, output_path=None,
                 status=None, warnings=None):
    """Build a normalized stem separation result.

    Args:
        provider: Required. Provider identifier.
        model: Optional. Provider model.
        raw_response: Optional. Provider response.
        output_path: Optional. Saved output path.
        status: Optional. Status override.
        warnings: Optional. Warning strings.

    Returns:
        A normalized music result dictionary with stems when available.
    """
    return result_utils.normalize_provider_result(
        provider,
        model,
        raw_response,
        operation="stem_separation",
        output_path=output_path,
        status=status,
        stems=True,
    )


def failure_result(provider, model=None, exc=None, request_id=None,
                   output_path=None, warnings=None):
    """Build a normalized stem separation failure result.

    Args:
        provider: Required. Provider identifier.
        model: Optional. Provider model.
        exc: Optional. Error object.
        request_id: Optional. Provider request ID.
        output_path: Optional. Saved output path.
        warnings: Optional. Warning strings.

    Returns:
        A normalized failure dictionary.
    """
    return result_utils.failure_result(
        provider=provider,
        model=model,
        operation="stem_separation",
        exc=exc,
        request_id=request_id,
        output_path=output_path,
        warnings=warnings,
    )
