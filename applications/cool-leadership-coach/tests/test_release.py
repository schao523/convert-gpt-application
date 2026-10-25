from __future__ import annotations

import importlib.util
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from obvious_one_plugin_framework import plugin_authoring


APPLICATION = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("leadership_release_builder", APPLICATION / "scripts/build_marketplace_release.py")
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ReleaseTests(unittest.TestCase):
    def test_pinned_source_and_identity(self) -> None:
        builder.verify_source(APPLICATION)
        derivative = json.loads((APPLICATION / "imported-plugin/WORKBENCH-DERIVATION-MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(derivative["source_archive_sha256"], "7603ec8f8d718b776e34ee1d8d69bf8ae19681c37b64b52415a6f19520fc640b")
        self.assertEqual(derivative["runtime_evidence"], "NOT VERIFIED")
        self.assertEqual(len(list((APPLICATION / "imported-plugin/skills").glob("*/SKILL.md"))), 6)
        source = {item["path"]: item["sha256"] for item in derivative["source_members"]}
        target = {item["path"]: item["sha256"] for item in derivative["target_members_excluding_self"]}
        changed = {path for path in source.keys() & target.keys() if source[path] != target[path]}
        self.assertEqual(changed, set(derivative["transformed_paths"]))
        for path in source:
            if path.endswith(".pdf") or path.endswith("/SKILL.md"):
                self.assertEqual(source[path], target[path], path)
        sidecar_bytes = (APPLICATION / "docs/source-package-metadata.json").read_bytes()
        self.assertEqual(sha256(sidecar_bytes).hexdigest(), "0c5b33feaeca6ae767150419dae09ce0add4312900e6cf99521d9b1a3ab6d32a")
        sidecar = json.loads(sidecar_bytes)
        source_manifest = json.loads((APPLICATION / "docs/source-plugin-builder-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(sidecar["schema"], "plugin-builder-package-v3")
        self.assertEqual(sidecar["archive_sha256"], derivative["source_archive_sha256"])
        self.assertEqual(sidecar["plugin_id"], derivative["source_plugin_id"])
        self.assertEqual(sidecar["runtime_realization_state"], "NOT VERIFIED")
        self.assertEqual(
            {item["path"]: item["sha256"] for item in sidecar["candidate_members"] if item["path"] != "PLUGIN-BUILDER-MANIFEST.json"},
            {item["path"]: item["sha256"] for item in source_manifest["members"]},
        )

    def test_marketplace_build_preserves_every_imported_byte(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = builder.build(APPLICATION, Path(temporary))
            expected = {member.path: member.sha256 for member in plugin_authoring.tree_manifest(APPLICATION / "imported-plugin")}
            observed = {member.path: member.sha256 for member in plugin_authoring.tree_manifest(target)}
            self.assertEqual({key: observed[key] for key in expected}, expected)
            self.assertEqual(set(observed) - set(expected), {"LICENSE"})
            self.assertEqual((target / "LICENSE").read_bytes(), (APPLICATION / "LICENSE").read_bytes())
            with self.assertRaisesRegex(ValueError, "marketplace_target_exists"):
                builder.build(APPLICATION, Path(temporary))

    def test_changed_imported_byte_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "application"
            shutil.copytree(APPLICATION / "imported-plugin", copied / "imported-plugin")
            shutil.copytree(APPLICATION / "docs", copied / "docs")
            path = copied / "imported-plugin/README.md"
            path.write_bytes(path.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "imported_plugin_tree_mismatch"):
                builder.verify_source(copied)


if __name__ == "__main__":
    unittest.main()
