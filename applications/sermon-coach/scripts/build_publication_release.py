#!/usr/bin/env python3
"""Build the approved sermon-coach 1.0.3 publication normalization."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

from obvious_one_plugin_framework import plugin_authoring
from obvious_one_plugin_framework.plugin_onboarding import OnboardingError, RepairResult


APPLICATION_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = APPLICATION_ROOT / "normalization" / "publication-normalization-v1.json"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_LAYERS = (
    "installation",
    "skill_invocation",
    "capability_discovery",
    "operation_execution",
    "result_delivery",
    "conversation",
)


def _fail(code: str, detail: str = "") -> OnboardingError:
    return OnboardingError(f"sermon_coach.normalization.{code}", "FAIL", detail)


def _canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def _tree_identity(members: list[dict[str, object]]) -> str:
    encoded = json.dumps(
        members, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return sha256(encoded).hexdigest()


def _load_contract(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail("contract_invalid") from exc
    keys = {
        "schema", "plugin_id", "version", "source_archive_sha256",
        "source_manifest_schema", "source_content_tree_sha256_claim",
        "source_content_tree_sha256_recomputed", "source_content_tree_disposition",
        "skill_local_document_bindings",
        "license", "copyright_year",
        "copyright_holder", "approval_record", "third_party_sources",
    }
    if not isinstance(payload, dict) or set(payload) != keys:
        raise _fail("contract_invalid")
    if payload["schema"] != "sermon-coach-publication-normalization-v1":
        raise _fail("contract_schema_invalid")
    if payload["plugin_id"] != "sermon-coach" or payload["version"] != "1.0.3":
        raise _fail("contract_identity_invalid")
    if payload["license"] != "MIT" or payload["copyright_year"] != 2026 or payload["copyright_holder"] != "SC":
        raise _fail("license_decision_invalid")
    digest = payload["source_archive_sha256"]
    if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
        raise _fail("source_digest_invalid")
    for key in (
        "source_content_tree_sha256_claim",
        "source_content_tree_sha256_recomputed",
    ):
        value = payload[key]
        if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
            raise _fail("source_content_tree_decision_invalid")
    if payload["source_content_tree_disposition"] != "SUPERSEDED_BY_EXACT_MEMBER_CLOSURE":
        raise _fail("source_content_tree_decision_invalid")
    bindings = payload["skill_local_document_bindings"]
    if not isinstance(bindings, dict) or set(bindings) != {"skills", "documents"}:
        raise _fail("skill_local_document_bindings_invalid")
    skills = bindings["skills"]
    documents = bindings["documents"]
    if (
        not isinstance(skills, list)
        or not skills
        or any(not isinstance(item, str) or not item or "/" in item or "\\" in item for item in skills)
        or len(skills) != len(set(skills))
        or not isinstance(documents, list)
        or not documents
    ):
        raise _fail("skill_local_document_bindings_invalid")
    document_paths: list[str] = []
    for item in documents:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise _fail("skill_local_document_bindings_invalid")
        relative = item["path"]
        digest_value = item["sha256"]
        if (
            not isinstance(relative, str)
            or not relative.startswith("docs/")
            or "\\" in relative
            or any(part in {"", ".", ".."} for part in PurePosixPath(relative).parts)
            or not isinstance(digest_value, str)
            or _DIGEST.fullmatch(digest_value) is None
        ):
            raise _fail("skill_local_document_bindings_invalid")
        document_paths.append(relative)
    if len(document_paths) != len(set(document_paths)):
        raise _fail("skill_local_document_bindings_invalid")
    approval = payload["approval_record"]
    if (
        not isinstance(approval, dict)
        or set(approval) != {"decision", "confirmed_by", "recorded_at"}
        or approval.get("decision") != "APPROVED"
        or not all(isinstance(approval.get(key), str) and approval[key].strip() for key in ("confirmed_by", "recorded_at"))
    ):
        raise _fail("approval_required")
    sources = payload["third_party_sources"]
    if not isinstance(sources, list) or not sources:
        raise _fail("third_party_sources_invalid")
    seen: set[str] = set()
    for item in sources:
        if not isinstance(item, dict) or set(item) != {"reference_id", "path", "sha256", "rights_basis"}:
            raise _fail("third_party_source_invalid")
        reference_id = item["reference_id"]
        relative = item["path"]
        if not isinstance(reference_id, str) or not reference_id or reference_id in seen:
            raise _fail("third_party_source_invalid")
        seen.add(reference_id)
        if not isinstance(relative, str) or "\\" in relative:
            raise _fail("third_party_source_invalid")
        portable = PurePosixPath(relative)
        if portable.is_absolute() or any(part in {"", ".", ".."} for part in portable.parts):
            raise _fail("third_party_source_invalid")
        if not isinstance(item["sha256"], str) or _DIGEST.fullmatch(item["sha256"]) is None:
            raise _fail("third_party_source_invalid")
        if not isinstance(item["rights_basis"], str) or not item["rights_basis"].strip():
            raise _fail("third_party_source_invalid")
    return payload


def _license() -> bytes:
    return b"""MIT License

