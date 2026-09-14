"""Configuration and result primitives for converted-application verification."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path, PurePosixPath
from string import Formatter
from typing import Any, Iterable, Mapping, Sequence

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
    "provenance",
    "verification",
}
_VERIFICATION_KEYS = {"test_directory", "commands", "codex_build", "marketplace"}
_COMMAND_KEYS = {"id", "argv", "clean_environment_prefixes"}
_CODEX_BUILD_KEYS = {"argv", "artifact_path"}
_MARKETPLACE_KEYS = {"codex_path", "openclaw_path", "approved_delta"}
_PROVENANCE_KEYS = {"source_repository", "incorporated_branches", "inventory_rules"}
_INVENTORY_RULE_KEYS = {"root", "classification", "include"}


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
class ProvenanceInventoryRule:
    root: PurePosixPath
    classification: str
    include: tuple[str, ...]


@dataclass(frozen=True)
class ProvenanceProfile:
    source_repository: str
    incorporated_branches: tuple[str, ...]
    inventory_rules: tuple[ProvenanceInventoryRule, ...]


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
    provenance: ProvenanceProfile
    verification: ApplicationVerificationProfile


@dataclass(frozen=True)
class ExpansionContext:
    python: str
    repository_root: Path
    application_root: Path
    diagnostics: Path
    plugin_id: str
    application_id: str
    version: str


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    state: str
    detail: str
    log_path: str | None = None
    data: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.state not in RESULT_STATES:
            raise ValueError(f"invalid result state: {self.state}")


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


def _safe_rule_path(value: Any, config_path: Path, field: str, *, allow_dot: bool) -> PurePosixPath:
    text = _text(value, config_path, field).replace("\\", "/")
    candidate = PurePosixPath(text)
    if candidate.is_absolute() or (candidate.parts and candidate.parts[0].endswith(":")):
        raise _error(config_path, field, "absolute paths are forbidden")
    if ".." in candidate.parts:
        raise _error(config_path, field, "path escape is forbidden")
    if not allow_dot and candidate.as_posix() in {"", "."}:
        raise _error(config_path, field, "must name a relative pattern")
    return candidate


def _load_provenance(raw: Any, *, config_path: Path) -> ProvenanceProfile:
    profile = _mapping(raw, config_path, "provenance")
    _only_keys(profile, _PROVENANCE_KEYS, config_path, "provenance")
    rules_raw = profile["inventory_rules"]
    if not isinstance(rules_raw, list) or not rules_raw:
        raise _error(config_path, "provenance.inventory_rules", "must be a non-empty list")
    rules: list[ProvenanceInventoryRule] = []
    identities: set[tuple[str, str, tuple[str, ...]]] = set()
    for index, item in enumerate(rules_raw):
        field = f"provenance.inventory_rules[{index}]"
        rule = _mapping(item, config_path, field)
        _only_keys(rule, _INVENTORY_RULE_KEYS, config_path, field)
        root = _safe_rule_path(rule["root"], config_path, f"{field}.root", allow_dot=True)
        classification = _text(rule["classification"], config_path, f"{field}.classification")
        patterns = _string_list(rule["include"], config_path, f"{field}.include")
        if not patterns:
            raise _error(config_path, f"{field}.include", "must not be empty")
        normalized_patterns = tuple(
            _safe_rule_path(pattern, config_path, f"{field}.include", allow_dot=False).as_posix()
            for pattern in patterns
        )
        identity = (root.as_posix(), classification, normalized_patterns)
        if identity in identities:
            raise _error(config_path, "provenance.inventory_rules", "duplicate rule")
        identities.add(identity)
        rules.append(ProvenanceInventoryRule(root, classification, normalized_patterns))
    return ProvenanceProfile(
        source_repository=_text(
            profile["source_repository"], config_path, "provenance.source_repository"
        ),
        incorporated_branches=_string_list(
            profile["incorporated_branches"],
            config_path,
            "provenance.incorporated_branches",
        ),
        inventory_rules=tuple(rules),
    )


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
        provenance=_load_provenance(raw["provenance"], config_path=config_path),
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


def select_applications(
    configs: Sequence[ApplicationConfig],
    *,
    application_id: str | None,
    select_all: bool,
) -> tuple[ApplicationConfig, ...]:
    """Select one application or all applications in stable identity order."""

    if application_id is not None and select_all:
        raise VerificationConfigError("--all and --application are mutually exclusive")
    ordered = tuple(sorted(configs, key=lambda item: item.application_id))
    if application_id is None:
        return ordered
    for config in ordered:
        if config.application_id == application_id:
            return (config,)
    raise VerificationConfigError(f"unknown application: {application_id}")


def expand_argv(argv: Sequence[str], context: ExpansionContext) -> list[str]:
    """Expand a validated argv template without invoking a command shell."""

    values = {
        "python": context.python,
        "repository_root": str(context.repository_root),
        "application_root": str(context.application_root),
        "diagnostics": str(context.diagnostics),
        "plugin_id": context.plugin_id,
        "application_id": context.application_id,
        "version": context.version,
    }
    result: list[str] = []
    for index, argument in enumerate(argv):
        if not isinstance(argument, str) or not argument:
            raise VerificationConfigError(f"argv[{index}]: must be non-empty text")
        _validate_placeholders(argument, Path("<runtime>"), f"argv[{index}]")
        try:
            expanded = argument.format_map(values)
        except (KeyError, ValueError) as exc:
            raise VerificationConfigError(f"argv[{index}]: invalid placeholder") from exc
        if not expanded:
            raise VerificationConfigError(f"argv[{index}]: expansion is empty")
        if argument.startswith(("{repository_root}", "{application_root}", "{diagnostics}")):
            expanded = str(Path(expanded))
        result.append(expanded)
    if not result:
        raise VerificationConfigError("argv: must not be empty")
    return result


def resolve_within(base: Path, value: str | Path, *, field: str) -> Path:
    """Resolve a relative path and require the result to remain below base."""

    boundary = Path(base).resolve()
    candidate = Path(value)
    if candidate.is_absolute():
        raise VerificationConfigError(f"{field}: absolute paths are forbidden")
    resolved = (boundary / candidate).resolve()
    if not resolved.is_relative_to(boundary):
        raise VerificationConfigError(f"{field}: path escapes declared boundary")
    return resolved


def aggregate_state(gates: Iterable[GateResult]) -> str:
    """Return FAIL for any failed required gate, otherwise PASS."""

    return "FAIL" if any(gate.state == "FAIL" for gate in gates) else "PASS"
