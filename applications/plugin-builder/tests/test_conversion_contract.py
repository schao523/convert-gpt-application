import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import unittest
import hashlib

from obvious_one_plugin_framework.plugin_authoring import validate_manifest_pair


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE_SHA256 = "8edde15b6bd0e658990c3a354b85ea90b93bfa1c17216c7b11928f8284c3f497"
NORMALIZED_PACKAGE_SHA256 = "953747ad9f92d05dc29a049359fa06227fc2f8cc8590242cd4d1f09e17f82b21"


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class ConversionContractTests(unittest.TestCase):
    def test_identity_scope_and_provenance_are_explicit(self) -> None:
        config = load_json("conversion.json")
        manifest = load_json(".codex-plugin/plugin.json")
        portable = load_json("plugin.json")
        scope = load_json("docs/phase-one-scope.json")
        inventory = load_json("docs/source-inventory.json")
        runtime = (ROOT / "docs/runtime-compatibility.md").read_text(encoding="utf-8")

        self.assertEqual(config["schema_version"], 2)
        self.assertEqual(config["application_id"], "plugin-builder")
        self.assertEqual(config["plugin_id"], "plugin-builder")
        self.assertEqual(
            config["provenance"]["inventory_rules"][0]["classification"],
            "approved-design-internal",
        )
        self.assertEqual(manifest["name"], "plugin-builder")
        self.assertEqual(manifest["version"], "0.1.1")
        self.assertEqual(portable["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual((portable["name"], portable["version"]), (manifest["name"], manifest["version"]))
        self.assertEqual(portable["extensions"]["com.openai"]["interface"], manifest["interface"])
        self.assertEqual(validate_manifest_pair(ROOT), ())

        self.assertEqual(scope["scope"], "OPENAI_ONLY_PHASE_ONE")
        self.assertEqual(scope["source_package_sha256"], SOURCE_PACKAGE_SHA256)
        self.assertEqual(scope["normalized_package_sha256"], NORMALIZED_PACKAGE_SHA256)
        self.assertEqual(
            set(scope["target_runtimes"]),
            {"ChatGPT Work Local/Desktop", "Codex"},
        )
        self.assertGreaterEqual(set(scope["excluded_runtimes"]), {"OpenClaw", "Claude"})
        self.assertEqual(scope["publication_state"], "NOT_PERFORMED")
        self.assertEqual(scope["release_state"], "NOT_PERFORMED")

        serialized_inventory = json.dumps(inventory, ensure_ascii=False)
        self.assertNotRegex(serialized_inventory, re.compile(r"[A-Za-z]:[\\/]"))
        self.assertNotIn("/Users/", serialized_inventory)
        self.assertNotIn("\\Users\\", serialized_inventory)
        for item in inventory["source_inventory"]:
            path = PurePosixPath(item["path"])
            self.assertFalse(path.is_absolute(), item["path"])
            self.assertNotIn("..", path.parts, item["path"])

        self.assertIn("| OpenClaw | NOT APPLICABLE |", runtime)
        self.assertIn("| Codex | RUNTIME VERIFIED |", runtime)
        self.assertIn("| ChatGPT Work Local/Desktop | RUNTIME VERIFIED |", runtime)

    def test_approved_design_snapshot_matches_normalized_manifest(self) -> None:
        approved = ROOT / "docs/approved-design"
        package_manifest = json.loads(
            (approved / "package-manifest.json").read_text(encoding="utf-8")
        )
        inventory = load_json("docs/source-inventory.json")
        inventory_hashes = {
            item["path"]: item["sha256"] for item in inventory["source_inventory"]
        }
        declared = {
            item["file"]: item["sha256"] for item in package_manifest["artifacts"]
        }
        declared[package_manifest["canonical_handoff"]["file"]] = package_manifest[
            "canonical_handoff"
        ]["sha256"]
        declared.update(
            {item["file"]: item["sha256"] for item in package_manifest["supporting_files"]}
        )

        files = sorted(path.name for path in approved.iterdir() if path.is_file())
        self.assertEqual(set(files), set(inventory_hashes))
        self.assertEqual(set(files) - {"package-manifest.json"}, set(declared))
        for filename in files:
            digest = hashlib.sha256((approved / filename).read_bytes()).hexdigest()
            self.assertEqual(digest, inventory_hashes[filename], filename)
            if filename in declared:
                self.assertEqual(digest, declared[filename], filename)

        self.assertEqual(
            package_manifest["gate"], "APPROVED WITH NONBLOCKING DECISIONS"
        )
        self.assertEqual(
            package_manifest["source_archive_sha256"], SOURCE_PACKAGE_SHA256
        )
        self.assertEqual(package_manifest["normalization"], "format-only")
        self.assertFalse((approved / "handoff_manifest.json").exists())

        for filename in files:
            relative = (approved / filename).relative_to(ROOT).as_posix()
            attribute = subprocess.check_output(
                ["git", "check-attr", "text", "--", relative],
                cwd=ROOT,
                text=True,
            ).strip()
            self.assertTrue(attribute.endswith("text: unset"), attribute)

    def test_requirement_coverage_matrix_is_complete_and_honest(self) -> None:
        matrix = (ROOT / "tests/coverage-matrix.md").read_text(encoding="utf-8")
        expected_ids = {
            *(f"RQ{index}" for index in range(1, 8)),
            *(f"AC{index}" for index in range(1, 11)),
            *(f"T{index}" for index in range(1, 8)),
        }
        rows: dict[str, list[str]] = {}
        for line in matrix.splitlines():
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and cells[0] in expected_ids:
                self.assertNotIn(cells[0], rows, cells[0])
                rows[cells[0]] = cells

        self.assertEqual(set(rows), expected_ids)
        allowed_states = {
            "EXPECTED",
            "STATICALLY VERIFIED",
            "RUNTIME VERIFIED",
            "NOT VERIFIED",
        }
        for requirement_id, cells in rows.items():
            self.assertEqual(len(cells), 4, requirement_id)
            self.assertTrue(cells[1], requirement_id)
            self.assertTrue(cells[2], requirement_id)
            self.assertIn(cells[3], allowed_states, requirement_id)

        self.assertIn("| RUNTIME-OPENCLAW | OpenClaw | Excluded phase-one runtime | NOT APPLICABLE |", matrix)
        self.assertIn("| RUNTIME-CLAUDE | Claude | Excluded phase-one runtime | NOT APPLICABLE |", matrix)

    def test_configured_verification_registers_phase_two_smokes(self) -> None:
        config = load_json("conversion.json")
        command_ids = {item["id"] for item in config["verification"]["commands"]}
        self.assertEqual(
            command_ids,
            {"runtime-status", "session-validator", "create-smoke", "update-smoke", "bundled-local-tool-smoke"},
        )


if __name__ == "__main__":
    unittest.main()
