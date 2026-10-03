from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

from obvious_one_plugin_framework.plugin_authoring import archive as archive_module
from obvious_one_plugin_framework.plugin_authoring import (
    ArchiveLimits,
    PluginAuthoringError,
    TreeMember,
    extract_archive,
    inventory_archive,
    locate_plugin_archive_root,
    tree_manifest,
    tree_sha256,
    write_deterministic_zip,
)


class PluginAuthoringArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_zip(
        self,
        name: str,
        members: list[tuple[str, bytes]],
        *,
        mutate_info=None,
    ) -> Path:
        destination = self.root / name
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for member_name, body in members:
                    info = zipfile.ZipInfo(member_name)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    if mutate_info is not None:
                        mutate_info(info)
                    archive.writestr(info, body)
        return destination

    @staticmethod
    def mark_encrypted(path: Path) -> None:
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

    def assert_error_code(self, code: str, action) -> None:
        with self.assertRaises(PluginAuthoringError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)

    def test_inventory_rejects_alias_collision_encryption_links_and_expansion_limits(self) -> None:
        alias = self.write_zip(
            "alias.zip",
            [("skills/author/SKILL.md", b"one"), ("skillsXauthorXSKILL.md", b"two")],
        )
        alias.write_bytes(
            alias.read_bytes().replace(b"skillsXauthorXSKILL.md", b"skills\\author\\SKILL.md")
        )
        self.assert_error_code("archive_alias_collision", lambda: inventory_archive(alias))

        encrypted = self.write_zip("encrypted.zip", [("plugin.json", b"{}")])
        self.mark_encrypted(encrypted)
        self.assert_error_code("archive_encrypted_member", lambda: inventory_archive(encrypted))

        def unix_link(info: zipfile.ZipInfo) -> None:
            info.create_system = 3
            info.external_attr = 0o120777 << 16

        linked = self.write_zip("linked.zip", [("skills/author", b"target")], mutate_info=unix_link)
        self.assert_error_code("archive_link_member", lambda: inventory_archive(linked))

        expanded = self.write_zip("expanded.zip", [("a.txt", b"1234"), ("b.txt", b"5678")])
        self.assert_error_code(
            "archive_expansion_limit",
            lambda: inventory_archive(expanded, ArchiveLimits(max_total_bytes=7)),
        )

    def test_extract_is_transactional_and_confined(self) -> None:
        destination = self.root / "plugin"
        destination.mkdir()
        (destination / "preserve.txt").write_text("original", encoding="utf-8")

        escaping = self.write_zip(
            "escaping.zip",
            [("../outside.txt", b"escaped"), ("plugin.json", b"{}")],
        )
        self.assert_error_code(
            "archive_path_escape",
            lambda: extract_archive(escaping, destination),
        )
        self.assertEqual((destination / "preserve.txt").read_text(encoding="utf-8"), "original")
        self.assertFalse((self.root / "outside.txt").exists())

        valid = self.write_zip(
            "valid.zip",
            [("plugin.json", b"{}"), ("skills/author/SKILL.md", b"instructions")],
        )
        inventory = extract_archive(valid, destination)
        self.assertEqual(tuple(member.path for member in inventory.members), (
            "plugin.json",
            "skills/author/SKILL.md",
        ))
        self.assertFalse((destination / "preserve.txt").exists())
        self.assertEqual((destination / "skills" / "author" / "SKILL.md").read_bytes(), b"instructions")

    def test_destination_check_allows_only_root_owned_aliases(self) -> None:
        root_alias = Path(self.root.anchor) / "trusted-system-alias"
        destination = root_alias / "caller-workspace" / "plugin"

        with (
            patch("sys.platform", "darwin"),
            patch.object(
                archive_module,
                "_is_link_or_reparse",
                side_effect=lambda candidate: candidate == root_alias,
            ),
        ):
            archive_module._check_existing_components(destination)

        with (
            patch("sys.platform", "win32"),
            patch.object(
                archive_module,
                "_is_link_or_reparse",
                side_effect=lambda candidate: candidate == root_alias,
            ),
        ):
            self.assert_error_code(
                "destination_link_component",
                lambda: archive_module._check_existing_components(destination),
            )

        nested_alias = root_alias / "caller-workspace"
        with (
            patch("sys.platform", "darwin"),
            patch.object(
                archive_module,
                "_is_link_or_reparse",
                side_effect=lambda candidate: candidate in {root_alias, nested_alias},
            ),
        ):
            self.assert_error_code(
                "destination_link_component",
                lambda: archive_module._check_existing_components(destination),
            )

    def test_tree_and_zip_identity_are_portable_and_repeatable(self) -> None:
        first = self.root / "first"
        second = self.root / "second"
        for tree in (first, second):
            (tree / "skills" / "author").mkdir(parents=True)
            (tree / "plugin.json").write_bytes(b"alpha")
            (tree / "skills" / "author" / "SKILL.md").write_bytes(b"beta")

        expected = (
            TreeMember(
                path="plugin.json",
                size=5,
                sha256="8ed3f6ad685b959ead7022518e1af76cd816f8e8ec7ccdda1ed4018e8f2223f8",
            ),
            TreeMember(
                path="skills/author/SKILL.md",
                size=4,
                sha256="f44e64e75f3948e9f73f8dfa94721c4ce8cbb4f265c4790c702b2d41cfbf2753",
            ),
        )
        self.assertEqual(tree_manifest(first), expected)
        self.assertEqual(tree_manifest(second), expected)
        self.assertEqual(tree_sha256(first), tree_sha256(second))

        first_zip = self.root / "first.zip"
        second_zip = self.root / "second.zip"
        first_digest = write_deterministic_zip(first, first_zip)
        second_digest = write_deterministic_zip(second, second_zip)
        self.assertEqual(first_digest, second_digest)
        self.assertEqual(first_zip.read_bytes(), second_zip.read_bytes())

        with zipfile.ZipFile(first_zip) as archive:
            self.assertEqual(archive.namelist(), ["plugin.json", "skills/author/SKILL.md"])
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual((info.external_attr >> 16) & 0o777, 0o644)

    def test_deterministic_zip_can_prefix_every_member(self) -> None:
        tree = self.root / "plugin"
        tree.mkdir()
        (tree / "plugin.json").write_bytes(b"{}\n")
        (tree / "skill.txt").write_bytes(b"skill")
        first = self.root / "first-prefixed.zip"
        second = self.root / "second-prefixed.zip"

        self.assertEqual(
            write_deterministic_zip(tree, first, prefix="sample-plugin"),
            write_deterministic_zip(tree, second, prefix="sample-plugin"),
        )
        with zipfile.ZipFile(first) as archive:
            self.assertEqual(archive.namelist(), ["sample-plugin/plugin.json", "sample-plugin/skill.txt"])

    def test_locate_plugin_archive_root_accepts_portable_single_directory(self) -> None:
        extracted = self.root / "portable"
        plugin = extracted / "sample-plugin"
        plugin.mkdir(parents=True)
        (plugin / "plugin.json").write_text("{}", encoding="utf-8")
        located = locate_plugin_archive_root(extracted)
        self.assertEqual(located.path, plugin)
        self.assertEqual(located.profile, "PORTABLE_SINGLE_DIRECTORY")

    def test_locate_plugin_archive_root_accepts_legacy_flat_tree_for_update_only(self) -> None:
        extracted = self.root / "legacy"
        (extracted / ".codex-plugin").mkdir(parents=True)
        (extracted / ".codex-plugin/plugin.json").write_text("{}", encoding="utf-8")
        located = locate_plugin_archive_root(extracted)
        self.assertEqual(located.path, extracted)
        self.assertEqual(located.profile, "LEGACY_FLAT")

    def test_locate_plugin_archive_root_rejects_multiple_top_level_directories(self) -> None:
        extracted = self.root / "ambiguous"
        for name in ("one", "two"):
            (extracted / name).mkdir(parents=True)
            (extracted / name / "plugin.json").write_text("{}", encoding="utf-8")
        self.assert_error_code(
            "plugin_archive_root_ambiguous",
            lambda: locate_plugin_archive_root(extracted),
        )


    def test_inventory_rejects_portable_unicode_trailing_dot_reserved_and_prefix_aliases(self) -> None:
        cases = [
            [("café.txt", b"a"), ("café.txt", b"b")],
            [("a.txt", b"a"), ("a.txt.", b"b")],
            [("DIR", b"a"), ("dir/file.txt", b"b")],
            [("CON.txt", b"a")],
        ]
        for index, members in enumerate(cases):
            with self.subTest(index=index):
                archive = self.write_zip(f"portable-alias-{index}.zip", members)
                with self.assertRaises(PluginAuthoringError):
                    inventory_archive(archive)


if __name__ == "__main__":
    unittest.main()
