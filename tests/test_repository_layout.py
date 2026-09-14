from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryLayoutTests(unittest.TestCase):
    def test_src_layout_build_metadata_is_ignored(self) -> None:
        result = subprocess.run(
            [
                "git",
                "check-ignore",
                "src/obvious_one_plugin_framework.egg-info/PKG-INFO",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_required_roots_exist(self) -> None:
        for relative in (
            "src/obvious_one_plugin_framework",
            "applications",
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
