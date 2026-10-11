from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.plugin_onboarding.contract import (
    WorkbenchRepairMetadata,
    load_onboarding_metadata,
)
from tests.framework.plugin_onboarding_fixtures import (
    canonical_bytes,
    write_legacy_repair_fixture,
)


class VersionedLegacyProfileContractTests(unittest.TestCase):
    def test_workbench_metadata_preserves_versioned_legacy_source_profile(self) -> None:
        with tempfile.TemporaryDirectory(prefix="versioned-legacy-profile-") as name:
            root = Path(name)
            fixture = write_legacy_repair_fixture(root / "fixture")
            contract_path = root / "repair.json"
            contract_path.write_bytes(canonical_bytes(fixture.contract_payload))

            from obvious_one_plugin_framework.plugin_onboarding import (
                load_repair_contract,
                repair_delegated_reference_archive,
            )

            result = repair_delegated_reference_archive(
                fixture.archive,
                load_repair_contract(contract_path),
                root / "repaired.zip",
                root / "metadata.json",
            )
            payload = json.loads(result.metadata.read_text(encoding="utf-8"))
            payload["schema"] = "workbench-repaired-plugin-v2"
            payload["input_profile"] = "PLUGIN_BUILDER_VERSIONED_LEGACY_V1"
            payload["tool_bindings"] = []
            payload["tool_contracts_sha256"] = sha256(canonical_bytes([])).hexdigest()
            payload["offline_validators"] = []
            payload["offline_validators_sha256"] = sha256(canonical_bytes([])).hexdigest()
            payload["producer_claims"] = {
                "schema": "plugin-builder-manifest-v1.0.3-runtime-native-reference-access",
                "verification_state": "NOT VERIFIED",
            }
            result.metadata.write_bytes(canonical_bytes(payload))

            metadata = load_onboarding_metadata(result.metadata)

            self.assertIsInstance(metadata, WorkbenchRepairMetadata)
            self.assertEqual(
                metadata.input_profile,
                "PLUGIN_BUILDER_VERSIONED_LEGACY_V1",
            )
            self.assertEqual(
                metadata.producer_claims["schema"],
                "plugin-builder-manifest-v1.0.3-runtime-native-reference-access",
            )
            self.assertEqual(set(metadata.evidence_states.values()), {"NOT VERIFIED"})

    def test_v2_workbench_metadata_carries_hash_bound_tool_declarations(self) -> None:
        with tempfile.TemporaryDirectory(prefix="versioned-legacy-tools-") as name:
            root = Path(name)
            fixture = write_legacy_repair_fixture(root / "fixture")
            contract_path = root / "repair.json"
            contract_path.write_bytes(canonical_bytes(fixture.contract_payload))
            from obvious_one_plugin_framework.plugin_onboarding import (
                load_repair_contract,
                repair_delegated_reference_archive,
            )

            result = repair_delegated_reference_archive(
                fixture.archive,
                load_repair_contract(contract_path),
                root / "repaired.zip",
                root / "metadata.json",
            )
            payload = json.loads(result.metadata.read_text(encoding="utf-8"))
            bindings = [{"tool_id": "validator", "contract_sha256": "a" * 64}]
            contracts = [{"schema": "plugin-builder-application-tool-v1", "id": "validator"}]
            payload.update(
                {
                    "schema": "workbench-repaired-plugin-v2",
                    "input_profile": "PLUGIN_BUILDER_VERSIONED_LEGACY_V1",
                    "tool_bindings": bindings,
                    "tool_contracts_sha256": sha256(canonical_bytes(contracts)).hexdigest(),
                    "offline_validators": [],
                    "offline_validators_sha256": sha256(canonical_bytes([])).hexdigest(),
                }
            )
            result.metadata.write_bytes(canonical_bytes(payload))

            metadata = load_onboarding_metadata(result.metadata)

            self.assertEqual(metadata.schema, "workbench-repaired-plugin-v2")
            self.assertEqual(tuple(metadata.tool_bindings), tuple(bindings))
            self.assertEqual(metadata.tool_contracts_sha256, payload["tool_contracts_sha256"])

    def test_v2_workbench_metadata_carries_hash_bound_offline_validators(self) -> None:
        with tempfile.TemporaryDirectory(prefix="versioned-legacy-offline-") as name:
            root = Path(name)
            fixture = write_legacy_repair_fixture(root / "fixture")
            contract_path = root / "repair.json"
            contract_path.write_bytes(canonical_bytes(fixture.contract_payload))
            from obvious_one_plugin_framework.plugin_onboarding import (
                load_repair_contract,
                repair_delegated_reference_archive,
            )

            result = repair_delegated_reference_archive(
                fixture.archive,
                load_repair_contract(contract_path),
                root / "repaired.zip",
                root / "metadata.json",
            )
            payload = json.loads(result.metadata.read_text(encoding="utf-8"))
            validators = [
                {
                    "id": "package-validator",
                    "files": ["scripts/validate.py"],
                    "runtime_role": "OFFLINE_PACKAGE_VALIDATION_ONLY",
                    "required": False,
                    "installed_runtime_callable": False,
                    "source_contract_sha256": "b" * 64,
                }
            ]
            payload.update(
                {
                    "schema": "workbench-repaired-plugin-v2",
                    "input_profile": "PLUGIN_BUILDER_VERSIONED_LEGACY_V1",
                    "tool_bindings": [],
                    "tool_contracts_sha256": sha256(canonical_bytes([])).hexdigest(),
                    "offline_validators": validators,
                    "offline_validators_sha256": sha256(
                        canonical_bytes(validators)
                    ).hexdigest(),
                }
            )
            result.metadata.write_bytes(canonical_bytes(payload))

            metadata = load_onboarding_metadata(result.metadata)

            self.assertEqual(metadata.offline_validators[0]["id"], "package-validator")
            self.assertEqual(
                metadata.offline_validators[0]["files"],
                ("scripts/validate.py",),
            )
            self.assertEqual(
                metadata.offline_validators_sha256,
                payload["offline_validators_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
