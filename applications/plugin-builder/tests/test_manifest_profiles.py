from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.manifest_profile import validate_manifest_profile


VOCABULARY = ROOT / "contracts/openai-interface-vocabulary-v1.json"


class ManifestProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.manifest = {
            "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "name": "example",
            "version": "1.0.0",
            "description": "協助使用者完成清楚而可追溯的工作。",
            "author": {"name": "Example Developer"},
            "extensions": {"com.openai": {"interface": {
                "displayName": "Example",
                "shortDescription": "Clear traceable assistance.",
                "longDescription": "Provide clear and traceable assistance for the approved workflow.",
                "developerName": "Example Developer",
                "category": "Education",
                "capabilities": ["Interactive", "Read"],
                "defaultPrompt": "Help me complete this approved workflow.",
            }}},
        }
        (self.root / "plugin.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def decision(self, *, profile: str = "PRIVATE_LOCAL", categories=None, capabilities=None) -> dict:
        return {
            "target": "OPENAI_DESKTOP",
            "profile": profile,
            "vocabulary_version": "obvious-one-openai-interface-v1",
            "extensions": {
                "categories": sorted(categories or []),
                "capabilities": sorted(capabilities or []),
            },
        }

    def write_manifest(self) -> None:
        (self.root / "plugin.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_vocabulary_casing_and_explicit_extensions(self) -> None:
        self.manifest["extensions"]["com.openai"]["interface"]["category"] = "education"
        self.write_manifest()
        rejected = validate_manifest_profile(self.root, self.decision(), VOCABULARY)
        self.assertIn("manifest.category_unknown:education", rejected.diagnostics)

        accepted = validate_manifest_profile(
            self.root, self.decision(categories=["education"]), VOCABULARY
        )
        self.assertEqual(accepted.diagnostics, ())

    def test_private_local_requires_descriptive_identity_and_interface(self) -> None:
        interface = self.manifest["extensions"]["com.openai"]["interface"]
        interface["defaultPrompt"] = "TODO"
        self.manifest["author"] = {"name": ""}
        self.write_manifest()
        report = validate_manifest_profile(self.root, self.decision(), VOCABULARY)
        self.assertIn("manifest.author_invalid", report.diagnostics)
        self.assertIn("manifest.default_prompt_placeholder", report.diagnostics)

    def test_release_profile_blocks_unresolved_listing_metadata(self) -> None:
        private = validate_manifest_profile(self.root, self.decision(), VOCABULARY)
        self.assertEqual(private.diagnostics, ())
        self.assertEqual(private.as_dict()["listing_status"]["homepage"], "UNRESOLVED")

        release = validate_manifest_profile(
            self.root, self.decision(profile="RELEASE_READY"), VOCABULARY
        )
        self.assertTrue(any(item.startswith("manifest.release_metadata_unresolved:") for item in release.diagnostics))

    def test_listing_statuses_and_unicode_are_deterministic(self) -> None:
        self.manifest["homepage"] = "https://example.com"
        self.manifest["repository"] = None
        self.write_manifest()
        first = validate_manifest_profile(self.root, self.decision(), VOCABULARY).as_dict()
        second = validate_manifest_profile(self.root, self.decision(), VOCABULARY).as_dict()
        self.assertEqual(first, second)
        self.assertEqual(first["listing_status"]["homepage"], "SUPPLIED")
        self.assertEqual(first["listing_status"]["repository"], "NOT_APPLICABLE")


if __name__ == "__main__":
    unittest.main()
