import os
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture" / "scripture-sources"

from scripture_sources import (  # noqa: E402
    BUNDLED_SOURCES,
    SourceValidationError,
    resolve_bundled_sources,
    resolve_source_paths,
)


OLD_NAME = "Bible 舊約聖經和合本.pdf"
NEW_NAME = "Bible 新約聖經和合本.pdf"
SYNTHETIC_SOURCES = (
    (OLD_NAME, "306E9995DEEF860E2567FDEE8F3932C1793FE6ADE6491D7B724A7C14BE2FB2D1"),
    (NEW_NAME, "FFBAAB6CCD4448BAB927F8FE9E7D080F46DF2D2D6E8F17DF3230C727B3D39E86"),
)


class ScriptureSourceTests(unittest.TestCase):
    def setUp(self):
        if RUNTIME.exists():
            shutil.rmtree(RUNTIME)
        RUNTIME.mkdir(parents=True)
        self.root = RUNTIME
        self.plugin = self.root / "cool-bible-tutor"
        self.assets = self.plugin / "assets" / "scripture"
        self.assets.mkdir(parents=True)
        self.fake_script = (
            self.plugin / "skills" / "retrieving-chinese-union-version-scripture"
            / "scripts" / "scripture_sources.py"
        )
        self.fake_script.parent.mkdir(parents=True)
        self.old = self.assets / OLD_NAME
        self.new = self.assets / NEW_NAME
        self.old.write_bytes(b"old-public-domain")
        self.new.write_bytes(b"new-public-domain")

    def tearDown(self):
        if RUNTIME.exists():
            shutil.rmtree(RUNTIME)

    def bundled(self):
        return patch("scripture_sources.BUNDLED_SOURCES", SYNTHETIC_SOURCES)

    def test_production_allowlist_names_and_hashes_are_fixed(self):
        self.assertEqual(
            BUNDLED_SOURCES,
            (
                (OLD_NAME, "2740A6F824F96374CB127D78C3D646B489963898DACC252B842D9A8894A91125"),
                (NEW_NAME, "4F0F9EF4C4A78B83F918C74E8F368A7E0EAE515C17866C7767C310CA75786490"),
            ),
        )

    def test_valid_bundled_pair_resolves_in_canonical_order(self):
        with self.bundled():
            old, new = resolve_bundled_sources(self.fake_script)
        self.assertEqual((old, new), (self.old.resolve(), self.new.resolve()))

    def test_missing_bundled_member_is_rejected(self):
        self.new.unlink()
        with self.bundled():
            with self.assertRaisesRegex(SourceValidationError, "missing"):
                resolve_bundled_sources(self.fake_script)

    def test_tampered_bundled_member_is_rejected(self):
        self.old.write_bytes(b"tampered")
        with self.bundled():
            with self.assertRaisesRegex(SourceValidationError, "SHA-256"):
                resolve_bundled_sources(self.fake_script)

    def test_explicit_paths_take_precedence_over_environment(self):
        explicit = self.root / "explicit.pdf"
        environment = self.root / "environment.pdf"
        self.assertEqual(
            resolve_source_paths((explicit,), {"COOL_BIBLE_TUTOR_SOURCE_PDFS": str(environment)}),
            (explicit.resolve(),),
        )

    def test_environment_paths_take_precedence_over_bundled_sources(self):
        first = self.root / "first.pdf"
        second = self.root / "second.pdf"
        configured = os.pathsep.join((str(first), str(second)))
        self.assertEqual(
            resolve_source_paths((), {"COOL_BIBLE_TUTOR_SOURCE_PDFS": configured}),
            (first.resolve(), second.resolve()),
        )

    def test_empty_explicit_and_environment_values_use_bundled_pair(self):
        with self.bundled():
            self.assertEqual(
                resolve_source_paths((), {}, self.fake_script),
                (self.old.resolve(), self.new.resolve()),
            )


if __name__ == "__main__":
    unittest.main()
