"""The vendored wheel must carry ordinary importable Python subpackages."""

from pathlib import Path
import unittest
import zipfile


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WHEEL = PLUGIN_ROOT / "vendor" / "rag-subsystem" / "rag_subsystem-0.2.1-py3-none-any.whl"


class VendoredRagWheelTests(unittest.TestCase):
    def test_all_python_subpackages_have_package_markers(self):
        with zipfile.ZipFile(WHEEL) as archive:
            names = set(archive.namelist())
        package_dirs = {
            str(Path(name).parent).replace("\\", "/")
            for name in names
            if name.startswith("rag_subsystem/") and name.endswith(".py")
        }
        self.assertEqual(
            sorted(directory for directory in package_dirs if f"{directory}/__init__.py" not in names),
            [],
        )


if __name__ == "__main__":
    unittest.main()
