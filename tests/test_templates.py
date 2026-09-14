from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class PublicationTemplateTests(unittest.TestCase):
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
            content = path.read_text(encoding="utf-8")
            self.assertIn("{{PLUGIN_ID}}", content)


if __name__ == "__main__":
    unittest.main()
