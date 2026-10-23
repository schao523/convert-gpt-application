from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from obvious_one_plugin_framework.plugin_authoring.validation import ValidationIssue
from obvious_one_plugin_framework.plugin_onboarding.contract import (
    ExactStructuralCompatibility, OnboardingError, load_exact_structural_compatibility,
)
from obvious_one_plugin_framework.plugin_onboarding.inspection import (
    _canonical_bytes, _structural_findings,
)


class ExactStructuralCompatibilityTests(unittest.TestCase):
    def test_exact_path_binding_set_only(self) -> None:
        issues = (ValidationIssue("path_binding_missing", "skills/example/SKILL.md", "tools/run.py"),)
        findings = ({"code": issues[0].code, "path": issues[0].path, "detail": issues[0].detail},)
        profile = ExactStructuralCompatibility(
            archive_sha256="a" * 64, metadata_sha256="b" * 64,
            plugin_id="example", version="1.0.0",
            findings_sha256=sha256(_canonical_bytes(findings)).hexdigest(),
            findings_count=1, confirmed_by="Owner",
            decision_recorded_at="2026-10-23T18:37:12+08:00",
        )
        with patch("obvious_one_plugin_framework.plugin_onboarding.inspection.plugin_authoring.validate_plugin_tree", return_value=issues):
            self.assertEqual(_structural_findings(Path("unused"), profile), findings)
            with self.assertRaises(OnboardingError):
                _structural_findings(Path("unused"), None)
        for altered in (
            (ValidationIssue("path_binding_missing", "skills/other/SKILL.md", "tools/run.py"),),
            (ValidationIssue("secret_material", "skills/example/SKILL.md", "tools/run.py"),),
            (),
        ):
            with self.subTest(altered=altered), patch("obvious_one_plugin_framework.plugin_onboarding.inspection.plugin_authoring.validate_plugin_tree", return_value=altered):
                with self.assertRaises(OnboardingError):
                    _structural_findings(Path("unused"), profile)

    def test_profile_requires_exact_keys_and_approval(self) -> None:
        payload = {
            "schema": "workbench-exact-structural-compatibility-v1",
            "archive_sha256": "a" * 64, "metadata_sha256": "b" * 64,
            "plugin_id": "example", "version": "1.0.0",
            "findings_sha256": "c" * 64, "findings_count": 1,
            "approved": True, "confirmed_by": "Owner",
            "decision_recorded_at": "2026-10-23T18:37:12+08:00",
        }
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "profile.json"
            target.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(load_exact_structural_compatibility(target).plugin_id, "example")
            for change in ({"approved": False}, {"unknown": 1}, {"findings_count": 0}):
                target.write_text(json.dumps({**payload, **change}), encoding="utf-8")
                with self.assertRaises(OnboardingError):
                    load_exact_structural_compatibility(target)


if __name__ == "__main__":
    unittest.main()
