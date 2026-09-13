import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import sys

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
VENDORED_RUNTIME = PLUGIN_ROOT / "vendor" / "obvious-one-runtime"
if VENDORED_RUNTIME.is_dir() and str(VENDORED_RUNTIME) not in sys.path:
    sys.path.insert(0, str(VENDORED_RUNTIME))
try:
    from obvious_one_runtime.adapters import IngestionRequest, validate_ingestion_request
except ModuleNotFoundError:
    REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
    if str(REPOSITORY_ROOT) not in sys.path:
        sys.path.insert(0, str(REPOSITORY_ROOT))
    from obvious_one_plugin_framework.adapters import (
        IngestionRequest,
        validate_ingestion_request,
    )

from book_names import resolve_book
from corpus_db import DATABASE_NAME, resolve_data_dir
from rag_documents import (
    APP_ID, build_rag_documents, corpus_fingerprint, corpus_structure_sha256, read_corpus,
)
from rag_runtime import (
    AdapterConfigError,
    AdapterRuntimeError,
    load_rag_api,
    reexec_if_configured,
)
from rag_vector_lock import VectorFileLock
from rag_vector_manifest import read_json_vector_manifest


RAG_NAMESPACE = "cool-bible-tutor:zh:bge-large-zh"
CHUNKER_CONFIG_SHA256 = "bd23f12f7f02cf6e4626834896fb7492ccbc9b4fd30eecea8c663416ef194fa7"


class MissingCorpusError(AdapterConfigError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise AdapterConfigError(message)


def _positive_chapter(value: str) -> int:
    chapter = int(value)
    if chapter < 1:
        raise argparse.ArgumentTypeError("chapter must be positive")
    return chapter


def _parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Ingest a private CUV corpus into RAGenius")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--book")
    parser.add_argument("--chapter", type=_positive_chapter)
    return parser


def _emit_error(code: str, message: str) -> None:
    print(json.dumps({
        "status": "error",
        "error": {"code": code, "message": message},
    }, ensure_ascii=False))


def _finalize_full_ingestion(
    database: Path, initial_fingerprint: str, manifest: dict | None,
) -> None:
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        current_hashes, current_records = read_corpus(connection)
        if corpus_fingerprint(current_records, current_hashes) != initial_fingerprint:
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            connection.executemany(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                (("rag_index_state", "stale"), ("rag_index_stale_at", now)),
            )
            connection.commit()
            raise AdapterRuntimeError(
                "The corpus changed during RAG ingestion; run full ingestion again"
            )
        if manifest is not None and manifest["targeted_items"] < 1:
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            connection.executemany(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                (("rag_index_state", "stale"), ("rag_index_stale_at", now)),
            )
            connection.commit()
            raise AdapterRuntimeError(
                "JSON RAG ingestion produced no CUV chunks; stale state was retained"
            )
        connection.execute(
            "DELETE FROM metadata WHERE key IN "
            "('rag_index_state', 'rag_index_stale_at', 'rag_vector_item_count', "
            "'rag_corpus_structure_sha256', 'rag_vector_identity_sha256')"
        )
        if manifest is not None:
            connection.executemany(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                (
                    ("rag_vector_item_count", str(manifest["targeted_items"])),
                    ("rag_corpus_structure_sha256", corpus_structure_sha256(current_records)),
                    ("rag_vector_identity_sha256", manifest["identity_sha256"]),
                ),
            )
        connection.commit()


def ingest_database(database: Path, rag_api, book_id: int | None = None, chapter: int | None = None) -> dict:
    if chapter is not None and book_id is None:
        raise AdapterConfigError("--chapter requires --book")
    with closing(sqlite3.connect(database)) as connection:
        source_hashes, records = read_corpus(connection, book_id=book_id, chapter=chapter)
    if not records:
        raise AdapterConfigError("No verses match the ingestion selection")
    if not source_hashes:
        raise AdapterConfigError("The corpus has no stored source hashes")
    initial_fingerprint = corpus_fingerprint(records, source_hashes)

    documents = build_rag_documents(records, source_hashes)
    config = rag_api.ProcessConfig(min_chunk_length=1, section_token_threshold=10000)
    full_ingestion = book_id is None and chapter is None
    backend = os.environ.get("RAG_VECTOR_STORE_BACKEND", "pgvector").strip().lower()
    vector_path = os.environ.get("RAG_VECTOR_STORE_PATH", "").strip()
    validate_ingestion_request(IngestionRequest(
        plugin_id=APP_ID,
        app_id=APP_ID,
        namespace=RAG_NAMESPACE,
        source_manifest=database,
        chunker_id="cuv-chapter-v1",
        chunker_config_sha256=CHUNKER_CONFIG_SHA256,
        model_id="BAAI/bge-large-zh-v1.5",
        model_revision="79e7739b6ab944e86d6171e44d24c997fc1e0116",
        dimensions=1024,
        destination_index=Path(vector_path or "managed-vector-store"),
    ))
    try:
        if backend in {"json", "json_file"} and vector_path:
            with VectorFileLock(Path(vector_path)):
                results = rag_api.process_files(documents, config)
                if full_ingestion:
                    manifest = read_json_vector_manifest(Path(vector_path), APP_ID)
                    _finalize_full_ingestion(database, initial_fingerprint, manifest)
        else:
            results = rag_api.process_files(documents, config)
            if full_ingestion:
                _finalize_full_ingestion(database, initial_fingerprint, None)
    except AdapterRuntimeError:
        raise
    except Exception as error:
        raise AdapterRuntimeError("RAG ingestion failed") from error

    inserted_chunks = sum(result.inserted for result in results)

    return {
        "status": "ok",
        "app_id": APP_ID,
        "documents": len(documents),
        "inserted_chunks": inserted_chunks,
        "skipped": {
            "too_short": sum(result.skipped_too_short_count for result in results),
            "boilerplate": sum(result.skipped_boilerplate_count for result in results),
            "near_duplicate": sum(result.skipped_near_dup_count for result in results),
        },
        "source_hashes": source_hashes,
        "vector_backend": os.environ.get("RAG_VECTOR_STORE_BACKEND", "pgvector"),
    }


def main(argv: list[str] | None = None, rag_api_loader=load_rag_api) -> int:
    forwarded = list(sys.argv[1:] if argv is None else argv)
    try:
        reexec_code = reexec_if_configured(Path(__file__), forwarded)
        if reexec_code is not None:
            return reexec_code

        arguments = _parser().parse_args(forwarded)
        if arguments.chapter is not None and not arguments.book:
            raise AdapterConfigError("--chapter requires --book")
        book = resolve_book(arguments.book) if arguments.book else None
        data_dir = resolve_data_dir(arguments.data_dir)
        database = data_dir / DATABASE_NAME
        if not database.is_file():
            raise MissingCorpusError("Private CUV corpus was not found")
        rag_api = rag_api_loader()
        payload = ingest_database(
            database,
            rag_api,
            book_id=book.id if book else None,
            chapter=arguments.chapter,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except MissingCorpusError as error:
        _emit_error("missing_corpus", str(error))
        return 2
    except (AdapterConfigError, ValueError, sqlite3.Error) as error:
        _emit_error("invalid_request", str(error))
        return 2
    except AdapterRuntimeError as error:
        _emit_error("rag_unavailable", str(error))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
