from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
import warnings
import zipfile

from obvious_one_plugin_framework.hosted_deployment_contract import HostedDeploymentError
from obvious_one_plugin_framework.hosted_identity import (
    ArchiveLimits,
    inventory_hosted_identity_archive,
    propose_hosted_identity,
)


FIXTURE = Path(__file__).parent / "fixtures" / "hosted-deployment" / "application"


class HostedIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.application_root = self.root / "hosted-fixture"
        shutil.copytree(FIXTURE, self.application_root)
        self.application = self.application_root / "conversion.json"
        self.proposal = self.root / "proposal.json"
        self.archive = self.write_zip([
            ("plugin.json", json.dumps({"name": "gpt-hosted-fixture", "version": "1.0.0"}).encode()),
            (".codex-plugin/plugin.json", json.dumps({"name": "gpt-hosted-fixture", "version": "1.0.0"}).encode()),
            ("assets/icon.png", b"icon-bytes"),
            ("docs/private.txt", b"secret member body"),
        ])

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_zip(
        self,
        members: list[tuple[str, bytes]],
        *,
        path: Path | None = None,
        compression: int = zipfile.ZIP_DEFLATED,
        mutate_info=None,
    ) -> Path:
        destination = path or self.root / "hosted.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(destination, "w", compression=compression) as archive:
                for name, body in members:
                    info = zipfile.ZipInfo(name)
                    info.compress_type = compression
                    if mutate_info is not None:
                        mutate_info(info)
                    archive.writestr(info, body)
        return destination

    def mark_encrypted(self, path: Path) -> None:
        payload = bytearray(path.read_bytes())
        cursor = 0
        while True:
            cursor = payload.find(b"PK\x03\x04", cursor)
            if cursor < 0:
                break
            payload[cursor + 6] |= 1
            cursor += 4
        cursor = 0
        while True:
            cursor = payload.find(b"PK\x01\x02", cursor)
            if cursor < 0:
                break
            payload[cursor + 8] |= 1
            cursor += 4
        path.write_bytes(payload)

    def test_proposal_contains_hashes_but_no_private_path_or_member_bytes(self) -> None:
        result = propose_hosted_identity(self.application, self.archive, self.proposal)
        payload = json.loads(self.proposal.read_text(encoding="utf-8"))
        serialized = json.dumps(payload)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.code, "hosted_identity_approval_required")
        self.assertEqual(payload["proposal_schema"], "hosted-identity-proposal-v1")
        self.assertEqual(payload["candidate"]["package_name"], "gpt-hosted-fixture")
        self.assertNotIn(str(self.archive), serialized)
        self.assertNotIn("secret member body", serialized)

    def test_existing_destination_is_preserved(self) -> None:
        self.proposal.write_text("keep", encoding="utf-8")
        result = propose_hosted_identity(self.application, self.archive, self.proposal)
        self.assertEqual(result.code, "hosted_identity_proposal_exists")
        self.assertEqual(self.proposal.read_text(encoding="utf-8"), "keep")

    def test_casefold_collision_fails_before_proposal_mutation(self) -> None:
        archive = self.write_zip([
            ("Plugin.json", b"{}"),
            ("plugin.json", b"{}"),
        ])
        with self.assertRaisesRegex(HostedDeploymentError, "archive_casefold_collision"):
            inventory_hosted_identity_archive(archive)
        self.assertFalse(self.proposal.exists())

    def test_unsafe_member_names_and_duplicates_are_rejected(self) -> None:
        cases = [
            ([("../escape", b"x")], "archive_path_escape"),
            ([("/absolute", b"x")], "archive_path_escape"),
            ([("C:/private", b"x")], "archive_path_escape"),
            ([("plugin.json", b"{}"), ("plugin.json", b"{}")], "archive_duplicate_member"),
        ]
        for members, code in cases:
            with self.subTest(code=code):
                archive = self.write_zip(members)
                with self.assertRaisesRegex(HostedDeploymentError, code):
                    inventory_hosted_identity_archive(archive)
        alias = self.write_zip([("folder/alias", b"x")])
        payload = alias.read_bytes().replace(b"folder/alias", b"folder\\alias")
        alias.write_bytes(payload)
        with self.assertRaisesRegex(HostedDeploymentError, "archive_path_alias"):
            inventory_hosted_identity_archive(alias)

    def test_encrypted_links_and_unsupported_compression_are_rejected(self) -> None:
        encrypted = self.write_zip([("plugin.json", b"{}")])
        self.mark_encrypted(encrypted)
        with self.assertRaisesRegex(HostedDeploymentError, "archive_encrypted_member"):
            inventory_hosted_identity_archive(encrypted)

        def unix_link(info: zipfile.ZipInfo) -> None:
            info.create_system = 3
            info.external_attr = 0o120777 << 16

        linked = self.write_zip([("plugin.json", b"target")], mutate_info=unix_link)
        with self.assertRaisesRegex(HostedDeploymentError, "archive_link_member"):
            inventory_hosted_identity_archive(linked)

        def windows_link(info: zipfile.ZipInfo) -> None:
            info.create_system = 0
            info.external_attr = 0x400

        linked = self.write_zip([("plugin.json", b"target")], mutate_info=windows_link)
        with self.assertRaisesRegex(HostedDeploymentError, "archive_link_member"):
            inventory_hosted_identity_archive(linked)

        compressed = self.write_zip([("plugin.json", b"{}")], compression=zipfile.ZIP_BZIP2)
        with self.assertRaisesRegex(HostedDeploymentError, "archive_compression_unsupported"):
            inventory_hosted_identity_archive(compressed)

    def test_expansion_limits_are_checked_before_manifest_read(self) -> None:
        archive = self.write_zip([("plugin.json", b"{}"), ("extra", b"x")])
        with self.assertRaisesRegex(HostedDeploymentError, "archive_member_limit"):
            inventory_hosted_identity_archive(archive, ArchiveLimits(max_members=1))
        with self.assertRaisesRegex(HostedDeploymentError, "archive_member_too_large"):
            inventory_hosted_identity_archive(archive, ArchiveLimits(max_member_bytes=1))
        with self.assertRaisesRegex(HostedDeploymentError, "archive_expansion_limit"):
            inventory_hosted_identity_archive(archive, ArchiveLimits(max_total_bytes=2))

    def test_missing_malformed_and_incomplete_manifests_are_rejected(self) -> None:
        cases = [
            ([("README.md", b"none")], "hosted_manifest_missing"),
            ([("plugin.json", b"not-json")], "hosted_manifest_invalid"),
            ([("plugin.json", b"{}")], "hosted_identity_missing"),
        ]
        for members, code in cases:
            with self.subTest(code=code):
                archive = self.write_zip(members)
                with self.assertRaisesRegex(HostedDeploymentError, code):
                    inventory_hosted_identity_archive(archive)

    def test_non_ascii_archive_path_is_supported_without_path_disclosure(self) -> None:
        archive = self.write_zip([
            ("plugin.json", json.dumps({"name": "gpt-hosted-fixture", "version": "1.0.0"}).encode())
        ], path=self.root / "匯出外掛.zip")
        result = propose_hosted_identity(self.application, archive, self.proposal)
        self.assertEqual(result.status, "BLOCKED")
        self.assertNotIn("匯出外掛", json.dumps(result.evidence, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
