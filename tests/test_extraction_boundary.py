from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


def tracked_paths() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return [Path(item) for item in output.decode("utf-8").split("\0") if item]


class ExtractionBoundaryTests(unittest.TestCase):
    def test_no_private_source_extensions_outside_product_assets(self) -> None:
        offenders = []
        for relative in tracked_paths():
            if relative.suffix.lower() not in {".pdf", ".docx", ".ppt", ".pptx"}:
                continue
            parts = relative.parts
            allowed = len(parts) >= 4 and parts[0] == "applications" and "assets" in parts
            if not allowed:
                offenders.append(relative.as_posix())
        self.assertEqual(offenders, [])

    def test_no_absolute_developer_paths_in_tracked_text(self) -> None:
        offenders = []
        for relative in tracked_paths():
            path = ROOT / relative
            if path.suffix.lower() not in {".md", ".json", ".py", ".toml", ".yml", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8")
            if re.search(r"[A-Za-z]:\\Users\\[^\\]+\\OneDrive\\", text, re.IGNORECASE):
                offenders.append(relative.as_posix())
        self.assertEqual(offenders, [])

    def test_no_nested_source_git_or_worktree_metadata(self) -> None:
        nested = [path for path in ROOT.rglob(".git") if path != ROOT / ".git"]
        self.assertEqual(nested, [])

    def test_conversion_local_files_are_not_tracked(self) -> None:
        offenders = [
            path.as_posix()
            for path in tracked_paths()
            if path.name == "conversion.local.json"
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
