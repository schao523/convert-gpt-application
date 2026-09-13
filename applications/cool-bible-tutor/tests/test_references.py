import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "distribution_audit.py"
FIXTURE_ROOT = Path(__file__).parent / "_runtime_fixture"


def load_audit_module():
    if not MODULE_PATH.exists():
        raise ModuleNotFoundError("distribution_audit.py does not exist")
    spec = importlib.util.spec_from_file_location("distribution_audit", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MarkdownReferenceTests(unittest.TestCase):
    def setUp(self):
        self.root = FIXTURE_ROOT
        self.root.mkdir(parents=True, exist_ok=True)
        for candidate in self.root.rglob("*"):
            if candidate.is_file() and candidate.name != ".gitkeep":
                candidate.unlink()

    def tearDown(self):
        self.setUp()

    def test_collects_relative_markdown_links(self):
        reference = self.root / "references" / "guide.md"
        reference.parent.mkdir(parents=True, exist_ok=True)
        reference.write_text("guide", encoding="utf-8")
        skill = self.root / "SKILL.md"
        skill.write_text("Read [the guide](references/guide.md).", encoding="utf-8")

        targets = load_audit_module().collect_local_markdown_links(skill)

        self.assertEqual([reference.resolve()], targets)

    def test_reports_unresolved_markdown_links(self):
        skill = self.root / "SKILL.md"
        skill.write_text("Read [missing](references/missing.md).", encoding="utf-8")

        errors = load_audit_module().audit_markdown_links(self.root)

        self.assertEqual(
            ["broken Markdown link: SKILL.md -> references/missing.md"], errors
        )


if __name__ == "__main__":
    unittest.main()
