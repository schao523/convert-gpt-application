"""Runtime readiness states shared by generated plugin bootstraps."""

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

CORE_READY = "core_ready"
RAG_SETUP_REQUIRED = "rag_setup_required"
RAG_READY = "rag_ready"
RAG_INCOMPATIBLE = "rag_incompatible"
REVIEW_ASSETS_MISSING = "review_assets_missing"
RUNTIME_ASSET_TAMPERED = "runtime_asset_tampered"

ALL_STATES = frozenset({
    CORE_READY,
    RAG_SETUP_REQUIRED,
    RAG_READY,
    RAG_INCOMPATIBLE,
    REVIEW_ASSETS_MISSING,
    RUNTIME_ASSET_TAMPERED,
})


@dataclass(frozen=True)
class RuntimeStatus:
    state: str
    components: Mapping[str, str]
    config_path: Path | None

    def __post_init__(self) -> None:
        if self.state not in ALL_STATES:
            raise ValueError(f"unknown_runtime_state: {self.state}")
