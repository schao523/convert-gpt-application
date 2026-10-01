from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT.parents[1] / ".tmp" / "plugin-builder-release-tests"
PLUGIN_PREFIX = "plugins/plugin-builder/"
EXPECTED_SOURCE_PATHS = {
    "plugin.json",
    ".codex-plugin/plugin.json",
    "README.md",
    "DISTRIBUTION.md",
    "LICENSE",
    "PRIVACY.md",
    "SECURITY.md",
    "THIRD_PARTY_CONTENT.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/application-invariants.md",
    "docs/runtime-compatibility.md",
    "scripts/build_marketplace_release.py",
    "scripts/distribution_audit.py",
    "scripts/plugin_builder.py",
    "scripts/plugin_builder_core/__init__.py",
    "scripts/plugin_builder_core/approvals.py",
    "scripts/plugin_builder_core/bootstrap.py",
    "scripts/plugin_builder_core/candidate.py",
    "scripts/plugin_builder_core/evidence.py",
    "scripts/plugin_builder_core/handoff_normalization.py",
    "scripts/plugin_builder_core/implementation_plan.py",
    "scripts/plugin_builder_core/inspection.py",
    "scripts/plugin_builder_core/packaging.py",
    "scripts/plugin_builder_core/result.py",
    "scripts/plugin_builder_core/session_contract.py",
    "scripts/plugin_builder_core/session_state.py",
    "scripts/plugin_builder_core/tool_contract.py",
    "scripts/plugin_builder_core/tool_verification.py",
    "scripts/plugin_builder_core/update.py",
    "scripts/plugin_builder_core/update_candidate.py",
    "scripts/plugin_builder_core/verification.py",
    "scripts/vendor/obvious_one_plugin_framework/__init__.py",
    "scripts/vendor/obvious_one_plugin_framework/plugin_authoring/__init__.py",
    "scripts/vendor/obvious_one_plugin_framework/plugin_authoring/archive.py",
    "scripts/vendor/obvious_one_plugin_framework/plugin_authoring/identity.py",
    "scripts/vendor/obvious_one_plugin_framework/plugin_authoring/materialize.py",
    "scripts/vendor/obvious_one_plugin_framework/plugin_authoring/manifests.py",
    "scripts/vendor/obvious_one_plugin_framework/plugin_authoring/tools.py",
    "scripts/vendor/obvious_one_plugin_framework/plugin_authoring/validation.py",
    "skills/building-and-updating-plugins/SKILL.md",
    "skills/building-and-updating-plugins/agents/openai.yaml",
    "skills/building-and-updating-plugins/references/candidate-and-update-contract.md",
    "skills/building-and-updating-plugins/references/application-tool-contract.md",
    "skills/guiding-plugin-builder-sessions/SKILL.md",
    "skills/guiding-plugin-builder-sessions/agents/openai.yaml",
    "skills/guiding-plugin-builder-sessions/references/session-workflow.md",
    "skills/guiding-plugin-builder-sessions/references/state-and-recovery.md",
    "skills/planning-plugin-implementations/SKILL.md",
    "skills/planning-plugin-implementations/agents/openai.yaml",
    "skills/planning-plugin-implementations/references/input-and-plan-contract.md",
    "skills/planning-plugin-implementations/references/requirement-coverage-contract.md",
    "skills/verifying-and-packaging-plugins/SKILL.md",
    "skills/verifying-and-packaging-plugins/agents/openai.yaml",
    "skills/verifying-and-packaging-plugins/references/evidence-and-package-contract.md",
    "skills/verifying-and-packaging-plugins/references/tool-evidence-contract.md",
}


