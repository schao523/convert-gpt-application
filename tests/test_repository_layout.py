from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryLayoutTests(unittest.TestCase):
    def test_required_roots_exist(self) -> None:
        for relative in (
            "src/obvious_one_plugin_framework",
            "applications/cool-bible-tutor",
            "templates/plugin",
            "templates/skill",
            "templates/github-workflows",
            "templates/marketplace",
            "docs",
            "tests/framework",
        ):
            self.assertTrue((ROOT / relative).is_dir(), relative)

    def test_raw_gpt_sources_are_not_at_repository_root(self) -> None:
        forbidden = {".pdf", ".docx", ".ppt", ".pptx"}
        offenders = [
            path.name for path in ROOT.iterdir()
            if path.suffix.lower() in forbidden
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
