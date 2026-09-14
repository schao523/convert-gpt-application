"""Configuration and result primitives for converted-application verification."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
from string import Formatter
from typing import Any, Mapping

from .contract import ContractError, load_contract


RESULT_STATES = frozenset({"PASS", "FAIL", "NOT VERIFIED", "NOT APPLICABLE"})
ALLOWED_PLACEHOLDERS = frozenset(
    {
        "python",
        "repository_root",
        "application_root",
        "diagnostics",
        "plugin_id",
        "application_id",
        "version",
    }
)

_ROOT_KEYS = {
    "schema_version",
    "application_id",
    "plugin_id",
    "source_inventory",
    "source_location",
    "coverage_matrix",
    "distribution_contract",
    "marketplace_repository",
    "verification",
}
_VERIFICATION_KEYS = {"test_directory", "commands", "codex_build", "marketplace"}
_COMMAND_KEYS = {"id", "argv", "clean_environment_prefixes"}
_CODEX_BUILD_KEYS = {"argv", "artifact_path"}
_MARKETPLACE_KEYS = {"codex_path", "openclaw_path", "approved_delta"}


class VerificationConfigError(ValueError):
    """Raised when a conversion verification profile is invalid."""


@dataclass(frozen=True)
class VerificationCommand:
    command_id: str
    argv: tuple[str, ...]
    clean_environment_prefixes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CodexBuildProfile:
    argv: tuple[str, ...]
    artifact_path: str


@dataclass(frozen=True)
class MarketplaceProfile:
    codex_path: str
    openclaw_path: str
    approved_delta: Path


@dataclass(frozen=True)
class ApplicationVerificationProfile:
    test_directory: Path
    commands: tuple[VerificationCommand, ...]
    codex_build: CodexBuildProfile
    marketplace: MarketplaceProfile | None


@dataclass(frozen=True)
class ApplicationConfig:
    root: Path
    application_id: str
    plugin_id: str
    version: str
    source_inventory: Path
    source_location: Path
    coverage_matrix: Path
    distribution_contract: Path
    marketplace_repository: str
    verification: ApplicationVerificationProfile


def _error(path: Path, field: str, detail: str) -> VerificationConfigError:
    return VerificationConfigError(f"{path}: {field}: {detail}")


def _mapping(value: Any, path: Path, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise _error(path, field, "must be an object")
    return value


def _only_keys(
    value: Mapping[str, Any],
    allowed: set[str],
    path: Path,
    field: str,
    *,
    optional: set[str] | None = None,
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise _error(path, f"{field}.{unknown[0]}", "unknown field")
    required = allowed - (optional or set())
    missing = sorted(required - set(value))
    if missing:
        raise _error(path, f"{field}.{missing[0]}", "missing field")


def _text(value: Any, path: Path, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(path, field, "must be non-empty text")
    return value


def _string_list(value: Any, path: Path, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise _error(path, field, "must be a list")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_text(item, path, f"{field}[{index}]"))
    return tuple(result)


def _validate_placeholders(value: str, path: Path, field: str) -> None:
    try:
        parsed = Formatter().parse(value)
        fields = [name for _, name, _, _ in parsed if name is not None]
    except ValueError as exc:
        raise _error(path, field, "invalid placeholder syntax") from exc
    for name in fields:
        if name not in ALLOWED_PLACEHOLDERS:
            raise _error(path, field, f"unknown placeholder {name}")


def _argv(value: Any, path: Path, field: str) -> tuple[str, ...]:
    result = _string_list(value, path, field)
    if not result:
        raise _error(path, field, "must not be empty")
    for index, argument in enumerate(result):
        _validate_placeholders(argument, path, f"{field}[{index}]")
    return result


def _resolve_repository_path(
    value: Any,
    *,
    application_root: Path,
    repository_root: Path,
    config_path: Path,
    field: str,
    require_exists: bool,
) -> Path:
    text = _text(value, config_path, field)
    candidate = Path(text)
    if candidate.is_absolute():
        raise _error(config_path, field, "absolute paths are forbidden")
    resolved = (application_root / candidate).resolve()
    if not resolved.is_relative_to(repository_root):
        raise _error(config_path, field, "path escapes repository")
    if require_exists and not resolved.exists():
        raise _error(config_path, field, "path does not exist")
    return resolved


def _artifact_template(value: Any, config_path: Path, field: str) -> str:
    text = _text(value, config_path, field).replace("\\", "/")
    _validate_placeholders(text, config_path, field)
    sample = text
    for placeholder in ALLOWED_PLACEHOLDERS:
        sample = sample.replace("{" + placeholder + "}", "value")
    candidate = PurePosixPath(sample)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise _error(config_path, field, "path escape is forbidden")
    if any(part in {"", "."} for part in candidate.parts):
        raise _error(config_path, field, "invalid relative path")
    return text


def _load_verification(
    raw: Any,
    *,
    application_root: Path,
    repository_root: Path,
    config_path: Path,
) -> ApplicationVerificationProfile:
    profile = _mapping(raw, config_path, "verification")
    _only_keys(
        profile,
        _VERIFICATION_KEYS,
        config_path,
        "verification",
        optional={"marketplace"},
    )
    test_directory = _resolve_repository_path(
        profile["test_directory"],
        application_root=application_root,
        repository_root=application_root,
        config_path=config_path,
        field="verification.test_directory",
        require_exists=True,
    )

    commands_raw = profile["commands"]
    if not isinstance(commands_raw, list):
        raise _error(config_path, "verification.commands", "must be a list")
    commands: list[VerificationCommand] = []
    command_ids: set[str] = set()
    for index, item in enumerate(commands_raw):
        field = f"verification.commands[{index}]"
        command = _mapping(item, config_path, field)
        _only_keys(command, _COMMAND_KEYS, config_path, field, optional={"clean_environment_prefixes"})
        command_id = _text(command["id"], config_path, f"{field}.id")
        if command_id in command_ids:
            raise _error(config_path, "verification.commands", f"duplicate id {command_id}")
        command_ids.add(command_id)
        prefixes = _string_list(
            command.get("clean_environment_prefixes", []),
            config_path,
            f"{field}.clean_environment_prefixes",
        )
        commands.append(
            VerificationCommand(
                command_id=command_id,
                argv=_argv(command["argv"], config_path, f"{field}.argv"),
                clean_environment_prefixes=prefixes,
            )
        )

    build = _mapping(profile["codex_build"], config_path, "verification.codex_build")
    _only_keys(build, _CODEX_BUILD_KEYS, config_path, "verification.codex_build")
    codex_build = CodexBuildProfile(
        argv=_argv(build["argv"], config_path, "verification.codex_build.argv"),
        artifact_path=_artifact_template(
            build["artifact_path"], config_path, "verification.codex_build.artifact_path"
        ),
    )

    marketplace_profile: MarketplaceProfile | None = None
    if "marketplace" in profile:
        marketplace = _mapping(profile["marketplace"], config_path, "verification.marketplace")
        _only_keys(marketplace, _MARKETPLACE_KEYS, config_path, "verification.marketplace")
        marketplace_profile = MarketplaceProfile(
            codex_path=_artifact_template(
                marketplace["codex_path"], config_path, "verification.marketplace.codex_path"
            ),
            openclaw_path=_artifact_template(
                marketplace["openclaw_path"], config_path, "verification.marketplace.openclaw_path"
            ),
            approved_delta=_resolve_repository_path(
                marketplace["approved_delta"],
                application_root=application_root,
                repository_root=repository_root,
                config_path=config_path,
                field="verification.marketplace.approved_delta",
                require_exists=True,
            ),
        )
    return ApplicationVerificationProfile(
        test_directory=test_directory,
        commands=tuple(commands),
        codex_build=codex_build,
        marketplace=marketplace_profile,
    )


def load_application_config(application_root: Path, repository_root: Path) -> ApplicationConfig:
    """Load and validate one immediate `applications/*/conversion.json`."""

    repository = Path(repository_root).resolve()
    application = Path(application_root).resolve()
    config_path = application / "conversion.json"
    if application.parent != repository / "applications":
        raise _error(config_path, "application_root", "must be an immediate applications child")
    try:
        raw = _mapping(json.loads(config_path.read_text(encoding="utf-8")), config_path, "conversion")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _error(config_path, "conversion", "invalid JSON") from exc
    _only_keys(raw, _ROOT_KEYS, config_path, "conversion")
    if raw["schema_version"] != 2:
        raise _error(config_path, "schema_version", "must migrate to schema version 2")

    application_id = _text(raw["application_id"], config_path, "application_id")
    plugin_id = _text(raw["plugin_id"], config_path, "plugin_id")
    if application_id != application.name:
        raise _error(config_path, "application_id", "must match application directory")
    if plugin_id != application.name:
        raise _error(config_path, "plugin_id", "must match application directory")

    source_inventory = _resolve_repository_path(
        raw["source_inventory"], application_root=application, repository_root=repository,
        config_path=config_path, field="source_inventory", require_exists=True,
    )
    source_location = _resolve_repository_path(
        raw["source_location"], application_root=application, repository_root=repository,
        config_path=config_path, field="source_location", require_exists=False,
    )
    coverage_matrix = _resolve_repository_path(
        raw["coverage_matrix"], application_root=application, repository_root=application,
        config_path=config_path, field="coverage_matrix", require_exists=True,
    )
    distribution_contract = _resolve_repository_path(
        raw["distribution_contract"], application_root=application, repository_root=application,
        config_path=config_path, field="distribution_contract", require_exists=True,
    )
    try:
        contract = load_contract(distribution_contract)
    except ContractError as exc:
        raise _error(config_path, "distribution_contract", str(exc)) from exc
    if contract.plugin_id != plugin_id:
        raise _error(config_path, "distribution_contract", "plugin identity mismatch")

    return ApplicationConfig(
        root=application,
        application_id=application_id,
        plugin_id=plugin_id,
        version=contract.version,
        source_inventory=source_inventory,
        source_location=source_location,
        coverage_matrix=coverage_matrix,
        distribution_contract=distribution_contract,
        marketplace_repository=_text(
            raw["marketplace_repository"], config_path, "marketplace_repository"
        ),
        verification=_load_verification(
            raw["verification"],
            application_root=application,
            repository_root=repository,
            config_path=config_path,
        ),
    )


def discover_applications(repository_root: Path) -> tuple[ApplicationConfig, ...]:
    """Discover and validate every immediate configured application."""

    repository = Path(repository_root).resolve()
    applications_root = repository / "applications"
    configs = tuple(
        load_application_config(path.parent, repository)
        for path in sorted(applications_root.glob("*/conversion.json"))
    )
    application_ids = [config.application_id for config in configs]
    plugin_ids = [config.plugin_id for config in configs]
    if len(application_ids) != len(set(application_ids)):
        raise VerificationConfigError("conversion.json: application_id: duplicate identity")
    if len(plugin_ids) != len(set(plugin_ids)):
        raise VerificationConfigError("conversion.json: plugin_id: duplicate identity")
    return configs
