from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.contract import load_contract
from obvious_one_plugin_framework.knowledge_policy import validate_knowledge_policy
from obvious_one_plugin_framework.package_builder import build_package, verify_package


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "knowledge-policy-plugin"
CONTRACT = FIXTURE / "openclaw" / "distribution.json"


class KnowledgePolicyArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)

    def test_source_codex_shape_has_static_and_traceability_evidence_only(self) -> None:
        evidence = validate_knowledge_policy(
            FIXTURE,
            FIXTURE / "tests" / "coverage-matrix.md",
            require_coverage=True,
        )

        self.assertTrue((FIXTURE / ".codex-plugin" / "plugin.json").is_file())
        self.assertEqual(evidence.professional_reference_count, 1)
        self.assertEqual(evidence.general_reference_count, 1)
        self.assertEqual(evidence.package_structure, "STATICALLY VERIFIED")
        self.assertEqual(evidence.deterministic_discovery, "STATICALLY VERIFIED")
        self.assertEqual(evidence.coverage_traceability, "STATICALLY VERIFIED")
        self.assertEqual(evidence.behavior, "NOT VERIFIED")
        self.assertEqual(evidence.codex_execution, "NOT VERIFIED")
        self.assertEqual(evidence.openclaw_execution, "NOT VERIFIED")

    def test_openclaw_builds_are_deterministic_and_preserve_knowledge_bytes(self) -> None:
        contract = load_contract(CONTRACT)

        first = build_package(contract, self.output / "first")
        second = build_package(contract, self.output / "second")
        verified = verify_package(contract, first.output)

        self.assertEqual(first.content_sha256, second.content_sha256)
        self.assertEqual(first.content_sha256, verified.content_sha256)
        self.assertEqual(
            (first.output / "CONTENT-MANIFEST.json").read_bytes(),
            (second.output / "CONTENT-MANIFEST.json").read_bytes(),
        )

        manifest = json.loads(
            (first.output / "CONTENT-MANIFEST.json").read_text(encoding="utf-8")
        )
        records = {item["path"]: item for item in manifest["files"]}
        expected_paths = (
            "skills/designing-systems/references/design-rules.md",
            "skills/consulting-system-knowledge/references/architecture-guide.md",
            "skills/consulting-system-knowledge/references/knowledge-index.json",
        )
        for relative in expected_paths:
            with self.subTest(relative=relative):
                source_text = (FIXTURE / relative).read_text(encoding="utf-8")
                expected_bytes = source_text.encode("utf-8")
                self.assertEqual((first.output / relative).read_bytes(), expected_bytes)
                self.assertEqual(records[relative]["sha256"], sha256(expected_bytes).hexdigest())

    def test_unpacked_openclaw_bundle_remains_static_only(self) -> None:
        contract = load_contract(CONTRACT)
        built = build_package(contract, self.output / "openclaw")

        evidence = validate_knowledge_policy(built.output)

        self.assertEqual(evidence.package_structure, "STATICALLY VERIFIED")
        self.assertEqual(evidence.deterministic_discovery, "STATICALLY VERIFIED")
        self.assertEqual(evidence.coverage_traceability, "NOT VERIFIED")
        self.assertEqual(evidence.behavior, "NOT VERIFIED")
        self.assertEqual(evidence.codex_execution, "NOT VERIFIED")
        self.assertEqual(evidence.openclaw_execution, "NOT VERIFIED")


if __name__ == "__main__":
    unittest.main()
