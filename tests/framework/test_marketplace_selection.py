from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from obvious_one_plugin_framework.marketplace import (
    load_preparation_catalog,
    prepare_marketplace,
)
from obvious_one_plugin_framework.marketplace_ci import render_marketplace_selector
from tests.framework import test_marketplace as marketplace_fixture


class MarketplaceSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = marketplace_fixture.MarketplaceTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.catalog = load_preparation_catalog(fixture.catalog_path, fixture.repository)
        prepare_marketplace(self.catalog, fixture.baseline, fixture.output)
        self.root = fixture.output
        self.selector = self.root / "tools" / "select_marketplace_plugins.py"
        self._git("init")
        self._git("config", "user.email", "tests@example.invalid")
        self._git("config", "user.name", "Marketplace Tests")
        self._git("add", ".")
        self._git("commit", "-m", "baseline")
        self.base = self._git("rev-parse", "HEAD").stdout.strip()

    def _git(self, *arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd or self.root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def _commit(self, message: str = "change") -> str:
        self._git("add", "-A")
        self._git("commit", "-m", message)
        return self._git("rev-parse", "HEAD").stdout.strip()

    def _run(
        self,
        *,
        base: str | None = None,
        head: str | None = None,
        all_reason: str | None = None,
        root: Path | None = None,
        environment_overrides: dict[str, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        stage = root or self.root
        command = [
            sys.executable,
            "-B",
            str(stage / "tools" / "select_marketplace_plugins.py"),
            "--registry",
            str(stage / ".obvious-one-validation.json"),
        ]
        if all_reason is not None:
            command.extend(["--all", all_reason])
        else:
            command.extend(["--base", base or self.base, "--head", head or "HEAD"])
        command.append("--json")
        environment = os.environ.copy()
        environment["PYTHONPATH"] = ""
        environment.update(environment_overrides or {})
        completed = subprocess.run(
            command,
            cwd=stage,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
        )
        return completed, json.loads(completed.stdout)

    def _assert_selection(
        self,
        payload: dict[str, object],
        mode: str,
        plugins: list[str],
        reason: str | None = None,
    ) -> None:
        self.assertEqual(payload["result_schema_version"], 1)
        self.assertEqual(payload["operation"], "select-marketplace-plugins")
        self.assertEqual(payload["status"], "PASS")
        evidence = payload["evidence"]
        self.assertEqual(evidence["selection_mode"], mode)
        self.assertEqual(evidence["selected_plugins"], plugins)
        self.assertEqual(evidence["matrix"], {"plugin": plugins})
        self.assertEqual(evidence["fallback_reason"], reason)
        self.assertRegex(evidence["changed_paths_sha256"], r"^[0-9a-f]{64}$")

    def test_selects_one_or_multiple_destination_owners_in_sorted_order(self) -> None:
        legacy = self.root / "plugins" / "legacy" / ".codex-plugin" / "plugin.json"
        legacy.write_bytes(legacy.read_bytes() + b"\n")
        head = self._commit("legacy")

        completed, payload = self._run(head=head)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self._assert_selection(payload, "AFFECTED", ["legacy"])

        modern = self.root / "plugins" / "modern" / ".codex-plugin" / "plugin.json"
        modern.write_bytes(modern.read_bytes() + b"\n")
        head = self._commit("modern")
        _, payload = self._run(head=head)
        self._assert_selection(payload, "AFFECTED", ["legacy", "modern"])

    def test_empty_delta_and_manual_dispatch_have_explicit_modes(self) -> None:
        completed, empty = self._run(base=self.base, head=self.base)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self._assert_selection(empty, "NONE", [])
        self.assertEqual(empty["evidence"]["changed_path_count"], 0)

        completed, manual = self._run(all_reason="workflow_dispatch")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self._assert_selection(
            manual,
            "ALL",
            ["legacy", "modern"],
            "workflow_dispatch",
        )

    def test_delete_rename_and_copy_evaluate_every_endpoint(self) -> None:
        deleted = self.root / "openclaw" / "legacy" / "README.md"
        deleted.unlink()
        head = self._commit("delete")
        _, payload = self._run(head=head)
        self._assert_selection(payload, "AFFECTED", ["legacy"])

        source = self.root / "plugins" / "modern" / ".codex-plugin" / "plugin.json"
        destination = self.root / "plugins" / "modern" / ".codex-plugin" / "renamed.json"
        source.rename(destination)
        head = self._commit("rename")
        _, payload = self._run(head=head)
        self._assert_selection(payload, "AFFECTED", ["legacy", "modern"])

        legacy_source = self.root / "plugins" / "legacy" / ".codex-plugin" / "plugin.json"
        modern_copy = self.root / "plugins" / "modern" / ".codex-plugin" / "legacy-copy.json"
        shutil.copyfile(legacy_source, modern_copy)
        legacy_source.write_bytes(legacy_source.read_bytes() + b" ")
        head = self._commit("copy")
        _, payload = self._run(head=head)
        self._assert_selection(payload, "AFFECTED", ["legacy", "modern"])

    def test_unmapped_or_unavailable_delta_falls_back_to_all(self) -> None:
        (self.root / "README.md").write_text("unmapped\n", encoding="utf-8")
        head = self._commit("unmapped")
        _, unmapped = self._run(head=head)
        self._assert_selection(
            unmapped,
            "ALL",
            ["legacy", "modern"],
            "changed_path_unmapped",
        )

        _, invalid = self._run(base="missing-base", head="HEAD")
        self._assert_selection(
            invalid,
            "ALL",
            ["legacy", "modern"],
            "revision_unavailable",
        )

    def test_git_launch_failure_falls_back_to_all_with_valid_registry(self) -> None:
        completed, payload = self._run(
            base=self.base,
            head="HEAD",
            environment_overrides={"PATH": ""},
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self._assert_selection(
            payload,
            "ALL",
            ["legacy", "modern"],
            "revision_unavailable",
        )

    def test_shallow_history_falls_back_to_all(self) -> None:
        changed = self.root / "plugins" / "legacy" / ".codex-plugin" / "plugin.json"
        changed.write_bytes(changed.read_bytes() + b"\n")
        head = self._commit("shallow-head")
        shallow_parent = Path(tempfile.mkdtemp(dir=self.fixture.root))
        shallow = shallow_parent / "shallow"
        self._git(
            "clone",
            "--depth",
            "1",
            self.root.resolve().as_uri(),
            str(shallow),
            cwd=self.fixture.root,
        )

        _, payload = self._run(base=self.base, head=head, root=shallow)

        self._assert_selection(
            payload,
            "ALL",
            ["legacy", "modern"],
            "revision_unavailable",
        )

    def test_every_shared_control_selects_all(self) -> None:
        shared = (
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
            ".obvious-one-validation.json",
            "tools/verify_marketplace.py",
            "tools/select_marketplace_plugins.py",
            ".github/workflows/validate.yml",
            ".gitattributes",
        )
        for relative in shared:
            with self.subTest(relative=relative):
                self._git("reset", "--hard", self.base)
                path = self.root / relative
                if relative.endswith(".json"):
                    data = json.loads(path.read_text(encoding="utf-8"))
                    path.write_text(
                        json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                else:
                    path.write_bytes(path.read_bytes() + b"\n")
                head = self._commit(f"shared {relative}")
                _, payload = self._run(head=head)
                self._assert_selection(
                    payload,
                    "ALL",
                    ["legacy", "modern"],
                    "shared_control_changed",
                )

    def test_invalid_registry_fails_instead_of_constructing_matrix(self) -> None:
        registry_path = self.root / ".obvious-one-validation.json"
        original = json.loads(registry_path.read_text(encoding="utf-8"))
        cases = {}
        non_v2 = json.loads(json.dumps(original))
        non_v2["schema_version"] = 1
        cases["non-v2"] = non_v2
        duplicate = json.loads(json.dumps(original))
        duplicate["plugins"].append(json.loads(json.dumps(duplicate["plugins"][0])))
        cases["duplicate"] = duplicate
        overlap = json.loads(json.dumps(original))
        overlap["plugins"][1]["targets"]["codex"]["path"] = "plugins/legacy/nested"
        cases["overlap"] = overlap
        unsafe = json.loads(json.dumps(original))
        unsafe["plugins"][0]["targets"]["codex"]["path"] = "../outside"
        cases["unsafe"] = unsafe

        for name, registry in cases.items():
            with self.subTest(name=name):
                registry_path.write_text(
                    json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                completed, payload = self._run(all_reason="workflow_dispatch")
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(payload["status"], "FAIL")
                self.assertEqual(payload["code"], "marketplace_selection_failed")
                registry_path.write_text(
                    json.dumps(original, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

    def test_result_is_deterministic_and_script_is_framework_independent(self) -> None:
        changed = self.root / "plugins" / "legacy" / ".codex-plugin" / "plugin.json"
        changed.write_bytes(changed.read_bytes() + b"\n")
        head = self._commit("deterministic")

        first_completed, first = self._run(head=head)
        second_completed, second = self._run(head=head)

        self.assertEqual(first_completed.returncode, 0, first_completed.stderr)
        self.assertEqual(first_completed.stdout, second_completed.stdout)
        self.assertEqual(first, second)
        self.assertNotIn("obvious_one_plugin_framework", self.selector.read_text(encoding="utf-8"))

    def test_matrix_is_exactly_the_validated_selected_plugin_list(self) -> None:
        changed = self.root / "plugins" / "modern" / ".codex-plugin" / "plugin.json"
        changed.write_bytes(changed.read_bytes() + b"\n")
        head = self._commit("matrix contract")

        completed, payload = self._run(head=head)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        evidence = payload["evidence"]
        self.assertEqual(set(evidence["matrix"]), {"plugin"})
        self.assertEqual(evidence["matrix"]["plugin"], evidence["selected_plugins"])

    def test_renderer_matches_installed_template_and_generated_stage(self) -> None:
        rendered = render_marketplace_selector()

        self.assertEqual(self.selector.read_text(encoding="utf-8"), rendered)
        self.assertEqual(rendered, render_marketplace_selector())
        self.assertNotIn("\r", rendered)


if __name__ == "__main__":
    unittest.main()
