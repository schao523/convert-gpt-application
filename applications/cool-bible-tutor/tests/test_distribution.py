import importlib.util
import json
import shutil
import unittest
import uuid
from pathlib import Path

from obvious_one_plugin_framework.contract import load_contract


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "distribution_audit.py"
PLUGIN = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(__file__).parent / "_runtime_fixture"
OLD_PATH = "assets/scripture/Bible 舊約聖經和合本.pdf"
NEW_PATH = "assets/scripture/Bible 新約聖經和合本.pdf"
SYNTHETIC_APPROVED_PDFS = {
    OLD_PATH: "39387A268D5EA7EBBE877655BB7AD266AEAA8589989EA53CA9CEEC26B1590B86",
    NEW_PATH: "F4C7EC0BB06759C449E54C4EB34761AAB304726EF40AC1C7D0D1FA8E3DFE4CE5",
}


def load_audit_module():
    if not MODULE_PATH.exists():
        raise ModuleNotFoundError("distribution_audit.py does not exist")
    spec = importlib.util.spec_from_file_location("distribution_audit", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DistributionAuditTests(unittest.TestCase):
    def test_approved_openclaw_distribution_identity(self) -> None:
        contract = load_contract(PLUGIN / "openclaw" / "distribution.json")
        self.assertEqual(contract.version, "2.4.6")
        self.assertEqual(contract.package_name, "@obvious-one/cool-bible-tutor")
        self.assertEqual(contract.rag.app_id, "cool-bible-tutor")
        self.assertEqual(
            contract.rag.namespace,
            "cool-bible-tutor:zh:bge-large-zh",
        )
        self.assertEqual(
            {group.name for group in contract.rag.asset_groups},
            {"rag-index", "source-pdfs"},
        )

    def setUp(self):
        self.root = FIXTURE_ROOT / f"case-{uuid.uuid4().hex}"
        self.root.mkdir(parents=True)

    def tearDown(self):
        for candidate in self.root.rglob("*"):
            if candidate.is_file():
                candidate.unlink()

    def audit(self, approved=None):
        module = load_audit_module()
        module.APPROVED_PDFS = {} if approved is None else approved
        return module.audit_tree(self.root)

    def write_approved_pair(self):
        old = self.root / OLD_PATH
        new = self.root / NEW_PATH
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_bytes(b"old-approved")
        new.write_bytes(b"new-approved")

    def copy_public_runtime_assets(self):
        plugin = Path(__file__).parents[1]
        target = self.root / "assets" / "scripture"
        target.mkdir(parents=True, exist_ok=True)
        for name in (
            "cuv.sqlite3",
            "cuv-runtime-manifest.json",
            "cuv-approved-gaps.json",
        ):
            shutil.copy2(plugin / "assets" / "scripture" / name, target / name)

    def copy_public_rag_assets(self):
        plugin = Path(__file__).parents[1]
        rag_target = self.root / "assets" / "rag"
        scripture_target = self.root / "assets" / "scripture"
        rag_target.mkdir(parents=True, exist_ok=True)
        scripture_target.mkdir(parents=True, exist_ok=True)
        for name in (
            "cuv-rag-index.sqlite3",
            "cuv-rag-runtime-manifest.json",
            "bge-large-zh-v1.5-model-manifest.json",
        ):
            shutil.copy2(plugin / "assets" / "rag" / name, rag_target / name)
        for name in (
            "cuv.sqlite3",
            "cuv-runtime-manifest.json",
            "cuv-approved-gaps.json",
        ):
            shutil.copy2(
                plugin / "assets" / "scripture" / name,
                scripture_target / name,
            )

    def test_production_pdf_allowlist_is_fixed(self):
        self.assertEqual(
            load_audit_module().APPROVED_PDFS,
            {
                OLD_PATH: "2740A6F824F96374CB127D78C3D646B489963898DACC252B842D9A8894A91125",
                NEW_PATH: "4F0F9EF4C4A78B83F918C74E8F368A7E0EAE515C17866C7767C310CA75786490",
            },
        )

    def test_accepts_only_complete_hash_matching_pdf_allowlist(self):
        self.write_approved_pair()
        self.assertEqual([], self.audit(SYNTHETIC_APPROVED_PDFS))

    def test_rejects_missing_approved_pdf(self):
        self.write_approved_pair()
        (self.root / NEW_PATH).unlink()
        errors = self.audit(SYNTHETIC_APPROVED_PDFS)
        self.assertTrue(any("missing approved PDF" in error for error in errors))

    def test_rejects_tampered_approved_pdf(self):
        self.write_approved_pair()
        (self.root / OLD_PATH).write_bytes(b"changed")
        errors = self.audit(SYNTHETIC_APPROVED_PDFS)
        self.assertTrue(any("digest mismatch" in error for error in errors))

    def test_rejects_misplaced_or_extra_pdf(self):
        self.write_approved_pair()
        misplaced = self.root / "Bible 舊約聖經和合本.pdf"
        misplaced.write_bytes(b"old-approved")
        errors = self.audit(SYNTHETIC_APPROVED_PDFS)
        self.assertTrue(any("unapproved PDF" in error and misplaced.name in error for error in errors))

    def test_rejects_forbidden_scripture_and_database_files(self):
        (self.root / "Bible 新約聖經和合本.pdf").write_bytes(b"pdf")
        (self.root / "cuv.sqlite3").write_bytes(b"db")

        errors = self.audit()

        self.assertTrue(any("Bible 新約聖經和合本.pdf" in error for error in errors))
        self.assertTrue(any("cuv.sqlite3" in error for error in errors))

    def test_accepts_only_manifest_bound_public_corpus(self):
        self.copy_public_runtime_assets()

        self.assertEqual(self.audit(), [])

    def test_rejects_tampered_or_extra_database(self):
        self.copy_public_runtime_assets()
        database = self.root / "assets" / "scripture" / "cuv.sqlite3"
        database.write_bytes(b"tampered")
        extra = self.root / "assets" / "scripture" / "extra.sqlite3"
        extra.write_bytes(b"private")

        errors = self.audit()

        self.assertTrue(any("public corpus digest mismatch" in error for error in errors))
        self.assertTrue(any("forbidden file" in error and "extra.sqlite3" in error for error in errors))

    def test_accepts_only_manifest_bound_public_rag_index(self):
        self.copy_public_rag_assets()

        self.assertEqual(self.audit(), [])

    def test_rejects_tampered_or_extra_vector_database(self):
        self.copy_public_rag_assets()
        index = self.root / "assets" / "rag" / "cuv-rag-index.sqlite3"
        index.write_bytes(b"tampered")
        extra = self.root / "assets" / "rag" / "extra.sqlite3"
        extra.write_bytes(b"private")

        errors = self.audit()

        self.assertTrue(any("RAG index digest mismatch" in error for error in errors))
        self.assertTrue(any("forbidden file" in error and "extra.sqlite3" in error for error in errors))

    def test_rejects_private_build_state_and_ocr_artifacts(self):
        (self.root / "build-state.json").write_text("{}", encoding="utf-8")
        (self.root / "ocr-output.txt").write_text("private OCR", encoding="utf-8")
        (self.root / "page-001.png").write_bytes(b"image")

        errors = self.audit()

        for name in ("build-state.json", "ocr-output.txt", "page-001.png"):
            self.assertTrue(any(name in error for error in errors), name)

    def test_rejects_private_review_history_and_backup_directories(self):
        (self.root / "cuv-review-history.sqlite3").write_bytes(b"private")
        (self.root / "backups").write_bytes(b"private backup directory marker")

        errors = self.audit()

        self.assertTrue(any("cuv-review-history.sqlite3" in error for error in errors))
        self.assertTrue(any("backups" in error for error in errors))

    def test_allows_explicitly_synthetic_text_fixture(self):
        fixture = self.root / "fixtures" / "scripture"
        fixture.mkdir(parents=True, exist_ok=True)
        (fixture / "synthetic-page.txt").write_text("合成測試文字", encoding="utf-8")

        self.assertEqual([], self.audit())

    def test_rejects_machine_specific_windows_paths(self):
        (self.root / "config.md").write_text(
            "Corpus: C:\\Users\\Example\\corpus", encoding="utf-8"
        )

        errors = self.audit()

        self.assertTrue(any("absolute Windows path" in error for error in errors))

    def test_rejects_scaffold_markers(self):
        marker = "[" + "".join(("TO", "DO:")) + " replace me]"
        (self.root / "SKILL.md").write_text(marker, encoding="utf-8")

        errors = self.audit()

        self.assertTrue(any("scaffold marker" in error for error in errors))

    def test_rejects_python_cache_artifacts(self):
        cache = self.root / "cache-fixture"
        cache.mkdir()
        bytecode = cache / "module.cpython-312.pyc"
        bytecode.write_bytes(b"bytecode")
        self.addCleanup(bytecode.unlink, missing_ok=True)

        errors = self.audit()

        self.assertTrue(any("Python cache artifact" in error for error in errors))

    def test_rejects_vector_indexes_and_model_weights(self):
        vector = self.root / "bible-vectors.faiss"
        weights = self.root / "embedding-model.safetensors"
        vector.write_bytes(b"vector")
        weights.write_bytes(b"weights")

        errors = self.audit()

        self.assertTrue(any("bible-vectors.faiss" in error for error in errors))
        self.assertTrue(any("embedding-model.safetensors" in error for error in errors))

    def test_release_contract_bundles_sources_and_keeps_generated_data_external(self):
        plugin = Path(__file__).parents[1]
        distribution = (plugin / "DISTRIBUTION.md").read_text(encoding="utf-8")
        third_party = (plugin / "THIRD_PARTY_CONTENT.md").read_text(encoding="utf-8")
        setup = (
            plugin / "skills" / "retrieving-chinese-union-version-scripture"
            / "references" / "setup-scripture-data.md"
        ).read_text(encoding="utf-8")
        manifest = json.loads((plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

        self.assertIn("COOL_BIBLE_TUTOR_RAG_ROOT", distribution)
        self.assertIn("COOL_BIBLE_TUTOR_RAG_PYTHON", distribution)
        self.assertIn("cuv-rag-index.sqlite3", distribution)
        self.assertIn("不得包含 embedding model weights", distribution)
        self.assertIn("assets/scripture/cuv.sqlite3", distribution)
        self.assertIn("31,008", distribution)
        self.assertIn(OLD_PATH, distribution)
        self.assertIn(NEW_PATH, distribution)
        self.assertIn("public domain", third_party.lower())
        self.assertIn("plugin owner", third_party.lower())
        self.assertIn("build_cuv_index.py --data-dir", setup)
        self.assertIn("RAGenius", third_party)
        self.assertIn("MIT", third_party)
        self.assertEqual(manifest["version"], "2.4.6")

        combined = "\n".join((distribution, third_party, setup))
        self.assertIn("ObviousOne/shared-rag/runtimes", combined)
        self.assertIn("ObviousOne/shared-rag/models", combined)
        self.assertIn("ObviousOne/plugins/cool-bible-tutor/indexes", combined)
        self.assertIn("setup-rag --accept-downloads", combined)
        self.assertIn("no shared bible content pack", combined.lower())
        self.assertIn("public-domain", combined.lower())

    def test_clean_tree_has_no_errors(self):
        (self.root / "SKILL.md").write_text("# Valid skill", encoding="utf-8")

        self.assertEqual([], self.audit())

    def test_release_documents_the_top_level_setup_launcher(self):
        plugin = Path(__file__).parents[1]
        launcher = plugin / "scripts" / "cool_bible_tutor.py"
        readme = (plugin / "README.md").read_text(encoding="utf-8")
        scripture_skill = (
            plugin / "skills" / "retrieving-chinese-union-version-scripture" / "SKILL.md"
        ).read_text(encoding="utf-8")
        setup = (
            plugin / "skills" / "retrieving-chinese-union-version-scripture"
            / "references" / "setup-scripture-data.md"
        ).read_text(encoding="utf-8")

        self.assertTrue(launcher.is_file())
        for command in ("doctor", "init", "status", "verify", "review", "passage"):
            self.assertIn(f"cool_bible_tutor.py {command}", readme)
        for command in ("rag-check", "rag-ingest", "rag-discover"):
            self.assertIn(f"cool_bible_tutor.py {command}", readme)
        self.assertIn("cool_bible_tutor.py", scripture_skill)
        self.assertIn("cool_bible_tutor.py", setup)


if __name__ == "__main__":
    unittest.main()
