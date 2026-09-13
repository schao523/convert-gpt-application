"""Audit a plugin tree for local-only data and broken Markdown links."""

from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import re
from pathlib import Path
import sqlite3


FORBIDDEN_SUFFIXES = {
    ".sqlite", ".sqlite3", ".db",
    ".faiss", ".npy", ".npz", ".onnx", ".pt", ".pth", ".safetensors",
}
APPROVED_PDFS = {
    "assets/scripture/Bible 舊約聖經和合本.pdf":
        "2740A6F824F96374CB127D78C3D646B489963898DACC252B842D9A8894A91125",
    "assets/scripture/Bible 新約聖經和合本.pdf":
        "4F0F9EF4C4A78B83F918C74E8F368A7E0EAE515C17866C7767C310CA75786490",
}
PUBLIC_CORPUS_PATH = "assets/scripture/cuv.sqlite3"
PUBLIC_CORPUS_MANIFEST = "assets/scripture/cuv-runtime-manifest.json"
APPROVED_GAPS_MANIFEST = "assets/scripture/cuv-approved-gaps.json"
PUBLIC_RAG_INDEX = "assets/rag/cuv-rag-index.sqlite3"
PUBLIC_RAG_MANIFEST = "assets/rag/cuv-rag-runtime-manifest.json"
PUBLIC_MODEL_MANIFEST = "assets/rag/bge-large-zh-v1.5-model-manifest.json"
RUNTIME_LOCK = "vendor/rag-runtime/runtime-lock.json"
RUNTIME_REQUIREMENTS = "vendor/rag-runtime/requirements-rag.lock"
MODEL_DOWNLOAD_MANIFEST = "vendor/rag-runtime/model-manifest.json"
RAG_WHEEL = "vendor/rag-subsystem/rag_subsystem-0.2.1-py3-none-any.whl"
RAG_WHEEL_MANIFEST = "vendor/rag-subsystem/manifest.json"
FORBIDDEN_NAMES = {"ocr-output", "rendered-pages", "page-crops", "backups"}
FORBIDDEN_FILES = {"build-state.json", "cuv-review-history.sqlite3"}
PRIVATE_ARTIFACT = re.compile(
    r"(?:^|[-_.])(ocr(?:[-_.]?output)?|page[-_]?\d+|rendered[-_]?page)(?:[-_.]|$)",
    re.IGNORECASE,
)
PRIVATE_ARTIFACT_SUFFIXES = {".txt", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py"}
WINDOWS_USER_PATH = re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+")
UNIX_USER_PATH = re.compile(r"/(?:Users|home)/[^/\s]+/")
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+\.md)\)")


