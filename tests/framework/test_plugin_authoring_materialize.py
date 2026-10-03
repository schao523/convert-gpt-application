from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.plugin_authoring import (
    PluginAuthoringError,
    materialize_files,
    tree_manifest,
)


class MaterializeFilesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.sources = self.root / "sources"
        self.sources.mkdir()
        self.source = self.sources / "reference.bin"
        self.source.write_bytes(b"exact\x00reference\r\nbytes")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def inline_recipe(self, path: str, text: str) -> dict:
        canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        return {
            "path": path,
            "classification": "generated_text",
            "source_sha256": sha256(canonical).hexdigest(),
            "redistribution": {"state": "APPROVED", "evidence": "generated for this plugin"},
            "inline_text": text,
        }

    def source_recipe(self, path: str, source_path: str = "reference.bin") -> dict:
        return {
            "path": path,
            "classification": "approved_source",
            "source_sha256": sha256(self.source.read_bytes()).hexdigest(),
            "redistribution": {"state": "APPROVED", "evidence": "fixture owner approval"},
            "source_path": source_path,
        }

    def test_materialize_writes_exact_inline_and_source_bytes(self) -> None:
        json_bytes = (json.dumps({"z": 1, "a": 2}, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")
        recipes = [
            self.inline_recipe("skills/example/SKILL.md", "line one\r\nline two\r\n"),
            {
                "path": ".codex-plugin/plugin.json",
                "classification": "generated_json",
                "source_sha256": sha256(json_bytes).hexdigest(),
                "redistribution": {"state": "APPROVED", "evidence": "generated for this plugin"},
                "inline_json": {"z": 1, "a": 2},
            },
            self.source_recipe("skills/example/references/reference.bin"),
        ]
        destination = self.root / "candidate"

        manifest = materialize_files(recipes, self.sources, destination)

        self.assertEqual((destination / "skills/example/SKILL.md").read_bytes(), b"line one\nline two\n")
        self.assertEqual((destination / ".codex-plugin/plugin.json").read_bytes(), json_bytes)
        self.assertEqual((destination / "skills/example/references/reference.bin").read_bytes(), self.source.read_bytes())
        self.assertEqual(manifest, tree_manifest(destination))

    def test_materialize_rejects_collisions_links_and_source_escape(self) -> None:
        cases = [
            ([self.inline_recipe("Readme.md", "one"), self.inline_recipe("README.md", "two")], "materialize_path_collision"),
            ([self.inline_recipe("PLUGIN-BUILDER-MANIFEST.json", "reserved")], "materialize_reserved_path"),
            ([self.source_recipe("references/escape.bin", "../outside.bin")], "materialize_source_escape"),
        ]
        for index, (recipes, code) in enumerate(cases):
            with self.subTest(code=code):
                with self.assertRaises(PluginAuthoringError) as caught:
                    materialize_files(recipes, self.sources, self.root / f"candidate-{index}")
                self.assertEqual(caught.exception.code, code)

        linked = self.sources / "linked.bin"
        try:
            linked.symlink_to(self.source)
        except OSError:
            return
        recipe = self.source_recipe("references/linked.bin", "linked.bin")
        with self.assertRaises(PluginAuthoringError) as caught:
            materialize_files([recipe], self.sources, self.root / "linked-candidate")
        self.assertEqual(caught.exception.code, "materialize_source_link")

    def test_failed_materialization_preserves_previous_destination(self) -> None:
        destination = self.root / "candidate"
        destination.mkdir()
        (destination / "preserve.txt").write_text("original", encoding="utf-8")
        recipe = self.source_recipe("references/reference.bin")
        recipe["source_sha256"] = "0" * 64

        with self.assertRaises(PluginAuthoringError) as caught:
            materialize_files([recipe], self.sources, destination)
        self.assertEqual(caught.exception.code, "materialize_source_hash_mismatch")
        self.assertEqual((destination / "preserve.txt").read_text(encoding="utf-8"), "original")
        self.assertEqual([path.name for path in destination.iterdir()], ["preserve.txt"])


if __name__ == "__main__":
    unittest.main()
