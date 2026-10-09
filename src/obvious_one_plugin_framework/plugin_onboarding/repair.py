"""Deterministic repair of approved legacy delegated-reference defects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile

from .. import plugin_authoring
from .contract import OnboardingError
from .repair_contract import DelegatedReferenceRepair


_LAYERS = (
    "installation",
    "skill_invocation",
    "capability_discovery",
    "operation_execution",
    "result_delivery",
    "conversation",
)
_MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\(\s*(?:<(?P<angle>[^>]+)>|(?P<plain>[^\s)]+))"
)


@dataclass(frozen=True)
class RepairResult:
    archive: Path
    metadata: Path
    archive_sha256: str
    member_manifest_sha256: str
    source_archive_sha256: str


def _fail(code: str, detail: str = "") -> OnboardingError:
    return OnboardingError(f"onboarding.repair.{code}", "FAIL", detail)


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("ascii")


def _load_json(path: Path, code: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail(code) from exc
    if not isinstance(payload, dict):
        raise _fail(code)
    return payload


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(value))


def _owner_asset(root: Path, contract: DelegatedReferenceRepair, relative: str) -> Path:
    return root / "skills" / contract.owner_skill / Path(*PurePosixPath(relative).parts)


def _remove_reference_links(text: str, blocked: set[str]) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        targets = {
            match.group("angle") or match.group("plain")
            for match in _MARKDOWN_LINK.finditer(line)
        }
        if any(target in blocked for target in targets):
            continue
        kept.append(line)
    return "\n".join(kept).rstrip() + "\n"


def _handoff_section(contract: DelegatedReferenceRepair) -> str:
    ids = " and ".join(reference.reference_id for reference in contract.references)
    return (
        "\n## Delegated reference handoff\n\n"
        f"- Access: HANDOFF to `{contract.owner_skill}` for {ids}.\n"
        "- Triggers: exact CUV quotation or verification; formal Bible study.\n"
        "- Input: pass the relevant passage, question, established session context, and requested output.\n"
        "- Return: the result returns to the response owner for the ongoing workflow.\n"
        "- Fallback: if the owner or references are unavailable, disclose the limitation and do not fabricate exact Scripture.\n"
    )


def _repair_non_owner(root: Path, skill_name: str, contract: DelegatedReferenceRepair) -> None:
    skill = root / "skills" / skill_name
    if not skill.is_dir():
        raise _fail("non_owner_skill_missing", skill_name)
    profile_path = skill / "assets" / "reference-profile.json"
    profile = _load_json(profile_path, "reference_profile_invalid")
    if profile.get("skill") != skill_name:
        raise _fail("reference_profile_identity_mismatch", skill_name)
    profile["schema"] = "skill-reference-profile-v2"
    blocked_profile_paths = {
        reference.owner_relative_path
        for reference in contract.references
    } | {
        f"assets/{reference.owner_relative_path}"
        for reference in contract.references
    }
    for field in ("required", "conditional", "optional"):
        value = profile.get(field)
        if not isinstance(value, list):
            raise _fail("reference_profile_invalid", f"{skill_name}:{field}")
        profile[field] = [item for item in value if item not in blocked_profile_paths]
    profile["delegated_references"] = [
        {
            "reference_id": reference.reference_id,
            "owner_skill": contract.owner_skill,
            "access_mode": "HANDOFF",
            "local_copy": False,
        }
        for reference in contract.references
    ]
    _write_json(profile_path, profile)

    index_path = skill / "assets" / "knowledge-index.json"
    index = _load_json(index_path, "knowledge_index_invalid")
    assets = index.get("assets")
    if not isinstance(assets, list):
        raise _fail("knowledge_index_invalid", skill_name)
    blocked_ids = {reference.reference_id for reference in contract.references}
    index["assets"] = [
        item
        for item in assets
        if not isinstance(item, dict) or item.get("id") not in blocked_ids
    ]
    _write_json(index_path, index)

    skill_path = skill / "SKILL.md"
    try:
        text = skill_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise _fail("skill_unreadable", skill_name) from exc
    blocked_links = {
        reference.owner_relative_path
        for reference in contract.references
    }
    text = _remove_reference_links(text, blocked_links)
    skill_path.write_text(
        text + _handoff_section(contract), encoding="utf-8", newline="\n"
    )


def _verify_identity(root: Path, contract: DelegatedReferenceRepair) -> tuple[dict[str, object], dict[str, object]]:
    portable = _load_json(root / "plugin.json", "portable_manifest_invalid")
    overlay = _load_json(root / ".codex-plugin" / "plugin.json", "compatibility_manifest_invalid")
    for payload in (portable, overlay):
        if payload.get("name") != contract.plugin_id:
            raise _fail("plugin_identity_mismatch")
        if payload.get("version") != contract.source_version:
            raise _fail("source_version_mismatch")
    return portable, overlay


def _repair_tree(root: Path, contract: DelegatedReferenceRepair) -> None:
    portable, overlay = _verify_identity(root, contract)
    source_manifest = root / Path(*PurePosixPath(contract.source_manifest_path).parts)
    if not source_manifest.is_file():
        raise _fail("source_manifest_missing")
    source_manifest_bytes = source_manifest.read_bytes()
    try:
        source_manifest_payload = json.loads(source_manifest_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise _fail("source_manifest_invalid") from exc
    if (
        not isinstance(source_manifest_payload, dict)
        or source_manifest_payload.get("schema") != "plugin-builder-candidate-manifest-v1"
    ):
        raise _fail("source_manifest_invalid")
    owner = root / "skills" / contract.owner_skill
    if not owner.is_dir():
        raise _fail("owner_skill_missing")
    for reference in contract.references:
        asset = _owner_asset(root, contract, reference.owner_relative_path)
        if not asset.is_file() or sha256(asset.read_bytes()).hexdigest() != reference.sha256:
            raise _fail("owner_reference_mismatch", reference.reference_id)
    for skill_name in contract.non_owner_skills:
        _repair_non_owner(root, skill_name, contract)
    provenance = root / "docs" / "provenance" / "source-PLUGIN-BUILDER-MANIFEST.json"
    provenance.parent.mkdir(parents=True, exist_ok=True)
    if provenance.exists():
        raise _fail("provenance_collision")
    provenance.write_bytes(source_manifest_bytes)
    source_manifest.unlink()
    portable["version"] = contract.target_version
    overlay["version"] = contract.target_version
    _write_json(root / "plugin.json", portable)
    _write_json(root / ".codex-plugin" / "plugin.json", overlay)
    before_manifest = plugin_authoring.tree_manifest(root)
    repair_manifest = {
        "schema": "workbench-repair-manifest-v1",
        "plugin_id": contract.plugin_id,
        "source_version": contract.source_version,
        "target_version": contract.target_version,
        "source_archive_sha256": contract.source_archive_sha256,
        "source_manifest_sha256": sha256(source_manifest_bytes).hexdigest(),
        "owner_skill": contract.owner_skill,
        "non_owner_skills": list(contract.non_owner_skills),
        "references": [asdict(reference) for reference in contract.references],
        "approval_record": dict(contract.approval_record),
        "content_members": [asdict(member) for member in before_manifest],
        "content_tree_sha256": plugin_authoring.tree_sha256(root),
    }
    _write_json(root / "WORKBENCH-REPAIR-MANIFEST.json", repair_manifest)
    issues = plugin_authoring.validate_plugin_tree(root)
    if issues:
        first = issues[0]
        raise _fail("candidate_invalid", f"{first.code}:{first.path}")


def repair_delegated_reference_archive(
    archive: Path,
    contract: DelegatedReferenceRepair,
    output_archive: Path,
    output_metadata: Path,
) -> RepairResult:
    """Create a deterministic repaired derivative after complete validation."""

    source = Path(archive)
    destination = Path(output_archive)
    metadata_destination = Path(output_metadata)
    if destination.absolute() == metadata_destination.absolute():
        raise _fail("output_collision")
    if destination.exists() or metadata_destination.exists():
        raise _fail("output_exists")
    try:
        inventory = plugin_authoring.inventory_archive(source)
    except plugin_authoring.PluginAuthoringError as exc:
        raise _fail("archive_invalid", exc.code) from exc
    if inventory.archive_sha256 != contract.source_archive_sha256:
        raise _fail("source_digest_mismatch")
    with tempfile.TemporaryDirectory(prefix="plugin-reference-repair-") as temporary_name:
        temporary = Path(temporary_name)
        extracted = temporary / "source"
        try:
            plugin_authoring.extract_archive(source, extracted)
            located = plugin_authoring.locate_plugin_archive_root(extracted)
        except plugin_authoring.PluginAuthoringError as exc:
            raise _fail("archive_invalid", exc.code) from exc
        if located.profile != "LEGACY_FLAT":
            raise _fail("source_profile_invalid")
        _repair_tree(located.path, contract)
        staged_archive = temporary / "candidate.zip"
        archive_sha256 = plugin_authoring.write_deterministic_zip(
            located.path, staged_archive
        )
        repaired_inventory = plugin_authoring.inventory_archive(staged_archive)
        content_tree_sha256 = plugin_authoring.tree_sha256(located.path)
        members = [asdict(member) for member in repaired_inventory.members]
        member_manifest_sha256 = sha256(_canonical_bytes(members)).hexdigest()
        repair_manifest_sha256 = next(
            member.sha256
            for member in repaired_inventory.members
            if member.path == "WORKBENCH-REPAIR-MANIFEST.json"
        )
        metadata_payload = {
            "schema": "workbench-repaired-plugin-v1",
            "plugin_id": contract.plugin_id,
            "version": contract.target_version,
            "archive_sha256": archive_sha256,
            "source_archive_sha256": contract.source_archive_sha256,
            "member_manifest_sha256": member_manifest_sha256,
            "content_tree_sha256": content_tree_sha256,
            "members": members,
            "input_profile": "PLUGIN_BUILDER_CANDIDATE_V1",
            "envelope_profile": "LEGACY_FLAT",
            "manifest_profile": "PORTABLE_WITH_OPENAI_COMPATIBILITY",
            "repair_manifest_sha256": repair_manifest_sha256,
            "producer_claims": {
                "schema": "plugin-builder-candidate-manifest-v1",
                "verification_state": "NOT VERIFIED",
            },
            "evidence_states": {layer: "NOT VERIFIED" for layer in _LAYERS},
            "extracted_validation": {"state": "PASS", "diagnostics": []},
            "safety_validation": {"state": "PASS", "diagnostics": []},
        }
        staged_metadata = temporary / "package-metadata.json"
        staged_metadata.write_bytes(_canonical_bytes(metadata_payload))
        destination.parent.mkdir(parents=True, exist_ok=True)
        metadata_destination.parent.mkdir(parents=True, exist_ok=True)
        published_archive = False
        try:
            os.replace(staged_archive, destination)
            published_archive = True
            os.replace(staged_metadata, metadata_destination)
        except OSError as exc:
            if published_archive:
                destination.unlink(missing_ok=True)
            metadata_destination.unlink(missing_ok=True)
            raise _fail("output_write_failed") from exc
    return RepairResult(
        archive=destination,
        metadata=metadata_destination,
        archive_sha256=archive_sha256,
        member_manifest_sha256=member_manifest_sha256,
        source_archive_sha256=contract.source_archive_sha256,
    )
