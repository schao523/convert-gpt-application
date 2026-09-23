"""Verify every configured GPT-application conversion without publishing it."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable, Iterable, Mapping, Sequence
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from obvious_one_plugin_framework.verification import (  # noqa: E402
    ApplicationConfig,
    ExpansionContext,
    GateResult,
    RESULT_STATES,
    VerificationConfigError,
    aggregate_state,
    discover_applications,
    expand_argv,
    resolve_within,
    select_applications,
)
from obvious_one_plugin_framework.provenance import (  # noqa: E402
    ProvenanceError,
    validate_provenance,
)


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
_DIFFERENCE_KEYS = ("missing", "unexpected", "digest_mismatch")


@dataclass(frozen=True)
class RunContext:
    repository_root: Path
    diagnostics: Path
    python: str
    marketplace: Path | None = None
    provenance_override: Path | None = None
    command_runner: CommandRunner = subprocess.run


@dataclass(frozen=True)
class ApplicationResult:
    application_id: str
    state: str
    gates: tuple[GateResult, ...]
    artifacts: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.state not in RESULT_STATES:
            raise ValueError(f"invalid result state: {self.state}")

    def to_dict(self) -> dict[str, object]:
        return {
            "application_id": self.application_id,
            "state": self.state,
            "gates": [_gate_dict(gate) for gate in self.gates],
            "artifacts": dict(sorted(self.artifacts.items())),
        }


@dataclass(frozen=True)
class VerificationReport:
    state: str
    diagnostics: Path
    report_path: Path
    shared_gates: tuple[GateResult, ...]
    applications: tuple[ApplicationResult, ...]

    def __post_init__(self) -> None:
        if self.state not in RESULT_STATES:
            raise ValueError(f"invalid result state: {self.state}")

    def to_dict(self, repository_root: Path | None = None) -> dict[str, object]:
        root = (repository_root or ROOT).resolve()
        return {
            "state": self.state,
            "diagnostics": _display_path(self.diagnostics, root),
            "shared_gates": [_gate_dict(gate) for gate in self.shared_gates],
            "applications": [result.to_dict() for result in self.applications],
        }


def _gate_dict(gate: GateResult) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": gate.gate_id,
        "state": gate.state,
        "detail": gate.detail,
    }
    if gate.log_path is not None:
        payload["log"] = gate.log_path
    if gate.data:
        payload["data"] = dict(gate.data)
    return payload


def _display_path(path: Path, repository_root: Path) -> str:
    resolved = Path(path).resolve()
    resolved_repository = Path(repository_root).resolve()
    if resolved.is_relative_to(resolved_repository):
        return resolved.relative_to(resolved_repository).as_posix()
    return resolved.name


def _digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _inventory(root: Path, excluded: set[str]) -> dict[str, str]:
    if not root.is_dir():
        return {}
    result: dict[str, str] = {}
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(root).as_posix()
        if relative in excluded:
            continue
        result[relative] = _digest(candidate)
    return result


def compare_trees(
    expected: Path,
    actual: Path,
    excluded: set[str] | None = None,
) -> dict[str, list[str]]:
    """Return stable, machine-readable path and digest differences."""

    omitted = excluded or set()
    expected_files = _inventory(Path(expected), omitted)
    actual_files = _inventory(Path(actual), omitted)
    expected_paths = set(expected_files)
    actual_paths = set(actual_files)
    return {
        "missing": sorted(expected_paths - actual_paths),
        "unexpected": sorted(actual_paths - expected_paths),
        "digest_mismatch": sorted(
            path
            for path in expected_paths & actual_paths
            if expected_files[path] != actual_files[path]
        ),
    }


def _tree_identity(root: Path, excluded: set[str] | None = None) -> str:
    inventory = _inventory(root, excluded or set())
    digest = sha256()
    for path, value in sorted(inventory.items()):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(value.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{timestamp}-{os.getpid()}-{uuid4().hex[:8]}"


def _base_environment(repository_root: Path) -> dict[str, str]:
    environment = dict(os.environ)
    source = str(repository_root / "src")
    current = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = source if not current else os.pathsep.join((source, current))
    environment["PYTHONUTF8"] = "1"
    return environment


def _safe_log_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "gate"


def _run_gate(
    context: RunContext,
    gate_id: str,
    command: Sequence[str],
    *,
    environment: Mapping[str, str] | None = None,
    log_directory: Path | None = None,
) -> GateResult:
    log_root = log_directory or context.diagnostics / "logs"
    log_root.mkdir(parents=True, exist_ok=True)
    log = log_root / f"{_safe_log_name(gate_id)}.log"
    completed = context.command_runner(
        list(command),
        cwd=context.repository_root,
        env=dict(environment or _base_environment(context.repository_root)),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        shell=False,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    log.write_text(output, encoding="utf-8")
    if completed.returncode:
        return GateResult(
            gate_id,
            "FAIL",
            f"command exited {completed.returncode}",
            _display_path(log, context.repository_root),
        )
    return GateResult(
        gate_id,
        "PASS",
        "command passed",
        _display_path(log, context.repository_root),
    )


def run_shared_gates(context: RunContext) -> list[GateResult]:
    """Run repository and framework gates once per invocation."""

    python = context.python
    commands = (
        ("repository-layout", [python, "-B", "-m", "unittest", "tests.test_repository_layout", "-v"]),
        ("extraction-boundary", [python, "-B", "-m", "unittest", "tests.test_extraction_boundary", "-v"]),
        ("framework-tests", [python, "-B", "-m", "unittest", "discover", "-s", "tests/framework", "-v"]),
        ("application-config", [python, "-B", "-m", "unittest", "tests.test_application_config", "-v"]),
    )
    return [_run_gate(context, gate_id, command) for gate_id, command in commands]


def _expansion_context(
    config: ApplicationConfig,
    context: RunContext,
    application_diagnostics: Path,
) -> ExpansionContext:
    return ExpansionContext(
        python=context.python,
        repository_root=context.repository_root,
        application_root=config.root,
        diagnostics=application_diagnostics,
        plugin_id=config.plugin_id,
        application_id=config.application_id,
        version=config.version,
    )


def _skipped(gate_id: str, reason: str) -> GateResult:
    return GateResult(gate_id, "NOT VERIFIED", reason)


def _load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationConfigError(f"{path}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise VerificationConfigError(f"{path}: must contain an object")
    return value


def _provenance_gate(config: ApplicationConfig, context: RunContext) -> GateResult:
    path = context.provenance_override or config.source_inventory
    try:
        validate_provenance(_load_json(path), config)
    except (ProvenanceError, VerificationConfigError) as exc:
        return GateResult("provenance", "FAIL", str(exc))
    return GateResult("provenance", "PASS", "application provenance is valid")


def _git_output(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        shell=False,
        check=False,
    )
    if completed.returncode:
        raise VerificationConfigError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def _approved_delta(
    name: str,
    report: dict[str, list[str]],
    approved: Mapping[str, object],
) -> bool:
    expected = approved.get(name)
    if not isinstance(expected, dict):
        return False
    normalized = {
        key: sorted(str(item) for item in expected.get(key, []))
        for key in _DIFFERENCE_KEYS
    }
    return report == normalized


def _marketplace_gate(
    config: ApplicationConfig,
    context: RunContext,
    expansion: ExpansionContext,
    codex_artifact: Path,
    openclaw_artifact: Path,
) -> GateResult:
    profile = config.verification.marketplace
    if profile is None:
        return GateResult("marketplace", "NOT APPLICABLE", "application is not published")
    if context.marketplace is None:
        return GateResult("marketplace", "NOT VERIFIED", "marketplace was not supplied")
    marketplace = context.marketplace.resolve()
    if not marketplace.is_dir():
        return GateResult("marketplace", "FAIL", "marketplace directory does not exist")
    try:
        status = _git_output(marketplace, "status", "--short")
        if status:
            return GateResult("marketplace", "FAIL", "marketplace working tree is not clean")
        commit = _git_output(marketplace, "rev-parse", "HEAD")
        provenance = _load_json(context.provenance_override or config.source_inventory)
        recorded_commit = provenance.get("marketplace_commit")
        if recorded_commit is not None and recorded_commit != commit:
            return GateResult("marketplace", "FAIL", "marketplace commit differs from provenance")
        codex_path = expand_argv((profile.codex_path,), expansion)[0]
        openclaw_path = expand_argv((profile.openclaw_path,), expansion)[0]
        published_codex = resolve_within(marketplace, codex_path, field="marketplace.codex_path")
        published_openclaw = resolve_within(
            marketplace, openclaw_path, field="marketplace.openclaw_path"
        )
        codex_delta = compare_trees(codex_artifact, published_codex)
        openclaw_delta = compare_trees(
            openclaw_artifact, published_openclaw, {"CONTENT-MANIFEST.json"}
        )
        approved = _load_json(profile.approved_delta)
        if approved.get("marketplace_commit") != commit:
            return GateResult("marketplace", "FAIL", "approved delta belongs to another commit")
        data = {"commit": commit, "codex": codex_delta, "openclaw": openclaw_delta}
        if not _approved_delta("codex", codex_delta, approved):
            return GateResult("marketplace", "FAIL", "Codex marketplace delta is not approved", data=data)
        if not _approved_delta("openclaw", openclaw_delta, approved):
            return GateResult("marketplace", "FAIL", "OpenClaw marketplace delta is not approved", data=data)
        return GateResult(
            "marketplace",
            "PASS",
            "published artifacts match the approved boundary",
            data=data,
        )
    except VerificationConfigError as exc:
        return GateResult("marketplace", "FAIL", str(exc))


def run_application(config: ApplicationConfig, context: RunContext) -> ApplicationResult:
    """Run independent and dependency-ordered gates for one application."""

    application_diagnostics = context.diagnostics / "applications" / config.application_id
    application_diagnostics.mkdir(parents=True, exist_ok=True)
    logs = application_diagnostics / "logs"
    expansion = _expansion_context(config, context, application_diagnostics)
    gates: list[GateResult] = [_provenance_gate(config, context)]

    gates.append(
        _run_gate(
            context,
            "product-tests",
            [context.python, "-B", "-m", "unittest", "discover", "-s", str(config.verification.test_directory), "-v"],
            log_directory=logs,
        )
    )
    for command in config.verification.commands:
        environment = _base_environment(context.repository_root)
        for name in tuple(environment):
            if any(name.startswith(prefix) for prefix in command.clean_environment_prefixes):
                del environment[name]
        gates.append(
            _run_gate(
                context,
                command.command_id,
                expand_argv(command.argv, expansion),
                environment=environment,
                log_directory=logs,
            )
        )

    codex_gate = _run_gate(
        context,
        "codex-build",
        expand_argv(config.verification.codex_build.argv, expansion),
        log_directory=logs,
    )
    gates.append(codex_gate)
    codex_root = application_diagnostics / "codex-marketplace"
    artifact_relative = expand_argv((config.verification.codex_build.artifact_path,), expansion)[0]
    codex_artifact = resolve_within(codex_root, artifact_relative, field="codex artifact")

    openclaw_a = application_diagnostics / "openclaw-a" / config.plugin_id
    openclaw_b = application_diagnostics / "openclaw-b" / config.plugin_id
    build_gates: list[GateResult] = []
    for gate_id, output in (("openclaw-build-a", openclaw_a), ("openclaw-build-b", openclaw_b)):
        result = _run_gate(
            context,
            gate_id,
            [context.python, "-B", "-m", "obvious_one_plugin_framework.cli", "build-package", "--contract", str(config.distribution_contract), "--output", str(output), "--json"],
            log_directory=logs,
        )
        build_gates.append(result)
        gates.append(result)

    if build_gates[0].state == "PASS":
        verify_gate = _run_gate(
            context,
            "openclaw-verify",
            [context.python, "-B", "-m", "obvious_one_plugin_framework.cli", "verify", "--contract", str(config.distribution_contract), "--output", str(openclaw_a), "--json"],
            log_directory=logs,
        )
    else:
        verify_gate = _skipped("openclaw-verify", "openclaw-build-a failed")
    gates.append(verify_gate)

    if all(gate.state == "PASS" for gate in build_gates):
        differences = compare_trees(openclaw_a, openclaw_b)
        deterministic_gate = GateResult(
            "openclaw-determinism",
            "PASS" if not any(differences.values()) else "FAIL",
            "builds are byte-identical" if not any(differences.values()) else "builds differ",
            data={"differences": differences},
        )
    else:
        deterministic_gate = _skipped("openclaw-determinism", "both OpenClaw builds must pass")
    gates.append(deterministic_gate)

    prerequisites_pass = codex_gate.state == "PASS" and build_gates[0].state == "PASS" and verify_gate.state == "PASS"
    if prerequisites_pass:
        gates.append(_marketplace_gate(config, context, expansion, codex_artifact, openclaw_a))
    elif config.verification.marketplace is None:
        gates.append(GateResult("marketplace", "NOT APPLICABLE", "application is not published"))
    else:
        gates.append(_skipped("marketplace", "artifact prerequisites failed"))

    artifacts: dict[str, str] = {}
    if codex_gate.state == "PASS" and codex_artifact.is_dir():
        artifacts["codex"] = _display_path(codex_artifact, context.repository_root)
        artifacts["codex_content_sha256"] = _tree_identity(codex_artifact)
    if build_gates[0].state == "PASS" and openclaw_a.is_dir():
        artifacts["openclaw"] = _display_path(openclaw_a, context.repository_root)
        artifacts["openclaw_content_sha256"] = _tree_identity(openclaw_a)

    return ApplicationResult(
        application_id=config.application_id,
        state=aggregate_state(gates),
        gates=tuple(gates),
        artifacts=artifacts,
    )


def write_report(
    context: RunContext,
    shared: Sequence[GateResult],
    applications: Sequence[ApplicationResult],
) -> VerificationReport:
    state = "FAIL" if aggregate_state(shared) == "FAIL" or any(
        application.state == "FAIL" for application in applications
    ) else "PASS"
    report_path = context.diagnostics / "report.json"
    report = VerificationReport(
        state=state,
        diagnostics=context.diagnostics,
        report_path=report_path,
        shared_gates=tuple(shared),
        applications=tuple(applications),
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_dict(context.repository_root), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify(
    *,
    repository_root: Path,
    application_id: str | None = None,
    select_all: bool = False,
    marketplace: Path | None = None,
    provenance_override: Path | None = None,
    command_runner: CommandRunner = subprocess.run,
) -> VerificationReport:
    """Verify selected applications and return a combined local report."""

    repository = Path(repository_root).resolve()
    configs = discover_applications(repository)
    selected = select_applications(configs, application_id=application_id, select_all=select_all)
    if provenance_override is not None:
        if len(selected) != 1:
            raise VerificationConfigError("--provenance requires exactly one application")
        resolved_provenance = Path(provenance_override).resolve()
        if not resolved_provenance.is_relative_to(repository):
            raise VerificationConfigError("provenance: path escapes repository")
        provenance_override = resolved_provenance
    diagnostics = repository / ".tmp" / "verification" / _run_id()
    diagnostics.mkdir(parents=True, exist_ok=False)
    context = RunContext(
        repository_root=repository,
        diagnostics=diagnostics,
        python=sys.executable,
        marketplace=Path(marketplace).resolve() if marketplace is not None else None,
        provenance_override=provenance_override,
        command_runner=command_runner,
    )
    shared = run_shared_gates(context)
    applications: list[ApplicationResult] = []
    if aggregate_state(shared) == "FAIL":
        for config in selected:
            applications.append(
                ApplicationResult(
                    application_id=config.application_id,
                    state="NOT VERIFIED",
                    gates=(_skipped("application-verification", "a shared verification gate failed"),),
                )
            )
    else:
        for config in selected:
            applications.append(run_application(config, context))
    return write_report(context, shared, applications)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--all", action="store_true", help="verify all applications")
    selection.add_argument("--application", help="verify one application ID")
    parser.add_argument("--marketplace", type=Path)
    parser.add_argument("--provenance", type=Path)
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    options = build_parser().parse_args(arguments)
    try:
        report = verify(
            repository_root=ROOT,
            application_id=options.application,
            select_all=options.all,
            marketplace=options.marketplace.resolve() if options.marketplace else None,
            provenance_override=options.provenance.resolve() if options.provenance else None,
        )
    except (OSError, VerificationConfigError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print(f"{report.state} verification report: {report.report_path}")
    return 0 if report.state == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
