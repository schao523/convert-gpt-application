"""Derive the owner-approved Codex release from one exact Plugin Builder ZIP.

The original producer manifest is retained as source evidence outside the
installed plugin. This script never represents the derivative as a new Plugin
Builder build or promotes installed-runtime evidence.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sys
import zipfile

from obvious_one_plugin_framework import plugin_authoring


SOURCE_ARCHIVE_SHA256 = "7603ec8f8d718b776e34ee1d8d69bf8ae19681c37b64b52415a6f19520fc640b"
SOURCE_MANIFEST_SHA256 = "bb594de6099f09b93ce4ef0e00e7bef4d74c1c442d3ecba24be9eb690cc03395"
SOURCE_ID = "gpt-a78425d7a04b61ed25c338d0e4e210de"
SOURCE_VERSION = "0.27.0"
TARGET_ID = "cool-leadership-coach"
TARGET_VERSION = "1.0.0"
DISPLAY_NAME = "酷領導力教練"
AUTHOR = "Shen-Chang Chao"
SOURCE_MANIFEST = "PLUGIN-BUILDER-MANIFEST.json"
TARGET_MANIFEST = "WORKBENCH-DERIVATION-MANIFEST.json"
TRANSFORMED = (
    ".codex-plugin/plugin.json",
    "plugin.json",
    "RUNTIME-COMPATIBILITY.md",
    "skills/explaining-source-evidence/references/knowledge-index.json",
    "skills/explaining-source-evidence/references/professional-index.json",
    "skills/explaining-source-evidence/references/rights-ledger.md",
    "skills/explaining-source-evidence/references/source-quality.md",
)


def _encode(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def _members(root: Path) -> list[dict[str, object]]:
    return [asdict(member) for member in plugin_authoring.tree_manifest(root)]


def _replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise ValueError(f"source text anchor mismatch: {path.name}")
    path.write_bytes(text.replace(old, new).encode("utf-8"))


def _replace_count(path: Path, old: str, new: str, count: int) -> None:
    content = path.read_text(encoding="utf-8")
    if content.count(old) != count:
        raise ValueError(f"source text anchor mismatch: {path.name}")
    path.write_bytes(content.replace(old, new).encode("utf-8"))


def _rewrite_identity(path: Path, *, codex_manifest: bool) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (payload.get("name"), payload.get("version")) != (SOURCE_ID, SOURCE_VERSION):
        raise ValueError("source plugin identity mismatch")
    interface = payload["interface"] if codex_manifest else payload["extensions"]["com.openai"]["interface"]
    if payload.get("author", {}).get("name") != AUTHOR or interface.get("developerName") != AUTHOR:
        raise ValueError("source author identity mismatch")
    payload["name"] = TARGET_ID
    payload["version"] = TARGET_VERSION
    payload["author"]["name"] = AUTHOR
    interface["developerName"] = AUTHOR
    interface["displayName"] = DISPLAY_NAME
    path.write_bytes(_encode(payload))


def derive(source: Path, application: Path) -> dict[str, object]:
    source = source.resolve()
    application = application.resolve()
    imported = application / "imported-plugin"
    if imported.exists():
        raise ValueError("derivative destination already exists")
    if sha256(source.read_bytes()).hexdigest() != SOURCE_ARCHIVE_SHA256:
        raise ValueError("source archive digest mismatch")
    inventory = plugin_authoring.inventory_archive(source)
    if inventory.archive_sha256 != SOURCE_ARCHIVE_SHA256:
        raise ValueError("source archive inventory mismatch")

    with zipfile.ZipFile(source) as archive:
        prefix = f"{SOURCE_ID}/"
        names = archive.namelist()
        if len(names) != len(set(names)) or any(not name.startswith(prefix) or name.endswith("/") for name in names):
            raise ValueError("source envelope mismatch")
        source_manifest_bytes = archive.read(prefix + SOURCE_MANIFEST)
        if sha256(source_manifest_bytes).hexdigest() != SOURCE_MANIFEST_SHA256:
            raise ValueError("source producer manifest mismatch")
        source_manifest = json.loads(source_manifest_bytes)
        if source_manifest.get("schema") != "plugin-builder-candidate-manifest-v3":
            raise ValueError("source producer schema mismatch")
        expected = source_manifest.get("members")
        if not isinstance(expected, list):
            raise ValueError("source member inventory missing")
        expected_by_path = {member["path"]: member for member in expected}
        actual_paths = {name[len(prefix):] for name in names} - {SOURCE_MANIFEST}
        if len(expected_by_path) != len(expected) or actual_paths != set(expected_by_path):
            raise ValueError("source member set mismatch")
        for relative in sorted(actual_paths):
            content = archive.read(prefix + relative)
            record = expected_by_path[relative]
            if (len(content), sha256(content).hexdigest()) != (record["size"], record["sha256"]):
                raise ValueError(f"source member hash mismatch: {relative}")
            target = imported / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

    _rewrite_identity(imported / "plugin.json", codex_manifest=False)
    _rewrite_identity(imported / ".codex-plugin" / "plugin.json", codex_manifest=True)
    _replace_once(
        imported / "RUNTIME-COMPATIBILITY.md",
        "Public release HOLD. A local successful build is neither expert accreditation nor release acceptance. No external publication/deployment authorization is included.",
        "Public Obvious One Codex publication of the 1.0.0 derivative was authorized by the decision owner on 2026-10-25. This does not certify expert review, installed Skill invocation, reference consultation, or conversational behavior; those remain NOT VERIFIED.",
    )
    _replace_once(
        imported / "RUNTIME-COMPATIBILITY.md",
        "T01–T30, 13 stage practices, 8 negatives, expert reviews and exact-edition/derivative rights remain separate post-build gates.",
        "T01–T30, 13 stage practices, 8 negatives, and expert reviews remain separate post-build gates. The owner recorded the exact-edition and derivative redistribution decision for this release.",
    )
    _replace_once(
        imported / "skills" / "explaining-source-evidence" / "references" / "rights-ledger.md",
        "Public release remains gated. A private/nonpublic build is not represented as publication.",
        "For the 1.0.0 derivative, the decision owner confirmed public MIT redistribution rights for every bundled PDF, card, reference, and code file on 2026-10-25. Workbench makes no independent legal determination.",
    )
    _replace_once(
        imported / "skills" / "explaining-source-evidence" / "references" / "rights-ledger.md",
        "- **Public-release step:** documented lawful basis for each Bible PDF and professional derivative expression, no bulk excerpts, no hidden nested original PDF, attribution/provenance, privacy and final owner release decision.",
        "- **Public-release decision:** the owner confirmed lawful redistribution and required notices for the exact source archive and approved a Codex-only Obvious One release under MIT. The two retained Bible PDFs and their SHA-256 identities are documented in `THIRD_PARTY_NOTICES.md`; no removed professional PDF is restored.",
    )
    references = imported / "skills" / "explaining-source-evidence" / "references"
    _replace_once(
        references / "source-quality.md",
        "Bible public-domain status is the owner's declaration, with exact-edition and jurisdiction review pending. This is permission for a nonpublic candidate, not public distribution clearance. PUBLIC RELEASE HOLD remains until rights, runtime acceptance, independent review and separate owner release authorization are satisfied.",
        "The owner confirmed exact-edition and derivative redistribution rights for this 1.0.0 Codex release under MIT on 2026-10-25; Workbench made no independent legal determination. Installed runtime acceptance and independent professional review remain NOT VERIFIED and are not implied by publication.",
    )
    _replace_count(
        references / "knowledge-index.json",
        "project method is provisional; public release HOLD.",
        "project method is provisional; 1.0.0 redistribution owner-approved; installed use NOT VERIFIED.",
        10,
    )
    _replace_count(
        references / "professional-index.json",
        "PUBLIC_DOMAIN\\u2014OWNER DECLARATION; PUBLIC_RELEASE_HOLD",
        "PUBLIC_DOMAIN\\u2014OWNER DECLARATION; OWNER_APPROVED_REDISTRIBUTION_2026-10-25",
        2,
    )

    pdf_records = [member for member in expected if str(member["path"]).lower().endswith(".pdf")]
    if len(pdf_records) != 2:
        raise ValueError("unexpected PDF inventory")
    notice_lines = [
        "# Third-party content and notices",
        "",
        "The decision owner confirmed redistribution rights for this exact release on 2026-10-25.",
        "The source rights ledger describes the two retained Chinese Union Version PDFs as owner-stated public-domain material. Workbench did not make an independent legal determination.",
        "",
    ]
    for record in pdf_records:
        notice_lines += [f"- `{record['path']}` — SHA-256 `{record['sha256']}`"]
    notice_lines += [
        "",
        "Project-authored professional cards are nonverbatim syntheses according to the source rights ledger. No original third-party professional PDF is bundled.",
    ]
    (imported / "THIRD_PARTY_NOTICES.md").write_bytes(("\n".join(notice_lines) + "\n").encode("utf-8"))
    (imported / "THIRD_PARTY_CONTENT.md").write_bytes(
        b"# Third-party content\n\nSee THIRD_PARTY_NOTICES.md for the two retained Bible PDFs, their exact hashes, and the owner-confirmed redistribution decision. The original third-party professional PDFs are excluded.\n"
    )
    (imported / "PRIVACY.md").write_bytes(
        b"# Privacy\n\nThis plugin contains local skills and references and declares no external service or credential requirement. Conversation data is handled by the host runtime; the plugin does not claim durable memory or independent data retention.\n"
    )
    (imported / "README.md").write_bytes(
        ("# " + DISPLAY_NAME + "\n\nCodex-only 1.0.0 release derived from the exact owner-approved 0.27.0 Plugin Builder package. See WORKBENCH-DERIVATION-MANIFEST.json for provenance. Installed Skill invocation and conversational behavior remain NOT VERIFIED.\n").encode("utf-8")
    )
    target_members = _members(imported)
    derivation = {
        "schema": "workbench-identity-derivation-v1",
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "source_candidate_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "source_candidate_schema": "plugin-builder-candidate-manifest-v3",
        "source_plugin_id": SOURCE_ID,
        "source_version": SOURCE_VERSION,
        "target_plugin_id": TARGET_ID,
        "target_version": TARGET_VERSION,
        "target_display_name": DISPLAY_NAME,
        "author": AUTHOR,
        "developer_name": AUTHOR,
        "transformed_paths": sorted(TRANSFORMED),
        "removed_paths": [SOURCE_MANIFEST],
        "added_paths": sorted(["PRIVACY.md", "README.md", "THIRD_PARTY_CONTENT.md", "THIRD_PARTY_NOTICES.md", TARGET_MANIFEST]),
        "source_members": expected,
        "target_members_excluding_self": target_members,
        "runtime_evidence": "NOT VERIFIED",
    }
    (imported / TARGET_MANIFEST).write_bytes(_encode(derivation))
    issues = plugin_authoring.validate_plugin_tree(imported)
    if issues:
        raise ValueError(f"derivative structural findings: {issues}")

    docs = application / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "source-plugin-builder-manifest.json").write_bytes(source_manifest_bytes)
    observed = _members(imported)
    imported_inventory = {
        "schema": "plugin-onboarding-imported-inventory-v1",
        "plugin_id": TARGET_ID,
        "archive_sha256": SOURCE_ARCHIVE_SHA256,
        "candidate_sha256": plugin_authoring.tree_sha256(imported),
        "content_tree_sha256": plugin_authoring.tree_sha256(imported),
        "members": observed,
    }
    (docs / "imported-package-inventory.json").write_bytes(_encode(imported_inventory))
    source_inventory = {
        "schema": "workbench-source-archive-inventory-v1",
        "archive_sha256": SOURCE_ARCHIVE_SHA256,
        "source_root": SOURCE_ID,
        "producer_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "producer_schema": "plugin-builder-candidate-manifest-v3",
        "source_members": expected,
        "derivation_manifest_sha256": sha256((imported / TARGET_MANIFEST).read_bytes()).hexdigest(),
    }
    (docs / "source-archive-inventory.json").write_bytes(_encode(source_inventory))
    return imported_inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--application", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    inventory = derive(args.source, args.application)
    sys.stdout.write(json.dumps({"status": "PASS", "plugin_id": TARGET_ID, "candidate_sha256": inventory["candidate_sha256"]}, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
