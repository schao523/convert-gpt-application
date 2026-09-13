"""Verify the controlled GPT-application repository extraction.

The verifier is deliberately read-only outside ``.tmp/verification``. It builds
fresh Codex and OpenClaw artifacts, checks them, and compares them with the
recorded public-marketplace baseline without modifying that marketplace.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
APPLICATION = ROOT / "applications" / "cool-bible-tutor"
VERSION = "2.4.6"
DIAGNOSTICS = ROOT / ".tmp" / "verification" / f"run-{os.getpid()}"


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


def compare_trees(expected: Path, actual: Path, excluded: set[str]) -> dict[str, list[str]]:
    """Return stable, machine-readable path and digest differences."""

    expected_files = _inventory(Path(expected), excluded)
    actual_files = _inventory(Path(actual), excluded)
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


def _run(name: str, command: list[str], *, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    log = DIAGNOSTICS / "logs" / f"{name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(f"{name} failed ({completed.returncode}); see {log}")
    print(f"PASS {name}")
    return completed.stdout


def _git_output(repository: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repository), *arguments],
        text=True,
        encoding="utf-8",
    ).strip()


def _assert_clean(repository: Path, name: str) -> None:
    status = _git_output(repository, "status", "--short")
    if status:
        raise RuntimeError(f"{name} is not clean:\n{status}")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_approved_delta(
    name: str,
    report: dict[str, list[str]],
    approved: dict[str, object],
) -> None:
    expected = approved.get(name)
    if not isinstance(expected, dict):
        raise RuntimeError(f"approved delta is missing {name}")
    normalized = {
        key: sorted(str(item) for item in expected.get(key, []))
        for key in ("missing", "unexpected", "digest_mismatch")
    }
    if report != normalized:
        raise RuntimeError(f"{name} marketplace delta is not approved")


def _write_report(payload: dict[str, object]) -> None:
    path = DIAGNOSTICS / "equivalence.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify(marketplace: Path, provenance_path: Path) -> None:
    DIAGNOSTICS.mkdir(parents=True)

    python = sys.executable
    _run("repository-layout", [python, "-B", "-m", "unittest", "tests.test_repository_layout", "-v"])
    _run("provenance", [python, "-B", "-m", "unittest", "tests.test_provenance", "-v"])
    _run("extraction-boundary", [python, "-B", "-m", "unittest", "tests.test_extraction_boundary", "-v"])
    _run("framework-tests", [python, "-B", "-m", "unittest", "discover", "-s", "tests/framework", "-v"])
    _run("application-config", [python, "-B", "-m", "unittest", "tests.test_application_config", "-v"])
    _run("product-tests", [python, "-B", "-m", "unittest", "discover", "-s", str(APPLICATION / "tests"), "-v"])
    _run("distribution-audit", [python, "-B", str(APPLICATION / "scripts" / "distribution_audit.py"), str(APPLICATION)])

    clean_env = os.environ.copy()
    for key in tuple(clean_env):
        if key.startswith("COOL_BIBLE_TUTOR_"):
            clean_env.pop(key)
    passage = _run(
        "exact-passage",
        [python, "-B", str(APPLICATION / "scripts" / "cool_bible_tutor.py"), "passage", "約 3:16", "--format", "json"],
        env=clean_env,
    )
    passage_data = json.loads(passage)
    verses = passage_data.get("verses", [])
    if (
        passage_data.get("trust_status") != "verified"
        or not verses
        or not all(verse.get("verified") for verse in verses)
        or "神愛世人" not in str(passage_data)
    ):
        raise RuntimeError("exact-passage did not return verified John 3:16")
    status = json.loads(_run(
        "runtime-status",
        [python, "-B", str(APPLICATION / "scripts" / "cool_bible_tutor.py"), "status", "--json"],
        env=clean_env,
    ))
    if (
        status.get("core_status") != "core_ready"
        or status.get("corpus_origin") != "bundled"
        or status.get("total_rows") != 31008
        or status.get("approved_source_gaps") != 71
        or status.get("unverified_rows") != 0
    ):
        raise RuntimeError("runtime-status did not report the production corpus")

    codex_root = DIAGNOSTICS / "codex-marketplace"
    _run(
        "codex-build",
        [python, "-B", str(APPLICATION / "scripts" / "build_marketplace_release.py"), "--source", str(APPLICATION), "--destination", str(codex_root), "--version", VERSION],
    )
    contract = APPLICATION / "openclaw" / "distribution.json"
    openclaw_a = DIAGNOSTICS / "openclaw-a" / "cool-bible-tutor"
    openclaw_b = DIAGNOSTICS / "openclaw-b" / "cool-bible-tutor"
    for label, output in (("openclaw-build-a", openclaw_a), ("openclaw-build-b", openclaw_b)):
        _run(label, [python, "-B", "-m", "obvious_one_plugin_framework.cli", "build-package", "--contract", str(contract), "--output", str(output), "--json"])
    _run("openclaw-verify", [python, "-B", "-m", "obvious_one_plugin_framework.cli", "verify", "--contract", str(contract), "--output", str(openclaw_a), "--json"])
    deterministic = compare_trees(openclaw_a, openclaw_b, excluded=set())
    if any(deterministic.values()):
        raise RuntimeError("OpenClaw builds are not deterministic")

    provenance = _load_json(provenance_path)
    _assert_clean(marketplace, "public marketplace")
    marketplace_commit = _git_output(marketplace, "rev-parse", "HEAD")
    if marketplace_commit != provenance.get("marketplace_commit"):
        raise RuntimeError("public marketplace commit differs from source provenance")

    codex_delta = compare_trees(
        codex_root / "plugins" / "cool-bible-tutor",
        marketplace / "plugins" / "cool-bible-tutor",
        excluded=set(),
    )
    openclaw_delta = compare_trees(
        openclaw_a,
        marketplace / "openclaw" / "cool-bible-tutor",
        excluded={"CONTENT-MANIFEST.json"},
    )
    report = {
        "marketplace_commit": marketplace_commit,
        "codex": codex_delta,
        "openclaw": openclaw_delta,
        "openclaw_deterministic": True,
    }
    _write_report(report)
    approved = _load_json(ROOT / "docs" / "provenance" / "marketplace-approved-delta.json")
    if approved.get("marketplace_commit") != marketplace_commit:
        raise RuntimeError("approved delta belongs to a different marketplace commit")
    _assert_approved_delta("codex", codex_delta, approved)
    _assert_approved_delta("openclaw", openclaw_delta, approved)
    print("PASS release-equivalence")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--marketplace", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path)
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    options = _parser().parse_args(arguments)
    try:
        verify(options.marketplace.resolve(), options.provenance.resolve())
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("PASS controlled extraction")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
