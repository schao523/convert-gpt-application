from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class PublicationTemplateTests(unittest.TestCase):
    def test_repository_ci_runs_full_suites_on_three_operating_systems(self) -> None:
        content = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        for runner in ("windows-latest", "ubuntu-latest", "macos-latest"):
            self.assertIn(runner, content)
        self.assertIn("unittest discover -s . -v", content)
        self.assertIn(
            "unittest discover -s applications/vibe-coding-designer/tests -v",
            content,
        )

    def test_expected_publication_templates_exist(self) -> None:
        expected = {
            "github-workflows/release-openclaw.yml.template",
            "github-workflows/retry-clawhub.yml.template",
            "github-workflows/validate.yml.template",
            "marketplace/codex-marketplace.json.template",
            "marketplace/openclaw-marketplace.json.template",
        }
        actual = {
            path.relative_to(TEMPLATES).as_posix()
            for path in TEMPLATES.rglob("*.template")
        }
        self.assertEqual(actual, expected)

    def test_generic_templates_expose_plugin_identity_placeholder(self) -> None:
        for path in TEMPLATES.rglob("*.template"):
            if path.name == "validate.yml.template":
                continue
            content = path.read_text(encoding="utf-8")
            self.assertIn("{{PLUGIN_ID}}", content)

    def test_validation_workflow_is_catalog_driven(self) -> None:
        content = (TEMPLATES / "github-workflows/validate.yml.template").read_text(
            encoding="utf-8"
        )
        self.assertIn(".obvious-one-validation.json", content)
        self.assertIn("matrix.plugin", content)
        self.assertNotIn("{{PLUGIN_ID}}", content)
        self.assertNotIn("clawhub", content.lower())


if __name__ == "__main__":
    unittest.main()
