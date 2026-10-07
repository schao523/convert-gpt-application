from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "workbench-handoff"
DESIGN_ASSISTANT = (
    ROOT / "applications" / "cool-plugin-design-assistant" / "scripts"
    / "cool_plugin_design_assistant.py"
)
PLUGIN_BUILDER_SCRIPTS = ROOT / "applications" / "plugin-builder" / "scripts"
if str(PLUGIN_BUILDER_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PLUGIN_BUILDER_SCRIPTS))

from plugin_builder_core.inspection import inspect_design_package


def _load_design_assistant():
    spec = importlib.util.spec_from_file_location("interop_design_assistant", DESIGN_ASSISTANT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


DESIGN_TOOL = _load_design_assistant()


def _canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def _write_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in sorted(members.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload)


def _directory_members(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class WorkbenchHandoffInteroperabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_root = ROOT / ".tmp" / "workbench-handoff-interoperability"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=temporary_root)
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _full_source(self) -> Path:
        path = self.root / "full-source.zip"
        _write_zip(path, _directory_members(FIXTURES / "full"))
        return path

    def _baseline(self) -> tuple[Path, dict[str, bytes]]:
        members = _directory_members(FIXTURES / "delta" / "baseline")
        path = self.root / "baseline.zip"
        _write_zip(path, members)
        return path, members

    def _delta_source(self, baseline: Path) -> Path:
        fixture = FIXTURES / "delta"
        members = {
            name: payload for name, payload in _directory_members(fixture).items()
            if not name.startswith("baseline/")
        }
        manifest = json.loads(members["delta_handoff_manifest.json"].decode("utf-8"))
        manifest["baseline"]["archive_sha256"] = sha256(baseline.read_bytes()).hexdigest()
        members["delta_handoff_manifest.json"] = _canonical_json(manifest)
        path = self.root / "delta-source.zip"
        _write_zip(path, members)
        return path

    def _produce(self, source: Path, name: str) -> Path:
        output = self.root / name
        report = DESIGN_TOOL.normalize_handoff_package(
            source, output, confirmed_by="fixture decision owner"
        )
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["output_profile"], "WORKBENCH_HANDOFF_V1_1")
        self.assertEqual(
            report["output_archive_sha256"],
            sha256(output.read_bytes()).hexdigest(),
        )
        return output

    def test_design_assistant_full_output_enters_plugin_builder_s2_without_repair(self) -> None:
        produced = self._produce(self._full_source(), "full-normalized.zip")
        outcome = inspect_design_package(produced, self.root / "full-workspace", "create")

        self.assertEqual((outcome.status, outcome.stage), ("PASS", "S2"), outcome.errors)
        session = json.loads((self.root / "full-workspace" / "session.json").read_bytes())
        self.assertEqual(session["inspection"]["normalization"]["profile"], "WORKBENCH_HANDOFF_V1_1")
        self.assertEqual([row["id"] for row in session["requirements"]], ["D-01", "DAC-01", "IM-09"])

    def test_design_assistant_delta_output_enters_plugin_builder_s2_with_matching_baseline(self) -> None:
        baseline, baseline_members = self._baseline()
        produced = self._produce(self._delta_source(baseline), "delta-normalized.zip")
        workspace = self.root / "delta-workspace"
        outcome = inspect_design_package(produced, workspace, "update", baseline)

        self.assertEqual((outcome.status, outcome.stage), ("PASS", "S2"), outcome.errors)
        inspection = json.loads((workspace / "inspection.json").read_bytes())
        self.assertEqual(inspection["baseline"]["plugin_id"], "interop-plugin")
        self.assertEqual(inspection["baseline"]["version"], "1.0.0")
        self.assertEqual(
            (workspace / "baseline" / "skills" / "existing" / "SKILL.md").read_bytes(),
            baseline_members["skills/existing/SKILL.md"],
        )

    def test_cross_product_output_preserves_ids_sources_text_and_source_bytes(self) -> None:
        source = self._full_source()
        produced = self._produce(source, "preservation-normalized.zip")
        workspace = self.root / "preservation-workspace"
        outcome = inspect_design_package(produced, workspace, "create")

        self.assertEqual(outcome.status, "PASS", outcome.errors)
        with zipfile.ZipFile(produced) as archive:
            handoff = json.loads(archive.read("workbench-handoff.json"))
            self.assertEqual(
                archive.read("Design_APPROVED.md"),
                (FIXTURES / "full" / "Design_APPROVED.md").read_bytes(),
            )
        inspection = json.loads((workspace / "inspection.json").read_bytes())
        expected = [
            (row["id"], row["source"], row["verbatim"])
            for row in handoff["requirements"]
        ]
        observed = [
            (row["id"], row["source"], row["verbatim"])
            for row in inspection["requirements"]
        ]
        self.assertEqual(observed, expected)
        self.assertIn("酷插件設計助理", observed[1][2])

    def test_cross_product_repeated_normalization_is_byte_deterministic(self) -> None:
        source = self._full_source()
        first = self._produce(source, "repeat-one.zip")
        second = self._produce(source, "repeat-two.zip")

        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(sha256(first.read_bytes()).hexdigest(), sha256(second.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
