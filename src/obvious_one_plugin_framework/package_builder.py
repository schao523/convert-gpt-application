"""Deterministic, deny-by-default OpenClaw bundle generation."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import importlib.util
import os
from pathlib import Path
import shutil
import stat
from tempfile import TemporaryDirectory

from .contract import DistributionContract, validate_contract


MANIFEST_NAME = "CONTENT-MANIFEST.json"
BOOTSTRAP_SOURCE = Path(__file__).resolve().parent / "templates" / "runtime"
FORBIDDEN_NAMES = {".env", ".git", "__pycache__", "openclaw.plugin.json"}
SECRET_FRAGMENTS = ("BEGIN PRIVATE KEY", "AWS_SECRET_ACCESS_KEY=", "GH_TOKEN=")


class PackageAuditError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class BuildResult:
    output: Path
    file_count: int
    total_bytes: int
    content_sha256: str


def _file_sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _remove_tree(path: Path) -> None:
    if not path.exists():
        return
    def retry(function, value, _error):
        os.chmod(value, stat.S_IWRITE)
        function(value)
    shutil.rmtree(path, onexc=retry)


def _is_reparse_or_symlink(path: Path) -> bool:
    return path.is_symlink() or bool(path.stat(follow_symlinks=False).st_file_attributes & 0x400) if os.name == "nt" else path.is_symlink()


def _declared_sources(contract: DistributionContract) -> tuple[tuple[Path, str], ...]:
    selected: dict[str, Path] = {}
    excluded = set(contract.exclude_paths)
    for relative in contract.include_files:
        candidate = contract.source_root / relative
        if not candidate.is_file():
            raise PackageAuditError("included_file_missing", relative)
        selected[relative] = candidate
    for prefix in contract.include_prefixes:
        base = contract.source_root / prefix
        if not base.is_dir():
            raise PackageAuditError("included_prefix_missing", prefix)
        for candidate in base.rglob("*"):
            relative = candidate.relative_to(contract.source_root).as_posix()
            if candidate.is_dir():
                continue
            if relative not in excluded:
                selected[relative] = candidate
    for relative in excluded:
        selected.pop(relative, None)
    return tuple((selected[key], key) for key in sorted(selected))


def _copy_file(source: Path, destination: Path, relative: str) -> None:
    if _is_reparse_or_symlink(source):
        raise PackageAuditError("link_forbidden", relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def _render_bootstrap(stage: Path) -> None:
    destination = stage / "vendor" / "obvious-one-runtime"
    for source in sorted(BOOTSTRAP_SOURCE.rglob("*")):
        if source.is_file():
            relative = source.relative_to(BOOTSTRAP_SOURCE)
            _copy_file(source, destination / relative, relative.as_posix())


def _write_package_json(contract: DistributionContract, stage: Path) -> None:
    data = {
        "name": contract.package_name,
        "version": contract.version,
        "description": f"Generated OpenClaw bundle for {contract.plugin_id}",
        "repository": f"https://github.com/{contract.release_repository}",
        "license": "MIT",
        "openclaw": {"family": contract.family},
    }
    (stage / "package.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _apply_overlay(contract: DistributionContract, stage: Path) -> None:
    if contract.readme_overlay is None:
        return
    source = contract.source_root / contract.readme_overlay
    if not source.is_file():
        raise PackageAuditError("readme_overlay_missing", contract.readme_overlay)
    _copy_file(source, stage / "README.md", contract.readme_overlay)


def _audit(stage: Path, contract: DistributionContract) -> None:
    total = 0
    for candidate in stage.rglob("*"):
        relative = candidate.relative_to(stage).as_posix()
        if _is_reparse_or_symlink(candidate):
            raise PackageAuditError("link_forbidden", relative)
        if candidate.name in FORBIDDEN_NAMES:
            raise PackageAuditError("forbidden_file", relative)
        if not candidate.is_file():
            continue
        total += candidate.stat().st_size
        if candidate.suffix.lower() in {".md", ".json", ".py", ".txt", ""}:
            try:
                text = candidate.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = ""
            if any(fragment in text for fragment in SECRET_FRAGMENTS):
                raise PackageAuditError("secret_pattern", relative)
    if total > contract.max_total_bytes:
        raise PackageAuditError("package_too_large", str(total))


def _run_product_audit(stage: Path, contract: DistributionContract) -> None:
    if contract.audit_hook is None:
        return
    try:
        raw_path, function_name = contract.audit_hook.split(":", 1)
        relative = Path(raw_path.replace("\\", "/"))
        hook_path = (contract.source_root / relative).resolve()
        hook_path.relative_to(contract.source_root.resolve())
        if not hook_path.is_file() or not function_name.isidentifier():
            raise ValueError("invalid audit hook")
        spec = importlib.util.spec_from_file_location(
            f"obvious_one_audit_{contract.plugin_id.replace('-', '_')}", hook_path
        )
        if spec is None or spec.loader is None:
            raise ValueError("audit hook cannot be loaded")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        hook = getattr(module, function_name)
        result = hook(stage, contract)
        if result:
            raise ValueError("; ".join(str(item) for item in result))
    except Exception as exc:
        raise PackageAuditError("product_audit_failed", str(exc)) from exc


def _records(stage: Path) -> list[dict[str, object]]:
    records = []
    for candidate in sorted(stage.rglob("*"), key=lambda item: item.relative_to(stage).as_posix()):
        if candidate.is_file() and candidate.name != MANIFEST_NAME:
            records.append({
                "path": candidate.relative_to(stage).as_posix(),
                "size": candidate.stat().st_size,
                "sha256": _file_sha(candidate),
            })
    return records


def _manifest_data(stage: Path, contract: DistributionContract) -> dict[str, object]:
    records = _records(stage)
    identity_payload = json.dumps(records, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return {
        "schema_version": 1,
        "plugin_id": contract.plugin_id,
        "version": contract.version,
        "file_count": len(records),
        "total_bytes": sum(int(item["size"]) for item in records),
        "content_sha256": sha256(identity_payload).hexdigest(),
        "files": records,
    }


def build_package(contract: DistributionContract, output: Path) -> BuildResult:
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    validate_contract(contract, contract.source_root)
    with TemporaryDirectory(prefix=f".{contract.plugin_id}-", dir=output.parent) as temporary:
        stage = Path(temporary) / contract.plugin_id
        stage.mkdir()
        for source, relative in _declared_sources(contract):
            _copy_file(source, stage / relative, relative)
        _render_bootstrap(stage)
        _write_package_json(contract, stage)
        _apply_overlay(contract, stage)
        _audit(stage, contract)
        _run_product_audit(stage, contract)
        manifest = _manifest_data(stage, contract)
        (stage / MANIFEST_NAME).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        backup = output.with_name(f".{output.name}.previous")
        _remove_tree(backup)
        if output.exists():
            os.replace(output, backup)
        try:
            os.replace(stage, output)
        except Exception:
            if backup.exists() and not output.exists():
                os.replace(backup, output)
            raise
        _remove_tree(backup)
    return BuildResult(output, int(manifest["file_count"]), int(manifest["total_bytes"]), str(manifest["content_sha256"]))


def verify_package(contract: DistributionContract, output: Path) -> BuildResult:
    output = Path(output).resolve()
    try:
        recorded = json.loads((output / MANIFEST_NAME).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PackageAuditError("content_manifest_invalid", str(output)) from exc
    _audit(output, contract)
    actual = _manifest_data(output, contract)
    if recorded != actual:
        raise PackageAuditError("content_manifest_mismatch", str(output))
    return BuildResult(output, int(actual["file_count"]), int(actual["total_bytes"]), str(actual["content_sha256"]))