def _scaffold_marker() -> str:
    return "[" + "".join(("TO", "DO:"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def collect_local_markdown_links(path: Path) -> list[Path]:
    content = path.read_text(encoding="utf-8")
    return [(path.parent / raw).resolve() for raw in MARKDOWN_LINK.findall(content)]


def audit_markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    for markdown in root.rglob("*.md"):
        content = markdown.read_text(encoding="utf-8")
        for raw in MARKDOWN_LINK.findall(content):
            if raw.startswith(("http://", "https://")):
                continue
            if not (markdown.parent / raw).resolve().exists():
                relative = markdown.relative_to(root).as_posix()
                errors.append(f"broken Markdown link: {relative} -> {raw}")
    return sorted(errors)


def audit_public_corpus(root: Path) -> list[str]:
    database = root / PUBLIC_CORPUS_PATH
    runtime_manifest = root / PUBLIC_CORPUS_MANIFEST
    approved_gaps = root / APPROVED_GAPS_MANIFEST
    present = [path.is_file() for path in (database, runtime_manifest, approved_gaps)]
    if not any(present):
        return []
    if not all(present):
        return ["public corpus runtime assets are incomplete"]
    try:
        runtime = json.loads(runtime_manifest.read_text(encoding="utf-8"))
        gaps = json.loads(approved_gaps.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ["public corpus manifest is invalid"]

    errors: list[str] = []
    database_sha256 = sha256_file(database).lower()
    if runtime.get("database_sha256") != database_sha256:
        errors.append("public corpus digest mismatch")
    if gaps.get("database_sha256") != database_sha256:
        errors.append("approved-gap corpus digest mismatch")
    if runtime.get("approved_gap_sha256") != sha256_file(approved_gaps).lower():
        errors.append("approved-gap manifest digest mismatch")
    if runtime.get("row_count") != 31008:
        errors.append("public corpus manifest row count mismatch")
    try:
        uri = database.resolve().as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%'"
                )
            }
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
            row_count = connection.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
        if integrity != "ok":
            errors.append("public corpus integrity check failed")
        if tables != {"metadata", "verses"}:
            errors.append("public corpus table allowlist mismatch")
        if int(row_count) != 31008:
            errors.append("public corpus database row count mismatch")
        private_prefixes = ("rag_", "review_", "backup_", "local_")
        if any(key.lower().startswith(private_prefixes) for key in metadata):
            errors.append("public corpus contains private metadata")
    except (OSError, sqlite3.Error, TypeError, ValueError):
        errors.append("public corpus database is invalid")
    return sorted(set(errors))


def audit_public_rag_index(root: Path) -> list[str]:
    index = root / PUBLIC_RAG_INDEX
    runtime_manifest = root / PUBLIC_RAG_MANIFEST
    model_manifest = root / PUBLIC_MODEL_MANIFEST
    corpus_manifest = root / PUBLIC_CORPUS_MANIFEST
    present = [path.is_file() for path in (index, runtime_manifest, model_manifest)]
    if not any(present):
        return []
    if not all(present) or not corpus_manifest.is_file():
        return ["public RAG runtime assets are incomplete"]
    try:
        runtime = json.loads(runtime_manifest.read_text(encoding="utf-8"))
        model = json.loads(model_manifest.read_text(encoding="utf-8"))
        corpus = json.loads(corpus_manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ["public RAG runtime manifest is invalid"]

    errors: list[str] = []
    if sha256_file(index).lower() != runtime.get("index_sha256"):
        errors.append("RAG index digest mismatch")
    if index.stat().st_size >= 100 * 1024 * 1024:
        errors.append("RAG index exceeds GitHub ordinary-object size limit")
    bindings = (
        (runtime.get("corpus_manifest_sha256"), sha256_file(corpus_manifest).lower()),
        (runtime.get("model_manifest_sha256"), sha256_file(model_manifest).lower()),
        (runtime.get("corpus_database_sha256"), corpus.get("database_sha256")),
        (runtime.get("corpus_structure_sha256"), corpus.get("corpus_structure_sha256")),
        (runtime.get("model_revision"), model.get("revision")),
        (runtime.get("model_files"), model.get("files")),
        (runtime.get("model_route"), model.get("route")),
        (runtime.get("dimensions"), model.get("dimensions")),
    )
    if any(expected != actual for expected, actual in bindings):
        errors.append("RAG runtime asset binding mismatch")
    if runtime.get("item_count") != 9942 or runtime.get("dimensions") != 1024:
        errors.append("RAG runtime manifest shape mismatch")

    try:
        uri = index.resolve().as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(chunks)")
            }
            metadata = dict(connection.execute("SELECT key, value FROM index_metadata"))
            count, app_count, app_id, blob_size = connection.execute(
                "SELECT COUNT(*), COUNT(DISTINCT app_id), MIN(app_id), "
                "MIN(length(embedding)) FROM chunks"
            ).fetchone()
            source_order = connection.execute(
                "SELECT MIN(source_order), MAX(source_order), COUNT(DISTINCT source_order) "
                "FROM chunks"
            ).fetchone()
            public_text = "\n".join(
                value
                for row in connection.execute("SELECT text, metadata_json FROM chunks")
                for value in row
                if value
            )
        expected_columns = {
            "chunk_id", "source_order", "doc_id", "text", "section_path",
            "chunk_order", "language", "embedding_model", "namespace", "app_id",
            "embedding", "metadata_json", "content_hash",
        }
        if integrity != "ok":
            errors.append("RAG index integrity check failed")
        if tables != {"index_metadata", "chunks"} or columns != expected_columns:
            errors.append("RAG index schema allowlist mismatch")
        if (count, app_count, app_id, blob_size) != (9942, 1, "cool-bible-tutor", 4096):
            errors.append("RAG index item, app, or dimension mismatch")
        if source_order != (0, 9941, 9942):
            errors.append("RAG index source-order mismatch")
        if metadata.get("vector_identity_sha256") != runtime.get("vector_identity_sha256"):
            errors.append("RAG index embedded metadata mismatch")
        private_fragments = (
            "C:/Users/", "C:\\Users\\", "/Users/", "/home/", "OneDrive",
            "Dropbox (Personal)", "source_path", "review_history", "authoring-data",
        )
        if any(fragment in public_text for fragment in private_fragments):
            errors.append("RAG index contains private path or authoring metadata")
    except (OSError, sqlite3.Error, TypeError, ValueError):
        errors.append("RAG index database is invalid")
    return sorted(set(errors))


def audit_managed_runtime(root: Path) -> list[str]:
    paths = {
        name: root / relative for name, relative in {
            "lock": RUNTIME_LOCK,
            "requirements": RUNTIME_REQUIREMENTS,
            "download": MODEL_DOWNLOAD_MANIFEST,
            "wheel": RAG_WHEEL,
            "wheel_manifest": RAG_WHEEL_MANIFEST,
            "identity": PUBLIC_MODEL_MANIFEST,
        }.items()
    }
    managed_present = [
        paths[name].is_file()
        for name in ("lock", "requirements", "download", "wheel", "wheel_manifest")
    ]
    if not any(managed_present):
        return []
    if not all(path.is_file() for path in paths.values()):
        return ["managed RAG runtime assets are incomplete"]
    try:
        lock = json.loads(paths["lock"].read_text(encoding="utf-8"))
        download = json.loads(paths["download"].read_text(encoding="utf-8"))
        wheel_manifest = json.loads(paths["wheel_manifest"].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ["managed RAG runtime manifest is invalid"]
    errors: list[str] = []
    bindings = (
        (lock.get("requirements_sha256"), sha256_file(paths["requirements"]).lower()),
        (lock.get("model_download_manifest_sha256"), sha256_file(paths["download"]).lower()),
        (lock.get("model_manifest_sha256"), sha256_file(paths["identity"]).lower()),
        (lock.get("wheel_sha256"), sha256_file(paths["wheel"]).lower()),
        (wheel_manifest.get("wheel_sha256"), sha256_file(paths["wheel"]).lower()),
        (lock.get("model_total_bytes"), download.get("total_bytes")),
        (lock.get("wheel_version"), wheel_manifest.get("version")),
        (download.get("identity_manifest_sha256"), lock.get("model_manifest_sha256")),
    )
    if any(expected != actual for expected, actual in bindings):
        errors.append("managed RAG runtime digest or identity binding mismatch")
    if wheel_manifest.get("license") != "MIT" or download.get("license") != "MIT":
        errors.append("managed RAG runtime license declaration mismatch")
    try:
        files = download["files"]
        if sum(int(item["size"]) for item in files) != int(download["total_bytes"]):
            errors.append("model download byte total mismatch")
        for item in files:
            relative = Path(str(item["path"]))
            url = str(item["url"])
            if relative.is_absolute() or ".." in relative.parts:
                errors.append("unsafe model download path")
            expected_prefix = (
                "https://huggingface.co/BAAI/bge-large-zh-v1.5/resolve/"
                + str(download["revision"]) + "/"
            )
            if not url.startswith(expected_prefix) or len(str(item["sha256"])) != 64:
                errors.append("unpinned model download URL or digest")
    except (KeyError, TypeError, ValueError):
        errors.append("model download file manifest is invalid")
    return sorted(set(errors))


def audit_tree(root: Path) -> list[str]:
    errors: list[str] = []
    for candidate in root.rglob("*"):
        relative = candidate.relative_to(root).as_posix()
        if candidate.suffix.lower() == ".pyc" or "__pycache__" in candidate.parts:
            errors.append(f"Python cache artifact: {relative}")
        if candidate.is_file() and candidate.suffix.lower() == ".pdf":
            expected = APPROVED_PDFS.get(relative)
            if expected is None:
                errors.append(f"unapproved PDF: {relative}")
            elif sha256_file(candidate) != expected.upper():
                errors.append(f"approved PDF digest mismatch: {relative}")
        if (
            candidate.is_file()
            and candidate.suffix.lower() in FORBIDDEN_SUFFIXES
            and relative not in {PUBLIC_CORPUS_PATH, PUBLIC_RAG_INDEX}
        ):
            errors.append(f"forbidden file: {relative}")
        if candidate.is_file() and candidate.name.lower() in FORBIDDEN_FILES:
            errors.append(f"private build artifact: {relative}")
        if (
            candidate.is_file()
            and candidate.suffix.lower() in PRIVATE_ARTIFACT_SUFFIXES
            and PRIVATE_ARTIFACT.search(candidate.stem)
            and "fixtures" not in {part.lower() for part in candidate.parts}
        ):
            errors.append(f"private OCR artifact: {relative}")
        if any(part.lower() in FORBIDDEN_NAMES for part in candidate.parts):
            errors.append(f"forbidden path: {relative}")
        if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES:
            content = candidate.read_text(encoding="utf-8")
            if WINDOWS_USER_PATH.search(content):
                errors.append(f"absolute Windows path: {relative}")
            if UNIX_USER_PATH.search(content):
                errors.append(f"absolute Unix path: {relative}")
            if _scaffold_marker() in content:
                errors.append(f"scaffold marker: {relative}")
    for relative in APPROVED_PDFS:
        if not (root / relative).is_file():
            errors.append(f"missing approved PDF: {relative}")
    errors.extend(audit_public_corpus(root))
    errors.extend(audit_public_rag_index(root))
    errors.extend(audit_managed_runtime(root))
    errors.extend(audit_markdown_links(root))
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    errors = audit_tree(args.root.resolve())
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
