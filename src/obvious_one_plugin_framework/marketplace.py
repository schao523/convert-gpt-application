"""Strict marketplace preparation catalogs and transactional local staging."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from .contract import ContractError, DistributionContract, load_contract, require_buildable_contract
from .package_builder import build_package, verify_package
from .results import ArtifactRecord, MutationRecord, OperationResult
from .verification import (
    ApplicationConfig,
    ExpansionContext,
    expand_argv,
    load_application_config_path,
    resolve_within,
)


_CATALOG_KEYS = {"schema_version", "marketplace_id", "applications"}
_ENTRY_KEYS = {
    "application_config",
    "distribution_contract",
    "codex_destination",
    "openclaw_destination",
    "mode",
}


class MarketplaceError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class PreparationEntry:
    application: ApplicationConfig
    contract: DistributionContract
    codex_destination: str
    openclaw_destination: str
    mode: str


@dataclass(frozen=True)
class PreparationCatalog:
    schema_version: int
    marketplace_id: str
    applications: tuple[PreparationEntry, ...]
    repository_root: Path
    catalog_path: Path


def load_preparation_catalog(path: Path, repository_root: Path) -> PreparationCatalog:
    repository = Path(repository_root).resolve()
    catalog_path = _within(repository, path, "catalog_path", already_relative=False)
    try:
        raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MarketplaceError("invalid_marketplace_catalog") from exc
    root = _strict_mapping(raw, _CATALOG_KEYS, "catalog")
    if root["schema_version"] != 1:
        raise MarketplaceError("unsupported_marketplace_catalog_schema")
    marketplace_id = _text(root["marketplace_id"], "marketplace_id")
    applications_raw = root["applications"]
    if not isinstance(applications_raw, list) or not applications_raw:
        raise MarketplaceError("invalid_marketplace_applications")

    entries: list[PreparationEntry] = []
    identities: set[str] = set()
    destinations: set[str] = set()
    for index, item in enumerate(applications_raw):
        entry = _strict_mapping(item, _ENTRY_KEYS, f"applications[{index}]")
        config_path = _within(repository, entry["application_config"], "application_config")
        contract_path = _within(repository, entry["distribution_contract"], "distribution_contract")
        application = load_application_config_path(config_path, repository)
        contract = load_contract(contract_path)
        if contract_path != application.distribution_contract:
            raise MarketplaceError("distribution_contract_mismatch", application.application_id)
        if contract.plugin_id != application.plugin_id:
            raise MarketplaceError("marketplace_identity_mismatch", application.plugin_id)
        mode = _text(entry["mode"], "mode")
        if mode not in {"build", "verify_existing"}:
            raise MarketplaceError("invalid_preparation_mode", mode)
        if mode == "build":
            try:
                require_buildable_contract(contract)
            except ContractError as exc:
                raise MarketplaceError(exc.code, application.plugin_id) from exc
        codex_destination = _destination(entry["codex_destination"], "codex_destination")
        openclaw_destination = _destination(entry["openclaw_destination"], "openclaw_destination")
        if application.application_id in identities:
            raise MarketplaceError("duplicate_marketplace_application", application.application_id)
        identities.add(application.application_id)
        for destination in (codex_destination, openclaw_destination):
            if destination in destinations:
                raise MarketplaceError("duplicate_marketplace_destination", destination)
            destinations.add(destination)
        entries.append(
            PreparationEntry(
                application,
                contract,
                codex_destination,
                openclaw_destination,
                mode,
            )
        )
    return PreparationCatalog(1, marketplace_id, tuple(entries), repository, catalog_path)


def prepare_marketplace(
    catalog: PreparationCatalog,
    baseline: Path,
    output: Path,
) -> OperationResult:
    baseline_root = Path(baseline).resolve()
    output_root = Path(output).resolve()
    _validate_separate_roots(catalog.repository_root, baseline_root, output_root)
    if not baseline_root.is_dir():
        raise MarketplaceError("marketplace_baseline_missing")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".marketplace-", dir=output_root.parent) as temporary:
        temporary_root = Path(temporary)
        stage = temporary_root / "marketplace"
        shutil.copytree(baseline_root, stage)
        for entry in catalog.applications:
            if entry.mode == "build":
                _build_entry(entry, stage, temporary_root / entry.application.plugin_id)
            else:
                _verify_existing_entry(entry, baseline_root, stage)
        _write_generated_controls(catalog, stage)
        delta = _tree_delta(baseline_root, stage)
        aggregate, total_bytes = _tree_identity(stage)
        _replace_tree_transactionally(stage, output_root)
    return OperationResult(
        operation="prepare-marketplace",
        status="PASS",
        code="marketplace_prepared",
        artifacts=(ArtifactRecord(output_root.name, "marketplace_stage", aggregate, total_bytes),),
        mutations=tuple(MutationRecord(item["path"], item["action"]) for item in delta),
        evidence={
            "changed_paths": [item["path"] for item in delta],
            "marketplace_id": catalog.marketplace_id,
        },
    )


def verify_marketplace(
    catalog: PreparationCatalog,
    marketplace: Path,
    *,
    check_index: bool = False,
    commit: str | None = None,
    fresh_checkout: bool = False,
) -> OperationResult:
    """Verify staged artifacts and optional Git byte evidence without mutation."""

    from .git_evidence import verify_git_evidence

    root = Path(marketplace).resolve()
    registry_path = root / ".obvious-one-validation.json"
    verifier = root / "tools" / "verify_marketplace.py"
    if not registry_path.is_file() or not verifier.is_file():
        raise MarketplaceError("marketplace_controls_missing")

    gates = {
        "filesystem": "PASS",
        "index": "NOT VERIFIED",
        "commit": "NOT VERIFIED",
        "fresh_checkout": "NOT VERIFIED",
    }
    diagnostics = []
    for entry in catalog.applications:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(verifier),
                "--registry",
                str(registry_path),
                "--plugin",
                entry.application.plugin_id,
                "--json",
            ],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            timeout=180,
            check=False,
        )
        if completed.returncode != 0:
            gates["filesystem"] = "FAIL"
            diagnostics.append(entry.application.plugin_id)

    git_codes: tuple[str, ...] = ()
    files_checked = 0
    requested_git = check_index or commit is not None or fresh_checkout
    if gates["filesystem"] == "PASS" and requested_git:
        scopes = tuple(
            destination
            for entry in catalog.applications
            for destination in (entry.codex_destination, entry.openclaw_destination)
        )
        reference = "HEAD" if fresh_checkout and commit is None else commit
        report = verify_git_evidence(
            root,
            scopes,
            commit=reference,
            fresh_checkout=fresh_checkout,
        )
        git_codes = report.codes
        files_checked = report.files_checked
        gates["index"] = report.status
        if commit is not None or fresh_checkout:
            gates["commit"] = report.status
        if fresh_checkout:
            gates["fresh_checkout"] = report.status

    failed = gates["filesystem"] == "FAIL" or any(
        value == "FAIL" for value in gates.values()
    )
    aggregate, total_bytes = _tree_identity(root)
    return OperationResult(
        operation="verify-marketplace",
        status="FAIL" if failed else "PASS",
        code="marketplace_verification_failed" if failed else "marketplace_verified",
        artifacts=(ArtifactRecord(root.name, "marketplace_stage", aggregate, total_bytes),),
        evidence={
            "diagnostic_plugins": diagnostics,
            "files_checked": files_checked,
            "gates": gates,
            "git_codes": list(git_codes),
            "marketplace_id": catalog.marketplace_id,
        },
    )


def _build_entry(entry: PreparationEntry, stage: Path, work: Path) -> None:
    work.mkdir(parents=True)
    diagnostics = work / "diagnostics"
    diagnostics.mkdir()
    context = ExpansionContext(
        python=sys.executable,
        repository_root=entry.application.root,
        application_root=entry.application.root,
        diagnostics=diagnostics,
        plugin_id=entry.application.plugin_id,
        application_id=entry.application.application_id,
        version=entry.application.version,
    )
    completed = subprocess.run(
        expand_argv(entry.application.verification.codex_build.argv, context),
        cwd=entry.application.root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise MarketplaceError("codex_build_failed", entry.application.plugin_id)
    codex_root = diagnostics / "codex-marketplace"
    artifact_relative = expand_argv((entry.application.verification.codex_build.artifact_path,), context)[0]
    codex_artifact = resolve_within(codex_root, artifact_relative, field="codex artifact")
    if not codex_artifact.is_dir():
        raise MarketplaceError("codex_artifact_missing", entry.application.plugin_id)
    _check_plugin_manifest(codex_artifact, entry.application.plugin_id, entry.application.version)

    openclaw_artifact = work / "openclaw" / entry.application.plugin_id
    build_package(entry.contract, openclaw_artifact)
    verify_package(entry.contract, openclaw_artifact)
    _replace_destination(codex_artifact, stage / Path(entry.codex_destination))
    _replace_destination(openclaw_artifact, stage / Path(entry.openclaw_destination))


def _verify_existing_entry(entry: PreparationEntry, baseline: Path, stage: Path) -> None:
    codex = baseline / Path(entry.codex_destination)
    openclaw = baseline / Path(entry.openclaw_destination)
    _check_plugin_manifest(codex, entry.application.plugin_id, entry.application.version)
    verify_package(entry.contract, openclaw)
    if _tree_files(codex) != _tree_files(stage / Path(entry.codex_destination)):
        raise MarketplaceError("verify_existing_mutated", entry.application.plugin_id)
    if _tree_files(openclaw) != _tree_files(stage / Path(entry.openclaw_destination)):
        raise MarketplaceError("verify_existing_mutated", entry.application.plugin_id)


def _check_plugin_manifest(root: Path, plugin_id: str, version: str) -> None:
    try:
        payload = json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MarketplaceError("codex_manifest_invalid", plugin_id) from exc
    if payload.get("name") != plugin_id or payload.get("version") != version:
        raise MarketplaceError("codex_manifest_identity_mismatch", plugin_id)


def _write_generated_controls(catalog: PreparationCatalog, stage: Path) -> None:
    from .marketplace_ci import (
        build_validation_registry,
        render_marketplace_verifier,
        render_validation_workflow,
    )

    codex_path = stage / ".codex-plugin" / "marketplace.json"
    openclaw_path = stage / "openclaw" / "marketplace.json"
    if codex_path.is_file():
        codex_catalog: object = codex_path
    else:
        codex_catalog = {
            "plugins": [
                {
                    "name": entry.application.plugin_id,
                    "source": {"path": f"./{entry.codex_destination}"},
                }
                for entry in catalog.applications
            ]
        }
        _write_json_file(codex_path, codex_catalog)
    if openclaw_path.is_file():
        openclaw_catalog: object = openclaw_path
    else:
        openclaw_catalog = {
            "plugins": [
                {
                    "name": entry.application.plugin_id,
                    "version": entry.application.version,
                    "source": f"./{entry.openclaw_destination}",
                }
                for entry in catalog.applications
            ]
        }
        _write_json_file(openclaw_path, openclaw_catalog)

    registry = build_validation_registry(codex_catalog, openclaw_catalog, catalog)
    _write_json_file(stage / ".obvious-one-validation.json", registry)
    _write_text_file(stage / "tools" / "verify_marketplace.py", render_marketplace_verifier())
    _write_text_file(stage / ".github" / "workflows" / "validate.yml", render_validation_workflow())
    _merge_exact_byte_attributes(catalog, stage)


def _merge_exact_byte_attributes(catalog: PreparationCatalog, stage: Path) -> None:
    from .git_evidence import exact_byte_attributes

    path = stage / ".gitattributes"
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    existing = existing.replace("\r\n", "\n").replace("\r", "\n")
    lines = existing.splitlines()
    scopes = tuple(
        destination
        for entry in catalog.applications
        for destination in (entry.codex_destination, entry.openclaw_destination)
    )
    for line in exact_byte_attributes(scopes).splitlines():
        if line not in lines:
            lines.append(line)
    _write_text_file(path, "\n".join(lines) + "\n")


def _write_json_file(path: Path, value: object) -> None:
    _write_text_file(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _write_text_file(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def _validate_separate_roots(repository: Path, baseline: Path, output: Path) -> None:
    roots = (repository.resolve(), baseline.resolve(), output.resolve())
    for index, left in enumerate(roots):
        for right in roots[index + 1:]:
            if left == right or left.is_relative_to(right) or right.is_relative_to(left):
                raise MarketplaceError("unsafe_marketplace_path")


def _replace_destination(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def _replace_tree_transactionally(stage: Path, output: Path) -> None:
    backup = output.with_name(f".{output.name}.previous")
    if backup.exists():
        shutil.rmtree(backup)
    if output.exists():
        os.replace(output, backup)
    try:
        os.replace(stage, output)
    except Exception:
        if backup.exists() and not output.exists():
            os.replace(backup, output)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def _tree_files(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise MarketplaceError("marketplace_destination_missing", root.name)
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _tree_delta(before: Path, after: Path) -> list[dict[str, str]]:
    old = _tree_files(before)
    new = _tree_files(after)
    result = []
    for path in sorted(set(old) | set(new)):
        if old.get(path) == new.get(path):
            continue
        action = "create" if path not in old else "delete" if path not in new else "modify"
        result.append({"path": path, "action": action})
    return result


def _tree_identity(root: Path) -> tuple[str, int]:
    records = []
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            total += len(data)
            records.append({"path": path.relative_to(root).as_posix(), "sha256": sha256(data).hexdigest(), "size": len(data)})
    encoded = json.dumps(records, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest(), total


def _within(root: Path, value: object, field: str, *, already_relative: bool = True) -> Path:
    text = _text(value, field) if already_relative else str(value)
    candidate = Path(text)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise MarketplaceError("catalog_path_escape", field)
    return resolved


def _destination(value: object, field: str) -> str:
    text = _text(value, field).replace("\\", "/")
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise MarketplaceError("catalog_path_escape", field)
    return path.as_posix()


def _strict_mapping(value: object, keys: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise MarketplaceError("invalid_marketplace_catalog", label)
    if set(value) != keys:
        raise MarketplaceError("invalid_marketplace_catalog", label)
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarketplaceError("invalid_marketplace_catalog", field)
    return value
