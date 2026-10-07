from __future__ import annotations

import unittest

from obvious_one_plugin_framework.plugin_authoring.capabilities import (
    validate_capability_contract,
    validate_capability_register,
)


def capability(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "plugin-builder-capability-v1",
        "id": "normalize-content",
        "requirement_ids": ["RQ1"],
        "skill_bindings": ["answering-requests"],
        "realization_need": "TOOL_REQUIRED",
        "tool_id": "normalize-input",
        "runtime_targets": ["ChatGPT Work Local/Desktop", "Codex"],
        "evidence_targets": ["STRUCTURE", "OPERATION", "INSTALLED_REALIZATION", "BEHAVIOR"],
    }
    payload.update(changes)
    return payload


class CapabilityContractTests(unittest.TestCase):
    def test_valid_contract_is_immutable_and_preserves_exact_identity(self) -> None:
        original = capability()
        result = validate_capability_contract(original)
        self.assertEqual(result.errors, ())
        self.assertEqual(result.blockers, ())
        self.assertEqual(result.id, "normalize-content")
        self.assertEqual(result.payload["requirement_ids"], ("RQ1",))
        original["requirement_ids"].append("RQ2")  # type: ignore[union-attr]
        self.assertEqual(result.payload["requirement_ids"], ("RQ1",))
        with self.assertRaises(TypeError):
            result.payload["id"] = "changed"  # type: ignore[index]

    def test_exact_keys_stable_ids_and_modes_are_enforced(self) -> None:
        malformed = capability(extra=True, id="Bad_ID", realization_need="MODEL_ONLY")
        malformed.pop("evidence_targets")
        result = validate_capability_contract(malformed)
        self.assertEqual(
            result.errors,
            (
                "capability.Bad_ID.evidence_targets_invalid",
                "capability.Bad_ID.id_invalid",
                "capability.Bad_ID.invalid_keys",
                "capability.Bad_ID.realization_need_unsupported",
            ),
        )

    def test_skill_only_forbids_tool_and_tool_required_requires_one(self) -> None:
        skill_only = validate_capability_contract(
            capability(realization_need="SKILL_ONLY", tool_id="normalize-input")
        )
        missing_tool = validate_capability_contract(capability(tool_id=None))
        self.assertEqual(
            skill_only.errors,
            ("capability.normalize-content.tool_id_forbidden",),
        )
        self.assertEqual(
            missing_tool.errors,
            ("capability.normalize-content.tool_id_required",),
        )

    def test_bindings_targets_and_evidence_targets_are_closed(self) -> None:
        result = validate_capability_contract(
            capability(
                requirement_ids=[],
                skill_bindings=[],
                runtime_targets=["Codex"],
                evidence_targets=["STRUCTURE", "UNKNOWN"],
            )
        )
        self.assertEqual(
            result.errors,
            (
                "capability.normalize-content.evidence_targets_invalid",
                "capability.normalize-content.requirement_binding_required",
                "capability.normalize-content.runtime_targets_incomplete",
                "capability.normalize-content.skill_binding_required",
            ),
        )

    def test_register_rejects_duplicates_and_unknown_bindings_deterministically(self) -> None:
        first = capability(requirement_ids=["RQ2", "RQ1"], skill_bindings=["missing-skill"])
        errors, blockers = validate_capability_register(
            [first, capability()],
            requirement_ids={"RQ1"},
            skill_names={"answering-requests"},
        )
        self.assertEqual(blockers, ())
        self.assertEqual(
            errors,
            (
                "capability.normalize-content.duplicate_id",
                "capability.normalize-content.skill_binding_unknown:missing-skill",
                "capability.normalize-content.unknown_requirement:RQ2",
            ),
        )


if __name__ == "__main__":
    unittest.main()
