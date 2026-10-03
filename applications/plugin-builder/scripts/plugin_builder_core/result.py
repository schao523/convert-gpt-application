"""ASCII-safe operation result documents."""

from __future__ import annotations


def operation_document(
    operation: str,
    status: str,
    errors: list[str],
    **data: object,
) -> dict[str, object]:
    """Return the stable result-schema-v1 shape used by the product CLI."""

    return {
        "result_schema_version": 1,
        "operation": operation,
        "status": status,
        "errors": sorted(set(errors)),
        **data,
    }
