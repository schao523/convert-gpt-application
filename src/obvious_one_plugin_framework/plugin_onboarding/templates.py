"""Deterministic, product-neutral files for a plugin onboarding proposal."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Mapping

from .contract import PublicationDecisions
from .inspection import OnboardingInspection


def canonical_json_bytes(value: object) -> bytes:
    """Serialize one stable ASCII JSON document with an LF terminator."""

    return (json.dumps(_json_value(value), ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode(
        "ascii"
    )


def _json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def lf_bytes(value: str) -> bytes:
    return value.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _is_text(content: bytes) -> bool:
    if b"\x00" in content:
        return False
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _mit_license(decisions: PublicationDecisions) -> bytes:
    return lf_bytes(
        f"""MIT License

Copyright (c) {decisions.copyright_year} {decisions.author}

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
    )


def _builder_script(
    plugin_id: str,
    version: str,
    expected_members: tuple[object, ...],
    expected_tree_sha256: str,
) -> bytes:
    member_payload = [asdict(member) for member in expected_members]
    return lf_bytes(
        f'''"""Build the reviewed Codex plugin from immutable imported bytes."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile


PLUGIN_ID = {plugin_id!r}
VERSION = {version!r}
EXPECTED_MEMBERS = {member_payload!r}
EXPECTED_TREE_SHA256 = {expected_tree_sha256!r}


def _tree_manifest(root: Path) -> list[dict[str, object]]:
    members = []
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        directory_path = Path(directory)
        for name in sorted(names):
            child = directory_path / name
            attributes = getattr(child.lstat(), "st_file_attributes", 0)
            if child.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise ValueError("imported_plugin_tree_mismatch")
        for name in sorted(files):
            child = directory_path / name
            attributes = getattr(child.lstat(), "st_file_attributes", 0)
            if child.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise ValueError("imported_plugin_tree_mismatch")
            content = child.read_bytes()
            members.append({{
                "path": child.relative_to(root).as_posix(),
                "size": len(content),
                "sha256": sha256(content).hexdigest(),
            }})
    return sorted(members, key=lambda item: item["path"])


def _tree_identity(root: Path) -> None:
    members = _tree_manifest(root)
    encoded = json.dumps(
        members, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    if members != EXPECTED_MEMBERS or sha256(encoded).hexdigest() != EXPECTED_TREE_SHA256:
        raise ValueError("imported_plugin_tree_mismatch")


def _identity(root: Path) -> tuple[str, str]:
    identities = []
    for relative in ("plugin.json", ".codex-plugin/plugin.json"):
        payload = json.loads((root / relative).read_text(encoding="utf-8"))
        author = payload.get("author")
        if isinstance(author, dict):
            author = author.get("name")
        identities.append((payload.get("name"), payload.get("version"), author))
    if identities[0] != identities[1] or identities[0][:2] != (PLUGIN_ID, VERSION):
        raise ValueError("imported_plugin_identity_mismatch")
    return PLUGIN_ID, VERSION


def build(source: Path, destination: Path) -> Path:
    source = source.resolve()
    imported = source / "imported-plugin"
    license_path = source / "LICENSE"
    if not license_path.is_file():
        raise ValueError("license_missing")
    _identity(imported)
    _tree_identity(imported)
    target = destination.resolve() / "plugins" / PLUGIN_ID
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix=f".{{PLUGIN_ID}}-", dir=target.parent))
    staged = temporary_root / PLUGIN_ID
    try:
        shutil.copytree(imported, staged, copy_function=shutil.copy2)
        _identity(staged)
        _tree_identity(staged)
        shutil.copy2(license_path, staged / "LICENSE")
        if target.exists():
            shutil.rmtree(target)
        os.replace(staged, target)
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    if args.version != VERSION:
        raise ValueError("version_mismatch")
    build(args.source, args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    )


def _audit_script() -> bytes:
    return lf_bytes(
        '''"""Static audit hook for immutable imported plugin content."""
from __future__ import annotations

from pathlib import Path


def audit_distribution(stage: Path, contract: object) -> tuple[str, ...]:
    issues = []
    root = Path(stage)
    if not (root / "plugin.json").is_file():
        issues.append("missing plugin.json")
    if not (root / ".codex-plugin" / "plugin.json").is_file():
        issues.append("missing .codex-plugin/plugin.json")
    return tuple(issues)
'''
    )


def _generated_test_imported(
    plugin_id: str,
    version: str,
    expected_members: tuple[object, ...],
    expected_tree_sha256: str,
) -> bytes:
    member_payload = [asdict(member) for member in expected_members]
    return lf_bytes(
        f'''from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import unittest


EXPECTED_MEMBERS = {member_payload!r}
EXPECTED_TREE_SHA256 = {expected_tree_sha256!r}


def _tree_manifest(root: Path) -> list[dict[str, object]]:
    members = []
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        directory_path = Path(directory)
        for name in sorted(names):
            child = directory_path / name
            attributes = getattr(child.lstat(), "st_file_attributes", 0)
            if child.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise ValueError("imported_plugin_tree_mismatch")
        for name in sorted(files):
            child = directory_path / name
            attributes = getattr(child.lstat(), "st_file_attributes", 0)
            if child.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise ValueError("imported_plugin_tree_mismatch")
            content = child.read_bytes()
            members.append({{
                "path": child.relative_to(root).as_posix(),
                "size": len(content),
                "sha256": sha256(content).hexdigest(),
            }})
    return sorted(members, key=lambda item: item["path"])


class ImportedPackageTests(unittest.TestCase):
    def test_manifest_pair_identity(self) -> None:
        root = Path(__file__).resolve().parents[1] / "imported-plugin"
        identities = []
        for relative in ("plugin.json", ".codex-plugin/plugin.json"):
            payload = json.loads((root / relative).read_text(encoding="utf-8"))
            identities.append((payload["name"], payload["version"]))
        self.assertEqual(identities, [({plugin_id!r}, {version!r})] * 2)

    def test_exact_member_bytes(self) -> None:
        root = Path(__file__).resolve().parents[1] / "imported-plugin"
        members = _tree_manifest(root)
        encoded = json.dumps(
            members, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("ascii")
        self.assertEqual(members, EXPECTED_MEMBERS)
        self.assertEqual(sha256(encoded).hexdigest(), EXPECTED_TREE_SHA256)


if __name__ == "__main__":
    unittest.main()
'''
    )


def _generated_test_release(plugin_id: str) -> bytes:
    return lf_bytes(
        f'''from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


APPLICATION = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "onboarded_marketplace_builder", APPLICATION / "scripts" / "build_marketplace_release.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("marketplace_builder_unavailable")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class MarketplaceReleaseTests(unittest.TestCase):
    def test_build_copies_imported_tree(self) -> None:
        source = APPLICATION
        with tempfile.TemporaryDirectory() as name:
            target = BUILDER.build(source, Path(name))
            self.assertEqual(target.name, {plugin_id!r})
            expected = sorted(p.relative_to(source / "imported-plugin") for p in (source / "imported-plugin").rglob("*") if p.is_file())
            actual = sorted(p.relative_to(target) for p in target.rglob("*") if p.is_file())
            self.assertEqual(actual, sorted(set(expected) | {{Path("LICENSE")}}))
            for relative in expected:
                self.assertEqual((target / relative).read_bytes(), (source / "imported-plugin" / relative).read_bytes())
            self.assertEqual((target / "LICENSE").read_bytes(), (source / "LICENSE").read_bytes())


if __name__ == "__main__":
    unittest.main()
'''
    )


def render_application_files(
    inspection: OnboardingInspection,
    decisions: PublicationDecisions,
    imported: Mapping[str, bytes],
) -> dict[str, bytes]:
    """Render every generated application file except imported plugin bytes."""

    plugin_id = inspection.plugin_id
    version = inspection.version
    selected = tuple(sorted(f"imported-plugin/{path}" for path in imported))
    text_paths = tuple(sorted(f"imported-plugin/{path}" for path, data in imported.items() if _is_text(data)))
    binary_paths = tuple(sorted(set(selected) - set(text_paths)))
    rights = {
        "status": "approved",
        "provenance": "docs/source-decisions.md",
    }
    content_rules = []
    if text_paths:
        content_rules.append(
            {
                "id": "imported-plugin-text",
                "paths": list(text_paths),
                "prefixes": [],
                "classification": "text",
                "redistribution": rights,
            }
        )
    if binary_paths:
        content_rules.append(
            {
                "id": "imported-plugin-binary",
                "paths": list(binary_paths),
                "prefixes": [],
                "classification": "binary",
                "redistribution": rights,
            }
        )
    size_limit = max(1_048_576, sum(len(data) for data in imported.values()) * 2)
    distribution = {
        "schema_version": 3,
        "plugin_id": plugin_id,
        "package_name": f"@obvious-one/{plugin_id}",
        "family": "bundle-plugin",
        "version": version,
        "source_root": "..",
        "include_files": list(selected),
        "include_prefixes": [],
        "exclude_paths": [],
        "max_total_bytes": size_limit,
        "release_repository": "schao523/obvious-one-plugins",
        "release_tag_template": f"{plugin_id}-v{{version}}",
        "readme_overlay": None,
        "audit_hook": "scripts/distribution_audit.py:audit_distribution",
        "rag": None,
        "content_rules": content_rules,
        "publication": {
            "github_marketplace": {"enabled": True},
            "clawhub": {"enabled": False, "family": None, "native_manifest": None},
        },
    }
    conversion = {
        "schema_version": 2,
        "application_id": plugin_id,
        "plugin_id": plugin_id,
        "source_inventory": "docs/imported-package-inventory.json",
        "source_location": "conversion.local.json",
        "coverage_matrix": "docs/application-invariants.md",
        "distribution_contract": "openclaw/distribution.json",
        "marketplace_repository": "schao523/obvious-one-plugins",
        "provenance": {
            "source_repository": "plugin-builder-reviewed-package",
            "incorporated_branches": [],
            "inventory_rules": [
                {"root": "imported-plugin", "classification": "approved-plugin", "include": ["**/*"]}
            ],
        },
        "verification": {
            "test_directory": "tests",
            "commands": [
                {
                    "id": "imported-package",
                    "argv": ["{python}", "-B", "{application_root}/tests/test_imported_package.py"],
                },
                {
                    "id": "marketplace-release",
                    "argv": ["{python}", "-B", "{application_root}/tests/test_marketplace_release.py"],
                },
            ],
            "codex_build": {
                "argv": [
                    "{python}", "-B", "{application_root}/scripts/build_marketplace_release.py",
                    "--source", "{application_root}", "--destination", "{diagnostics}/codex-marketplace",
                    "--version", "{version}",
                ],
                "artifact_path": "plugins/{plugin_id}",
            },
        },
    }
    inventory = {
        "schema": "plugin-onboarding-imported-inventory-v1",
        "plugin_id": plugin_id,
        "archive_sha256": inspection.archive_sha256,
        "content_tree_sha256": inspection.content_tree_sha256,
        "members": [asdict(member) for member in inspection.candidate_members],
    }
    if inspection.candidate_sha256 is not None:
        inventory["candidate_sha256"] = inspection.candidate_sha256
    decision_payload = {
        **decisions.identity_payload(),
        "decision_recorded_at": decisions.decision_recorded_at,
    }
    notices = (
        imported["THIRD_PARTY_NOTICES.md"]
        if decisions.third_party_content == "INCLUDED_WITH_PLUGIN_NOTICES"
        else lf_bytes("# Third-Party Notices\n\nNo third-party notices are required for this approved package.\n")
    )
    portable = imported["plugin.json"]
    compatibility = imported[".codex-plugin/plugin.json"]
    return {
        ".gitattributes": b"imported-plugin/** -text -whitespace\n",
        "conversion.json": canonical_json_bytes(conversion),
        "plugin.json": portable,
        ".codex-plugin/plugin.json": compatibility,
        "DISTRIBUTION.md": lf_bytes("# Distribution\n\nCodex marketplace build is enabled. OpenClaw and ClawHub publication are not applicable to this approved onboarding scope.\n"),
        "LICENSE": _mit_license(decisions),
        "PRIVACY.md": lf_bytes("# Privacy\n\nThis registration adds no data collection. Imported plugin behavior remains authoritative.\n"),
        "SECURITY.md": lf_bytes("# Security\n\nReport security concerns to the plugin owner. No imported executable is run during onboarding.\n"),
        "THIRD_PARTY_CONTENT.md": lf_bytes(f"# Third-Party Content\n\nOwner decision: `{decisions.third_party_content}`.\n"),
        "THIRD_PARTY_NOTICES.md": notices,
        "docs/application-invariants.md": lf_bytes("# Application Invariants\n\nThe imported plugin bytes, identity, skills, references, and declared behavior are preserved exactly.\n"),
        "docs/imported-package-inventory.json": canonical_json_bytes(inventory),
        "docs/publication-decisions.json": canonical_json_bytes(decision_payload),
        "docs/runtime-compatibility.md": lf_bytes("# Runtime Compatibility\n\nCodex publication is in scope. OpenClaw and ClawHub are not applicable under the approved target decision. Runtime evidence states remain those recorded in the onboarding proposal.\n"),
        "docs/source-decisions.md": lf_bytes(f"# Source Decisions\n\nRedistribution was explicitly approved by {decisions.confirmed_by}. License: MIT. Third-party content state: {decisions.third_party_content}.\n"),
        "openclaw/distribution.json": canonical_json_bytes(distribution),
        "scripts/build_marketplace_release.py": _builder_script(
            plugin_id,
            version,
            inspection.candidate_members,
            inspection.content_tree_sha256,
        ),
        "scripts/distribution_audit.py": _audit_script(),
        "tests/test_imported_package.py": _generated_test_imported(
            plugin_id,
            version,
            inspection.candidate_members,
            inspection.content_tree_sha256,
        ),
        "tests/test_marketplace_release.py": _generated_test_release(plugin_id),
    }