def load_release():
    path = ROOT / "scripts" / "build_marketplace_release.py"
    spec = importlib.util.spec_from_file_location("plugin_builder_marketplace_release", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load release module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tree_identity(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class MarketplaceReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    def test_release_is_deterministic_and_contains_exact_allowlist(self) -> None:
        release = load_release()
        expected_paths = tuple(sorted(PLUGIN_PREFIX + path for path in EXPECTED_SOURCE_PATHS))
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            destination = Path(temp) / "marketplace"
            first = release.build_release(ROOT, destination, "0.1.1")
            first_manifest = (destination / ".release-manifest.json").read_bytes()
            second = release.build_release(ROOT, destination, "0.1.1")
            second_manifest = (destination / ".release-manifest.json").read_bytes()

            self.assertEqual(first.paths, expected_paths)
            self.assertEqual(second.paths, expected_paths)
            self.assertEqual(first.sha256, second.sha256)
            self.assertEqual(first.total_bytes, second.total_bytes)
            self.assertEqual(first_manifest, second_manifest)
            recorded = json.loads(second_manifest)
            self.assertEqual(recorded["plugin_id"], "plugin-builder")
            self.assertEqual(recorded["version"], "0.1.1")
            self.assertEqual(
                [item["path"] for item in recorded["files"]], list(expected_paths)
            )
            self.assertFalse(
                any("docs/approved-design/" in path for path in second.paths)
            )

    def test_release_enforces_plugin_identity_and_version_before_mutation(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            temp_root = Path(temp)
            copied = temp_root / "source"
            shutil.copytree(ROOT, copied)
            destination = temp_root / "marketplace"

            with self.assertRaisesRegex(ValueError, "identity or version mismatch"):
                release.build_release(copied, destination, "9.9.9")
            self.assertFalse(destination.exists())

            manifest_path = copied / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["name"] = "wrong-plugin"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "identity or version mismatch"):
                release.build_release(copied, destination, "0.1.1")
            self.assertFalse(destination.exists())

    def test_release_refuses_nonempty_unmarked_destination(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            destination = Path(temp) / "marketplace"
            destination.mkdir()
            sentinel = destination / "owner-file.txt"
            sentinel.write_text("preserve\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "nonempty destination"):
                release.build_release(ROOT, destination, "0.1.1")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve\n")
            self.assertEqual(list(destination.iterdir()), [sentinel])

    def test_failed_rebuild_preserves_previous_artifact_and_manifest(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            temp_root = Path(temp)
            destination = temp_root / "marketplace"
            release.build_release(ROOT, destination, "0.1.1")
            before = tree_identity(destination)

            copied = temp_root / "unsafe-source"
            shutil.copytree(ROOT, copied)
            with (copied / "scripts" / "plugin_builder.py").open(
                "a", encoding="utf-8", newline="\n"
            ) as stream:
                stream.write('\ntoken = "ghp_abcdefghijklmnopqrstuvwxyz123456"\n')

            with self.assertRaisesRegex(ValueError, "source audit failed"):
                release.build_release(copied, destination, "0.1.1")
            self.assertEqual(tree_identity(destination), before)

    def test_each_transaction_move_failure_preserves_previous_release(self) -> None:
        release = load_release()
        for failing_move in range(1, 5):
            with self.subTest(failing_move=failing_move), tempfile.TemporaryDirectory(
                dir=TEMP_ROOT
            ) as temp:
                destination = Path(temp) / "marketplace"
                release.build_release(ROOT, destination, "0.1.1")
                before = tree_identity(destination)
                real_replace = release.os.replace
                call_count = 0

                def fail_one_move(source, target):
                    nonlocal call_count
                    call_count += 1
                    if call_count == failing_move:
                        raise PermissionError(f"injected move failure {failing_move}")
                    return real_replace(source, target)

                with mock.patch.object(release.os, "replace", side_effect=fail_one_move):
                    with self.assertRaisesRegex(
                        PermissionError, f"injected move failure {failing_move}"
                    ):
                        release.build_release(ROOT, destination, "0.1.1")

                self.assertEqual(tree_identity(destination), before)

    def test_undeclared_codex_metadata_is_not_packaged(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            temp_root = Path(temp)
            copied = temp_root / "source"
            shutil.copytree(ROOT, copied)
            private = copied / ".codex-plugin" / "private-notes.md"
            private.write_text("internal notes\n", encoding="utf-8")
            destination = temp_root / "marketplace"

            report = release.build_release(copied, destination, "0.1.1")

            self.assertNotIn(
                "plugins/plugin-builder/.codex-plugin/private-notes.md", report.paths
            )
            self.assertFalse(
                (destination / "plugins/plugin-builder/.codex-plugin/private-notes.md").exists()
            )

    def test_release_requires_rights_evidence_before_mutation(self) -> None:
        release = load_release()
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            temp_root = Path(temp)
            copied = temp_root / "source"
            shutil.copytree(ROOT, copied)
            (copied / "docs" / "source-decisions.md").unlink()
            destination = temp_root / "marketplace"

            with self.assertRaisesRegex(ValueError, "rights and provenance evidence missing"):
                release.build_release(copied, destination, "0.1.1")
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
