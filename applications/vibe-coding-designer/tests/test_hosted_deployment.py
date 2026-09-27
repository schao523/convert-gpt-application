from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from obvious_one_plugin_framework.content_policy import canonical_content_bytes
from obvious_one_plugin_framework.hosted_deployment_builder import build_hosted_deployment
from obvious_one_plugin_framework.hosted_deployment_contract import load_hosted_deployment_contract
from obvious_one_plugin_framework.hosted_deployment_planner import validate_hosted_deployment
from obvious_one_plugin_framework.hosted_deployment_verifier import verify_hosted_deployment


ROOT = Path(__file__).resolve().parents[1]
NATIVE_SKILLS = {
    "creating-implementation-prompts",
    "creating-repo-development-packages",
    "creating-software-design-specifications",
    "designing-data-services-and-workflows",
    "guiding-vibe-design-sessions",
    "planning-software-tests",
    "reviewing-software-design-specifications",
}
FORBIDDEN_ROOT_MEMBERS = {
    "conversion.json", "tests", "scripts", "openclaw", "docs/marketplace-approved-delta.json"
}


class VibeHostedDeploymentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)

    @staticmethod
    def skill_roots(names: list[str]) -> set[str]:
        return {
            name.split("/")[1]
            for name in names
            if name.startswith("skills/") and name.endswith("/SKILL.md")
        }

    def build(self, fixture: str, destination: str = "artifact"):
        contract = load_hosted_deployment_contract(ROOT / "tests" / "fixtures" / fixture)
        result = build_hosted_deployment(contract, self.base / destination)
        return contract, result

    def test_create_builds_seven_native_skills_and_explicit_router(self) -> None:
        contract, result = self.build("hosted-create.json")
        with zipfile.ZipFile(result.archive_path) as archive:
            names = archive.namelist()
            router = archive.read("skills/instructions/agents/openai.yaml").decode("utf-8")
        self.assertEqual(self.skill_roots(names), NATIVE_SKILLS | {"instructions"})
        self.assertIn("allow_implicit_invocation: false", router)
        self.assertIsNone(contract.identity_record)

    def test_update_preserves_identity_and_general_software_scope(self) -> None:
        contract, result = self.build("hosted-update.json")
        with zipfile.ZipFile(result.archive_path) as archive:
            manifest = json.loads(archive.read("plugin.json"))
            router = archive.read("skills/instructions/SKILL.md").decode("utf-8")
        self.assertEqual(manifest["name"], contract.identity_record.package_name)
        self.assertGreater(contract.target_version, contract.identity_record.last_confirmed_version)
        self.assertIn("never assume a Web GUI is required", router)
        self.assertIn("Produce design material rather than implementing", router)

    def test_native_skills_are_byte_derived_from_canonical_application(self) -> None:
        contract, result = self.build("hosted-create.json")
        validation = validate_hosted_deployment(contract)
        with zipfile.ZipFile(result.archive_path) as archive:
            for name in archive.namelist():
                if not name.startswith("skills/") or name.split("/")[1] not in NATIVE_SKILLS:
                    continue
                expected = canonical_content_bytes(
                    validation.source_paths[name], validation.content_policies[name]
                )
                self.assertEqual(archive.read(name), expected, name)

    def test_adapter_contains_only_manifests_presentation_assets_and_router(self) -> None:
        contract = load_hosted_deployment_contract(ROOT / "tests" / "fixtures" / "hosted-create.json")
        for mapping in contract.adapter_mappings:
            self.assertTrue(
                mapping.target in {"plugin.json", ".codex-plugin/plugin.json"}
                or mapping.target.startswith("assets/")
                or mapping.target.startswith("skills/instructions"),
                mapping.target,
            )
        self.assertEqual(
            {mapping.target for mapping in contract.canonical_mappings},
            {f"skills/{name}" for name in NATIVE_SKILLS},
        )

    def test_complete_archive_excludes_development_and_marketplace_files(self) -> None:
        _, result = self.build("hosted-create.json")
        with zipfile.ZipFile(result.archive_path) as archive:
            names = set(archive.namelist())
        for forbidden in FORBIDDEN_ROOT_MEMBERS:
            self.assertFalse(
                forbidden in names or any(name.startswith(forbidden.rstrip("/") + "/") for name in names),
                forbidden,
            )
        self.assertFalse(any(name.endswith(".py") for name in names))

    def test_create_build_is_deterministic_and_independently_verifiable(self) -> None:
        contract, first = self.build("hosted-create.json", "first")
        _, second = self.build("hosted-create.json", "second")
        self.assertEqual(first.artifact_sha256, second.artifact_sha256)
        self.assertEqual(
            {path.name: path.read_bytes() for path in first.output.iterdir()},
            {path.name: path.read_bytes() for path in second.output.iterdir()},
        )
        verified = verify_hosted_deployment(contract, first.output)
        self.assertEqual(verified.gates["complete_archive"], "PASS")
        self.assertEqual(verified.installation_status, "NOT VERIFIED")


if __name__ == "__main__":
    unittest.main()
