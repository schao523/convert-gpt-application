from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


APPLICATION = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "onboarded_marketplace_builder", APPLICATION / "scripts" / "build_marketplace_release.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("marketplace_builder_unavailable")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class MarketplaceReleaseTests(unittest.TestCase):
    def test_build_copies_imported_tree(self) -> None:
        source = APPLICATION
        with tempfile.TemporaryDirectory() as name:
            target = BUILDER.build(source, Path(name))
            self.assertEqual(target.name, 'steam-parent-child-learning')
            expected = sorted(p.relative_to(source / "imported-plugin") for p in (source / "imported-plugin").rglob("*") if p.is_file())
            actual = sorted(p.relative_to(target) for p in target.rglob("*") if p.is_file())
            self.assertEqual(actual, sorted(set(expected) | {Path("LICENSE")}))
            for relative in expected:
                self.assertEqual((target / relative).read_bytes(), (source / "imported-plugin" / relative).read_bytes())
            self.assertEqual((target / "LICENSE").read_bytes(), (source / "LICENSE").read_bytes())


if __name__ == "__main__":
    unittest.main()
