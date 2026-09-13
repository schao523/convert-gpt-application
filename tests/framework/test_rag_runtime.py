from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import threading
import unittest

from obvious_one_plugin_framework.rag_runtime import (
    ensure_cached_object,
    resolve_runtime_paths,
)


RUNTIME_SHA = "a" * 64
MODEL_SHA = "b" * 64


class RagRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_only_runtime_and_model_paths_are_shared(self) -> None:
        alpha = resolve_runtime_paths("plugin-alpha", RUNTIME_SHA, MODEL_SHA, self.root)
        beta = resolve_runtime_paths("plugin-beta", RUNTIME_SHA, MODEL_SHA, self.root)
        self.assertEqual(alpha.runtime_dir, beta.runtime_dir)
        self.assertEqual(alpha.model_dir, beta.model_dir)
        self.assertNotEqual(alpha.indexes_dir, beta.indexes_dir)
        self.assertNotEqual(alpha.source_assets_dir, beta.source_assets_dir)
        self.assertNotEqual(alpha.authoring_dir, beta.authoring_dir)
        self.assertEqual(alpha.runtime_dir.name, RUNTIME_SHA)
        self.assertEqual(alpha.model_dir.name, MODEL_SHA)

    def test_concurrent_cache_population_occurs_once(self) -> None:
        target = self.root / "shared-rag" / "models" / MODEL_SHA
        calls = 0
        guard = threading.Lock()

        def populate(stage: Path) -> None:
            nonlocal calls
            with guard:
                calls += 1
            (stage / "model.bin").write_bytes(b"verified")

        def verify(path: Path) -> None:
            self.assertEqual((path / "model.bin").read_bytes(), b"verified")

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(
                lambda _: ensure_cached_object(target, MODEL_SHA, populate, verify),
                range(2),
            ))
        self.assertEqual(results, [target, target])
        self.assertEqual(calls, 1)
        self.assertTrue((target / ".obvious-one-complete.json").is_file())

    def test_failed_replacement_preserves_existing_target(self) -> None:
        target = self.root / "shared-rag" / "models" / MODEL_SHA
        target.mkdir(parents=True)
        (target / "model.bin").write_bytes(b"previous")

        def populate(stage: Path) -> None:
            (stage / "model.bin").write_bytes(b"broken")

        def verify(path: Path) -> None:
            if (path / "model.bin").read_bytes() != b"previous":
                raise ValueError("invalid model")

        with self.assertRaisesRegex(ValueError, "invalid model"):
            ensure_cached_object(target, MODEL_SHA, populate, verify)
        self.assertEqual((target / "model.bin").read_bytes(), b"previous")


if __name__ == "__main__":
    unittest.main()
