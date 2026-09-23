"""Strict marketplace preparation catalogs and transactional local staging."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
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
    destination_parts: list[tuple[str, ...]] = []
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
            identity = destination.casefold()
            if identity in destinations:
                raise MarketplaceError("duplicate_marketplace_destination", destination)
            parts = tuple(part.casefold() for part in PurePosixPath(destination).parts)
            if any(
                parts[: len(existing)] == existing
                or existing[: len(parts)] == parts
                for existing in destination_parts
            ):
                raise MarketplaceError("overlapping_marketplace_destination", destination)
            destinations.add(identity)
            destination_parts.append(parts)
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
        _copy_marketplace_tree(baseline_root, stage)
        for entry in catalog.applications:
            if entry.mode == "build":
                _build_entry(entry, stage, temporary_root / entry.application.plugin_id)
            else:
                _verify_existing_entry(entry, baseline_root, stage)
        _write_generated_controls(catalog, stage)
        comparison = temporary_root / "comparison"
        _copy_marketplace_tree(baseline_root, comparison)
        if _is_git_root(baseline_root):
            for entry in catalog.applications:
                if entry.mode == "verify_existing":
                    _materialize_committed_destinations(
                        baseline_root,
                        comparison,
                        (entry.codex_destination, entry.openclaw_destination),
                    )
        delta = _tree_delta(comparison, stage)
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
    controls_valid = _marketplace_controls_valid(catalog, root, registry_path, verifier)
    if not controls_valid:
        gates["filesystem"] = "FAIL"
        diagnostics.extend(entry.application.plugin_id for entry in catalog.applications)
    for entry in catalog.applications if controls_valid else ():
        try:
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
        except subprocess.TimeoutExpired:
            gates["filesystem"] = "FAIL"
            diagnostics.append(entry.application.plugin_id)
            continue
        try:
            from .results import operation_result_from_payload

            payload = json.loads(completed.stdout)
            parsed = operation_result_from_payload(payload)
            valid_result = (
                not completed.stderr
                and parsed.operation == "verify-marketplace"
                and parsed.status == "PASS"
                and parsed.code == "marketplace_verified"
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            valid_result = False
        if completed.returncode != 0 or not valid_result:
            gates["filesystem"] = "FAIL"
            diagnostics.append(entry.application.plugin_id)

    git_codes: tuple[str, ...] = ()
    files_checked = 0
    requested_git = check_index or commit is not None or fresh_checkout
    if requested_git:
        scopes = tuple(
            destination
            for entry in catalog.applications
            for destination in (entry.codex_destination, entry.openclaw_destination)
        )
        reference = "HEAD" if fresh_checkout and commit is None else commit
        try:
            report = verify_git_evidence(
                root,
                scopes,
                commit=reference,
                fresh_checkout=fresh_checkout,
            )
        except subprocess.TimeoutExpired:
            git_codes = ("git_evidence_timeout",)
            report = None
        except ValueError:
            git_codes = ("git_evidence_command_failed",)
            report = None
        if report is None:
            gates["index"] = "FAIL"
            if commit is not None or fresh_checkout:
                gates["commit"] = "FAIL"
            if fresh_checkout:
                gates["fresh_checkout"] = "FAIL"
        else:
            git_codes = report.codes
            files_checked = report.files_checked
            gates["index"] = report.index_status
            if commit is not None or fresh_checkout:
                gates["commit"] = report.commit_status
            if fresh_checkout:
                gates["fresh_checkout"] = report.fresh_checkout_status

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
    _replace_destination(codex_artifact, _stage_destination(stage, entry.codex_destination))
    _replace_destination(openclaw_artifact, _stage_destination(stage, entry.openclaw_destination))


def _verify_existing_entry(entry: PreparationEntry, baseline: Path, stage: Path) -> None:
    committed = _is_git_root(baseline)
    if committed:
        _materialize_committed_destinations(
            baseline,
            stage,
            (entry.codex_destination, entry.openclaw_destination),
        )
    codex = _stage_destination(stage, entry.codex_destination)
    openclaw = _stage_destination(stage, entry.openclaw_destination)
    _check_plugin_manifest(codex, entry.application.plugin_id, entry.application.version)
    if entry.contract.schema_version == 3:
        verify_package(entry.contract, openclaw)
    else:
        _check_legacy_content_manifest(
            openclaw,
            entry.application.plugin_id,
            entry.application.version,
        )
    if not committed:
        if _tree_files(baseline / Path(entry.codex_destination)) != _tree_files(codex):
            raise MarketplaceError("verify_existing_mutated", entry.application.plugin_id)
        if _tree_files(baseline / Path(entry.openclaw_destination)) != _tree_files(openclaw):
            raise MarketplaceError("verify_existing_mutated", entry.application.plugin_id)


def _check_legacy_content_manifest(root: Path, plugin_id: str, version: str) -> None:
    manifest_path = root / "CONTENT-MANIFEST.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MarketplaceError("content_manifest_invalid", plugin_id) from exc
    if payload.get("schema_version") not in {1, 2}:
        raise MarketplaceError("content_manifest_invalid", plugin_id)
    if payload.get("plugin_id") != plugin_id or payload.get("version") != version:
        raise MarketplaceError("openclaw_identity_mismatch", plugin_id)
    records = payload.get("files")
    if not isinstance(records, list):
        raise MarketplaceError("content_manifest_invalid", plugin_id)
    by_path: dict[str, dict[str, object]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise MarketplaceError("content_manifest_invalid", plugin_id)
        relative = _destination(record["path"], "content_manifest_path")
        by_path[relative] = record
    actual = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    )
    if len(by_path) != len(records) or sorted(by_path) != actual:
        raise MarketplaceError("content_manifest_mismatch", plugin_id)
    actual_records = []
    for relative in actual:
        data = (root / relative).read_bytes()
        record: dict[str, object] = {
            "path": relative,
            "size": len(data),
            "sha256": sha256(data).hexdigest(),
        }
        for key in ("classification", "canonicalization"):
            if key in by_path[relative]:
                record[key] = by_path[relative][key]
        actual_records.append(record)
    identity = json.dumps(
        actual_records, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    expected = {
        "files": actual_records,
        "file_count": len(actual_records),
        "total_bytes": sum(int(item["size"]) for item in actual_records),
        "content_sha256": sha256(identity).hexdigest(),
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise MarketplaceError("content_manifest_mismatch", plugin_id)


def _is_git_root(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=path,
        shell=False,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return False
    return Path(completed.stdout.strip()).resolve() == path.resolve()


def _materialize_committed_destinations(
    baseline: Path,
    stage: Path,
    destinations: tuple[str, ...],
) -> None:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *destinations],
        cwd=baseline,
        shell=False,
        check=False,
        capture_output=True,
    )
    if status.returncode != 0:
        raise MarketplaceError("git_evidence_command_failed")
    if status.stdout:
        raise MarketplaceError("verify_existing_dirty")
    for destination in destinations:
        listing = subprocess.run(
            ["git", "ls-tree", "-r", "-z", "HEAD", "--", destination],
            cwd=baseline,
            shell=False,
            check=False,
            capture_output=True,
        )
        if listing.returncode != 0 or not listing.stdout:
            raise MarketplaceError("marketplace_destination_missing", destination)
        target = _stage_destination(stage, destination)
        if target.exists():
            shutil.rmtree(target)
        for record in listing.stdout.split(b"\0"):
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split(" ")
            relative = raw_path.decode("utf-8", "surrogateescape")
            if kind != "blob" or mode == "120000":
                raise MarketplaceError("link_forbidden", relative)
            output = (stage / Path(relative)).resolve()
            if not output.is_relative_to(target.resolve()):
                raise MarketplaceError("catalog_path_escape", relative)
            blob = subprocess.run(
                ["git", "cat-file", "blob", oid],
                cwd=baseline,
                shell=False,
                check=False,
                capture_output=True,
            )
            if blob.returncode != 0:
                raise MarketplaceError("git_evidence_command_failed")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(blob.stdout)


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

    codex_path = _first_catalog(
        stage,
        (".agents/plugins/marketplace.json", ".codex-plugin/marketplace.json"),
    )
    openclaw_path = _first_catalog(
        stage,
        (".claude-plugin/marketplace.json", "openclaw/marketplace.json"),
    )
    if codex_path.is_file():
        codex_catalog = _load_json_mapping(codex_path)
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
        openclaw_catalog = _load_json_mapping(openclaw_path)
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

    _update_build_catalogs(catalog, codex_catalog, openclaw_catalog)
    _write_json_file(codex_path, codex_catalog)
    _write_json_file(openclaw_path, openclaw_catalog)
    registry = _expected_registry(catalog, stage, codex_catalog, openclaw_catalog)
    _write_json_file(stage / ".obvious-one-validation.json", registry)
    _write_text_file(stage / "tools" / "verify_marketplace.py", render_marketplace_verifier())
    _write_text_file(stage / ".github" / "workflows" / "validate.yml", render_validation_workflow())
    _merge_exact_byte_attributes(catalog, stage)


def _load_json_mapping(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MarketplaceError("runtime_catalog_invalid") from exc
    if not isinstance(value, dict):
        raise MarketplaceError("runtime_catalog_invalid")
    return value


def _update_build_catalogs(
    catalog: PreparationCatalog,
    codex: dict[str, object],
    openclaw: dict[str, object],
) -> None:
    codex_records = codex.get("plugins")
    openclaw_records = openclaw.get("plugins")
    if not isinstance(codex_records, list) or not isinstance(openclaw_records, list):
        raise MarketplaceError("runtime_catalog_invalid")
    for entry in catalog.applications:
        if entry.mode != "build":
            continue
        codex_match = next((item for item in codex_records if isinstance(item, dict) and item.get("name") == entry.application.plugin_id), None)
        if codex_match is None:
            codex_match = {"name": entry.application.plugin_id}
            codex_records.append(codex_match)
        source = codex_match.get("source")
        source = dict(source) if isinstance(source, dict) else {}
        source["path"] = f"./{entry.codex_destination}"
        codex_match["source"] = source
        claw_match = next((item for item in openclaw_records if isinstance(item, dict) and item.get("name") == entry.application.plugin_id), None)
        if claw_match is None:
            claw_match = {"name": entry.application.plugin_id}
            openclaw_records.append(claw_match)
        claw_match["version"] = entry.application.version
        claw_match["source"] = f"./{entry.openclaw_destination}"


def _expected_registry(
    catalog: PreparationCatalog,
    stage: Path,
    codex_catalog: object,
    openclaw_catalog: object,
) -> dict[str, object]:
    from .marketplace_ci import build_validation_registry

    registry = build_validation_registry(codex_catalog, openclaw_catalog, catalog)
    entries = {entry.application.plugin_id: entry for entry in catalog.applications}
    for plugin in registry["plugins"]:
        entry = entries[plugin["plugin_id"]]
        plugin["artifacts"] = {
            "codex": _artifact_identity(_stage_destination(stage, entry.codex_destination)),
            "openclaw": _artifact_identity(_stage_destination(stage, entry.openclaw_destination)),
        }
    return registry


def _marketplace_controls_valid(
    catalog: PreparationCatalog,
    root: Path,
    registry_path: Path,
    verifier: Path,
) -> bool:
    from .marketplace_ci import render_marketplace_verifier

    try:
        expected_verifier = render_marketplace_verifier().replace("\r\n", "\n").replace("\r", "\n")
        observed_verifier = verifier.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
        if observed_verifier != expected_verifier:
            return False
        codex = _load_json_mapping(_first_catalog(root, (".agents/plugins/marketplace.json", ".codex-plugin/marketplace.json")))
        openclaw = _load_json_mapping(_first_catalog(root, (".claude-plugin/marketplace.json", "openclaw/marketplace.json")))
        recorded = _load_json_mapping(registry_path)
        return recorded == _expected_registry(catalog, root, codex, openclaw)
    except (MarketplaceError, OSError, UnicodeError):
        return False


def _first_catalog(stage: Path, candidates: tuple[str, ...]) -> Path:
    for relative in candidates:
        candidate = stage / Path(relative)
        if candidate.is_file():
            return candidate
    return stage / Path(candidates[0])


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


def _artifact_identity(root: Path) -> dict[str, object]:
    _reject_links(root)
    records = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            records.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "size": len(data),
                    "sha256": sha256(data).hexdigest(),
                }
            )
    identity = json.dumps(
        records, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return {
        "content_sha256": sha256(identity).hexdigest(),
        "file_count": len(records),
        "total_bytes": sum(record["size"] for record in records),
        "files": records,
    }


def _write_text_file(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def _validate_separate_roots(repository: Path, baseline: Path, output: Path) -> None:
    repository = repository.resolve()
    baseline = baseline.resolve()
    output = output.resolve()
    if (
        repository == baseline
        or repository.is_relative_to(baseline)
        or baseline.is_relative_to(repository)
        or baseline == output
        or baseline.is_relative_to(output)
        or output.is_relative_to(baseline)
        or output == repository
        or repository.is_relative_to(output)
    ):
        raise MarketplaceError("unsafe_marketplace_path")
    if output.is_relative_to(repository):
        relative = output.relative_to(repository)
        if not relative.parts or relative.parts[0].casefold() not in {"dist", ".tmp"}:
            raise MarketplaceError("unsafe_marketplace_path")


def _replace_destination(source: Path, destination: Path) -> None:
    _reject_links(source)
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, symlinks=True)


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


def _copy_marketplace_tree(source: Path, destination: Path) -> None:
    """Copy public marketplace content without repository-internal Git state."""

    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(".git"),
        symlinks=True,
    )
    _reject_links(destination)


def _reject_links(root: Path) -> None:
    if _path_is_link(root):
        raise MarketplaceError("link_forbidden", ".")
    for directory, names, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in (*names, *files):
            candidate = parent / name
            if _path_is_link(candidate):
                raise MarketplaceError(
                    "link_forbidden", candidate.relative_to(root).as_posix()
                )


def _stage_destination(stage: Path, relative: str) -> Path:
    stage_root = stage.resolve()
    destination = stage_root / Path(relative)
    current = stage_root
    for part in Path(relative).parts:
        current = current / part
        if _path_is_link(current):
            raise MarketplaceError("link_forbidden", relative)
    resolved = destination.resolve()
    if not resolved.is_relative_to(stage_root) or resolved == stage_root:
        raise MarketplaceError("catalog_path_escape", relative)
    return destination


def _path_is_link(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(attributes & 0x400)


def _tree_files(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise MarketplaceError("marketplace_destination_missing", root.name)
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
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
        if path.is_file() and ".git" not in path.relative_to(root).parts:
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
    windows = PureWindowsPath(text)
    if (
        text in {"", "."}
        or path.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or ".." in path.parts
        or any(part in {"", "."} for part in path.parts)
    ):
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
