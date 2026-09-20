"""Deterministic aggregation for machine-readable framework results."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Sequence

from .results import OperationResult, load_result, result_json, result_payload


def combine_results(inputs: Sequence[Path]) -> OperationResult:
    """Combine result documents using FAIL, BLOCKED, PASS precedence."""

    payloads = tuple(load_result(Path(path)) for path in inputs)
    if not payloads:
        raise ValueError("report_inputs_empty")
    status = "FAIL" if any(item.status == "FAIL" for item in payloads) else (
        "BLOCKED" if any(item.status == "BLOCKED" for item in payloads) else "PASS"
    )
    return OperationResult(
        operation="report",
        status=status,
        code="combined_results",
        evidence={"inputs": [result_payload(item) for item in payloads]},
    )


def write_result_transactionally(result: OperationResult, output: Path) -> None:
    """Write one canonical result without exposing or partially replacing paths."""

    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_name = stream.name
            stream.write(result_json(result))
        os.replace(temporary_name, destination)
        temporary_name = None
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
