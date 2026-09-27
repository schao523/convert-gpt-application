from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from obvious_one_plugin_framework.hosted_deployment_builder import build_hosted_deployment
from obvious_one_plugin_framework.hosted_deployment_contract import (
    HostedDeploymentError,
    load_hosted_deployment_contract,
)


FIXTURE = Path(__file__).parent / "fixtures" / "hosted-deployment" / "application"


class HostedDeploymentBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.application = self.root / "hosted-fixture"
        shutil.copytree(FIXTURE, self.application)
        self.contract_path = self.application / "hosted-openai" / "deployment.json"
        self.contract = load_hosted_deployment_contract(self.contract_path)
        self.output = self.root / "artifact"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def tree_bytes(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
            if path.is_file()
        }

    def source_hashes(self) -> dict[str, str]:
        return {
            path.relative_to(self.application).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.application.rglob("*"), key=lambda item: item.as_posix())
            if path.is_file()
        }

    def test_create_builds_complete_artifact_set_without_previous_archive(self) -> None:
        result = build_hosted_deployment(self.contract, self.output)
        self.assertEqual(set(path.name for path in self.output.iterdir()), {
            result.archive_path.name,
            "deployment-manifest.json",
            "validation-report.json",
            "deployment-report.json",
        })
        self.assertEqual(result.archive_path.name, "gpt-hosted-fixture-1.1.0.zip")

    def test_two_builds_are_byte_identical(self) -> None:
        first = build_hosted_deployment(self.contract, self.root / "a")
        second = build_hosted_deployment(self.contract, self.root / "b")
        self.assertEqual(first.artifact_sha256, second.artifact_sha256)
        self.assertEqual(self.tree_bytes(self.root / "a"), self.tree_bytes(self.root / "b"))

    def test_failure_preserves_previous_artifact_directory(self) -> None:
        build_hosted_deployment(self.contract, self.output)
        before = self.tree_bytes(self.output)
        (self.application / "skills" / "demo" / "SKILL.md").unlink()
        with self.assertRaises(HostedDeploymentError):
            build_hosted_deployment(self.contract, self.output)
        self.assertEqual(self.tree_bytes(self.output), before)

    def test_zip_has_exact_sorted_members_and_fixed_metadata(self) -> None:
        result = build_hosted_deployment(self.contract, self.output)
        with zipfile.ZipFile(result.archive_path) as archive:
            infos = archive.infolist()
        self.assertEqual([item.filename for item in infos], [
            ".codex-plugin/plugin.json", "plugin.json", "skills/demo/SKILL.md"
        ])
        self.assertTrue(all(item.date_time == (1980, 1, 1, 0, 0, 0) for item in infos))
        self.assertTrue(all((item.external_attr >> 16) & 0o777 == 0o644 for item in infos))

    def test_text_is_lf_binary_is_exact_and_source_is_not_mutated(self) -> None:
        skill = self.application / "skills" / "demo" / "SKILL.md"
        skill.write_bytes(skill.read_bytes().replace(b"\n", b"\r\n"))
        binary = self.application / "assets" / "icon.bin"
        binary.parent.mkdir()
        binary.write_bytes(b"\x00\r\n\xff")
        distribution_path = self.application / "openclaw" / "distribution.json"
        distribution = json.loads(distribution_path.read_text(encoding="utf-8"))
        distribution["include_files"].append("assets/icon.bin")
        distribution["content_rules"].append({
            "id": "approved-binary", "paths": ["assets/icon.bin"], "prefixes": [],
            "classification": "binary",
            "redistribution": {"status": "approved", "provenance": "docs/source-decisions.md"}
        })
        distribution_path.write_text(json.dumps(distribution), encoding="utf-8")
        deployment = json.loads(self.contract_path.read_text(encoding="utf-8"))
        deployment["content"]["canonical_mappings"].append({
            "id": "icon", "source_kind": "canonical_application", "source": "assets/icon.bin",
            "target": "assets/icon.bin", "copy_mode": "copy_file", "classification": "binary",
            "redistribution_reference": "approved-binary"
        })
        self.contract_path.write_text(json.dumps(deployment), encoding="utf-8")
        before = self.source_hashes()
        result = build_hosted_deployment(load_hosted_deployment_contract(self.contract_path), self.output)
        with zipfile.ZipFile(result.archive_path) as archive:
            self.assertNotIn(b"\r\n", archive.read("skills/demo/SKILL.md"))
            self.assertEqual(archive.read("assets/icon.bin"), b"\x00\r\n\xff")
        self.assertEqual(self.source_hashes(), before)

    def test_reports_are_canonical_and_previous_unlisted_files_do_not_survive(self) -> None:
        self.output.mkdir()
        (self.output / "old.zip").write_bytes(b"old")
        build_hosted_deployment(self.contract, self.output)
        self.assertFalse((self.output / "old.zip").exists())
        for name in ("deployment-manifest.json", "validation-report.json", "deployment-report.json"):
            raw = (self.output / name).read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("\n"))
            pairs = json.loads(raw, object_pairs_hook=list)
            self.assertEqual([key for key, _ in pairs], sorted(key for key, _ in pairs))


if __name__ == "__main__":
    unittest.main()