Copyright (c) 2026 SC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the \"Software\"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def _notice(contract: dict[str, object]) -> bytes:
    approval = contract["approval_record"]
    lines = [
        "# Third-Party Notices",
        "",
        "The decision owner reviewed and approved inclusion and public redistribution",
        "of the following source materials in this plugin release. This notice records",
        "that authorization without changing the sources' underlying ownership.",
        "",
        f"Confirmed by: {approval['confirmed_by']}",
        f"Recorded at: {approval['recorded_at']}",
        "",
    ]
    for item in contract["third_party_sources"]:
        lines.extend(
            [
                f"## {item['reference_id']}",
                "",
                f"- Path: `{item['path']}`",
                f"- SHA-256: `{item['sha256']}`",
                f"- Rights basis: {item['rights_basis']}",
                "",
            ]
        )
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _validate_source(root: Path, contract: dict[str, object]) -> bytes:
    source_manifest = root / "PLUGIN-BUILDER-MANIFEST.json"
    try:
        source_bytes = source_manifest.read_bytes()
        payload = json.loads(source_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail("source_manifest_invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema") != contract["source_manifest_schema"]:
        raise _fail("source_manifest_schema_mismatch")
    actual = [
        asdict(member)
        for member in plugin_authoring.tree_manifest(root)
        if member.path != "PLUGIN-BUILDER-MANIFEST.json"
    ]
    claimed = payload.get("members")
    if (
        not isinstance(claimed, list)
        or any(not isinstance(item, dict) or set(item) != {"path", "size", "sha256"} for item in claimed)
        or sorted(claimed, key=lambda item: item["path"])
        != sorted(actual, key=lambda item: item["path"])
    ):
        raise _fail("source_member_manifest_mismatch")
    expected = sorted([item["path"] for item in actual] + ["PLUGIN-BUILDER-MANIFEST.json"])
    claimed_expected = payload.get("expected_members")
    if (
        not isinstance(claimed_expected, list)
        or any(not isinstance(item, str) for item in claimed_expected)
        or len(claimed_expected) != len(set(claimed_expected))
        or set(claimed_expected) != set(expected)
    ):
        raise _fail("source_expected_members_mismatch")
    claimed_tree = payload.get("content_tree_sha256")
    recomputed_tree = _tree_identity(actual)
    if claimed_tree != contract["source_content_tree_sha256_claim"]:
        raise _fail("source_content_tree_claim_mismatch")
    if recomputed_tree != contract["source_content_tree_sha256_recomputed"]:
        raise _fail("source_content_tree_recomputed_mismatch")
    identities = []
    for relative in ("plugin.json", ".codex-plugin/plugin.json"):
        try:
            manifest = json.loads((root / relative).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise _fail("plugin_manifest_invalid", relative) from exc
        author = manifest.get("author")
        identities.append((manifest.get("name"), manifest.get("version"), author.get("name") if isinstance(author, dict) else author))
    if identities != [("sermon-coach", "1.0.3", "SC")] * 2:
        raise _fail("plugin_identity_mismatch")
    for item in contract["third_party_sources"]:
        target = root.joinpath(*PurePosixPath(item["path"]).parts)
        if not target.is_file() or sha256(target.read_bytes()).hexdigest() != item["sha256"]:
            raise _fail("third_party_source_mismatch", item["reference_id"])
    for relative in (
        "LICENSE", "THIRD_PARTY_NOTICES.md", "WORKBENCH-REPAIR-MANIFEST.json",
        "docs/provenance/source-PLUGIN-BUILDER-MANIFEST.json",
    ):
        if (root / relative).exists():
            raise _fail("publication_control_collision", relative)
    return source_bytes


def _publish_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise _fail("output_exists", destination.name)
    handle, name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(handle)
    staged = Path(name)
    try:
        shutil.copyfile(source, staged)
        os.replace(staged, destination)
    finally:
        staged.unlink(missing_ok=True)


def _repair_skill_local_documents(root: Path, contract: dict[str, object]) -> list[dict[str, object]]:
    bindings = contract["skill_local_document_bindings"]
    documents: list[tuple[str, bytes, str]] = []
    for item in bindings["documents"]:
        relative = item["path"]
        source = root.joinpath(*PurePosixPath(relative).parts)
        if not source.is_file():
            raise _fail("skill_local_document_missing", relative)
        content = source.read_bytes()
        if sha256(content).hexdigest() != item["sha256"]:
            raise _fail("skill_local_document_mismatch", relative)
        documents.append((relative, content, item["sha256"]))
    repairs: list[dict[str, object]] = []
    for skill_name in bindings["skills"]:
        skill_root = root / "skills" / skill_name
        skill_path = skill_root / "SKILL.md"
        if not skill_path.is_file():
            raise _fail("skill_local_document_skill_missing", skill_name)
        skill_bytes = skill_path.read_bytes()
        rewritten = skill_bytes
        copied: list[dict[str, str]] = []
        for relative, content, digest_value in documents:
            old = f"../../{relative}".encode("utf-8")
            new = f"assets/{relative}".encode("utf-8")
            if old not in rewritten:
                raise _fail("skill_local_document_binding_missing", f"{skill_name}:{relative}")
            rewritten = rewritten.replace(old, new)
            destination = skill_root.joinpath("assets", *PurePosixPath(relative).parts)
            if destination.exists():
                raise _fail("skill_local_document_collision", f"{skill_name}:{relative}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            copied.append({"path": destination.relative_to(root).as_posix(), "sha256": digest_value})
        skill_path.write_bytes(rewritten)
        repairs.append(
            {
                "skill": skill_name,
                "skill_sha256_before": sha256(skill_bytes).hexdigest(),
                "skill_sha256_after": sha256(rewritten).hexdigest(),
                "copied_documents": copied,
            }
        )
    return repairs


def _offline_validators(
    root: Path, source_manifest_bytes: bytes
) -> list[dict[str, object]]:
    try:
        source_manifest = json.loads(source_manifest_bytes)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise _fail("source_tool_declarations_invalid") from exc
    contracts = source_manifest.get("tool_contracts")
    bindings = source_manifest.get("tool_bindings")
    if not isinstance(contracts, list) or bindings != []:
        raise _fail("source_tool_declarations_invalid")
    validators: list[dict[str, object]] = []
    identifiers: set[str] = set()
    for source_contract in contracts:
        if not isinstance(source_contract, dict):
            raise _fail("source_tool_declarations_invalid")
        identifier = source_contract.get("id")
        files = source_contract.get("files")
        skill_bindings = source_contract.get("skill_bindings")
        if (
            not isinstance(identifier, str)
            or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier) is None
            or identifier in identifiers
            or source_contract.get("implementation_kind") != "BUNDLED_LOCAL"
            or source_contract.get("required") is not False
            or skill_bindings != []
            or not isinstance(files, list)
            or not files
        ):
            raise _fail("source_offline_validator_invalid", str(identifier or ""))
        normalized_files: list[str] = []
        for relative in files:
            if (
                not isinstance(relative, str)
                or PurePosixPath(relative).is_absolute()
                or any(part in {"", ".", ".."} for part in PurePosixPath(relative).parts)
                or not root.joinpath(*PurePosixPath(relative).parts).is_file()
            ):
                raise _fail("source_offline_validator_file_invalid", str(relative))
            normalized_files.append(relative)
        identifiers.add(identifier)
        validators.append(
            {
                "id": identifier,
                "files": normalized_files,
                "runtime_role": "OFFLINE_PACKAGE_VALIDATION_ONLY",
                "required": False,
                "installed_runtime_callable": False,
                "source_contract_sha256": sha256(
                    _canonical(source_contract)
                ).hexdigest(),
            }
        )
    return validators


def build_publication_release(source: Path, output_root: Path, contract_path: Path = CONTRACT_PATH) -> RepairResult:
    contract = _load_contract(contract_path)
    inventory = plugin_authoring.inventory_archive(source)
    if inventory.archive_sha256 != contract["source_archive_sha256"]:
        raise _fail("source_digest_mismatch")
    with tempfile.TemporaryDirectory(prefix="sermon-coach-publication-") as name:
        temporary = Path(name)
        extracted = temporary / "source"
        plugin_authoring.extract_archive(source, extracted)
        located = plugin_authoring.locate_plugin_archive_root(extracted)
        if located.profile != "LEGACY_FLAT":
            raise _fail("source_profile_invalid")
        root = located.path
        source_manifest_bytes = _validate_source(root, contract)
        offline_validators = _offline_validators(root, source_manifest_bytes)
        document_repairs = _repair_skill_local_documents(root, contract)
        provenance = root / "docs" / "provenance" / "source-PLUGIN-BUILDER-MANIFEST.json"
        provenance.parent.mkdir(parents=True)
        provenance.write_bytes(source_manifest_bytes)
        (root / "PLUGIN-BUILDER-MANIFEST.json").unlink()
        (root / "LICENSE").write_bytes(_license())
        (root / "THIRD_PARTY_NOTICES.md").write_bytes(_notice(contract))
        before_repair = [asdict(member) for member in plugin_authoring.tree_manifest(root)]
        repair_manifest = {
            "schema": "workbench-repair-manifest-v1",
            "plugin_id": contract["plugin_id"],
            "source_version": contract["version"],
            "target_version": contract["version"],
            "source_archive_sha256": contract["source_archive_sha256"],
            "source_manifest_schema": contract["source_manifest_schema"],
            "source_manifest_sha256": sha256(source_manifest_bytes).hexdigest(),
            "source_content_tree_sha256_claim": contract["source_content_tree_sha256_claim"],
            "source_content_tree_sha256_recomputed": contract["source_content_tree_sha256_recomputed"],
            "source_content_tree_disposition": contract["source_content_tree_disposition"],
            "approval_record": contract["approval_record"],
            "third_party_sources": contract["third_party_sources"],
            "skill_local_document_repairs": document_repairs,
            "tool_bindings": [],
            "tool_contracts": [],
            "offline_validators": offline_validators,
            "content_members": before_repair,
            "content_tree_sha256": plugin_authoring.tree_sha256(root),
        }
        (root / "WORKBENCH-REPAIR-MANIFEST.json").write_bytes(_canonical(repair_manifest))
        issues = plugin_authoring.validate_plugin_tree(root)
        if issues:
            raise _fail("candidate_invalid", f"{issues[0].code}:{issues[0].path}")
        staged_archive = temporary / "sermon-coach-1.0.3.zip"
        archive_sha256 = plugin_authoring.write_deterministic_zip(root, staged_archive)
        repaired_inventory = plugin_authoring.inventory_archive(staged_archive)
        members = [asdict(member) for member in repaired_inventory.members]
        repair_member = next(item for item in repaired_inventory.members if item.path == "WORKBENCH-REPAIR-MANIFEST.json")
        metadata_payload = {
            "schema": "workbench-repaired-plugin-v2",
            "plugin_id": "sermon-coach",
            "version": "1.0.3",
            "archive_sha256": archive_sha256,
            "source_archive_sha256": inventory.archive_sha256,
            "member_manifest_sha256": sha256(_canonical(members)).hexdigest(),
            "content_tree_sha256": plugin_authoring.tree_sha256(root),
            "members": members,
            "input_profile": "PLUGIN_BUILDER_VERSIONED_LEGACY_V1",
            "envelope_profile": "LEGACY_FLAT",
            "manifest_profile": "PORTABLE_WITH_OPENAI_COMPATIBILITY",
            "repair_manifest_sha256": repair_member.sha256,
            "producer_claims": {
                "schema": contract["source_manifest_schema"],
                "verification_state": "NOT VERIFIED",
                "source_archive_sha256": inventory.archive_sha256,
            },
            "evidence_states": {layer: "NOT VERIFIED" for layer in _LAYERS},
            "extracted_validation": {"state": "PASS", "diagnostics": []},
            "safety_validation": {"state": "PASS", "diagnostics": []},
            "tool_bindings": [],
            "tool_contracts_sha256": sha256(_canonical([])).hexdigest(),
            "offline_validators": offline_validators,
            "offline_validators_sha256": sha256(
                _canonical(offline_validators)
            ).hexdigest(),
        }
        staged_metadata = temporary / "package-metadata.json"
        staged_metadata.write_bytes(_canonical(metadata_payload))
        output = Path(output_root)
        archive = output / "sermon-coach-1.0.3.zip"
        metadata = output / "package-metadata.json"
        _publish_file(staged_archive, archive)
        try:
            _publish_file(staged_metadata, metadata)
        except BaseException:
            archive.unlink(missing_ok=True)
            raise
    return RepairResult(
        archive=archive,
        metadata=metadata,
        archive_sha256=archive_sha256,
        member_manifest_sha256=metadata_payload["member_manifest_sha256"],
        source_archive_sha256=inventory.archive_sha256,
    )
