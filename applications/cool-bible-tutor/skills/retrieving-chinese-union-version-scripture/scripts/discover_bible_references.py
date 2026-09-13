import argparse
from contextlib import closing
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
    from obvious_one_runtime.adapters import (
        AdapterContractError,
        DiscoveryRequest,
        validate_discovery_results,
    )
except ModuleNotFoundError:
    REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
    if str(REPOSITORY_ROOT) not in sys.path:
        sys.path.insert(0, str(REPOSITORY_ROOT))
    from obvious_one_plugin_framework.adapters import (
        AdapterContractError,
        DiscoveryRequest,
        validate_discovery_results,
    )

from book_names import Book, resolve_book
from corpus_db import DATABASE_NAME, fetch_passage, resolve_data_dir
from rag_documents import APP_ID
from rag_runtime import (
    AdapterConfigError,
    AdapterRuntimeError,
    build_bundled_rag_environment,
    load_rag_api,
    managed_runtime_environment,
    reexec_if_configured,
)
from references import ReferenceRequest, parse_reference


RAG_NAMESPACE = "cool-bible-tutor:zh:bge-large-zh"


class MissingCorpusError(AdapterConfigError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise AdapterConfigError(message)


def _parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Discover Bible references through RAGenius")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--book")
    parser.add_argument("--data-dir", type=Path)
    return parser


def _emit_error(code: str, message: str) -> None:
    print(json.dumps({
        "status": "error",
        "error": {"code": code, "message": message},
    }, ensure_ascii=True))


def read_source_hashes(connection: sqlite3.Connection) -> dict[str, str]:
    rows = connection.execute(
        "SELECT key, value FROM metadata WHERE key LIKE 'source_sha256:%' ORDER BY key"
    ).fetchall()
    return {key.split(":", 1)[1]: value for key, value in rows}


def parse_source_hashes(value) -> dict[str, str]:
    text = str(value or "").strip()
    if not text:
        return {}
    parsed: dict[str, str] = {}
    for pair in text.split(";"):
        if "=" not in pair:
            return {}
        name, digest = pair.rsplit("=", 1)
        name, digest = name.strip(), digest.strip()
        if not name or not digest or name in parsed:
            return {}
        parsed[name] = digest
    return parsed


def format_request(request: ReferenceRequest) -> str:
    book = request.book.canonical_zh
    if request.start_verse is None:
        return f"{book} {request.start_chapter}"
    if (request.start_chapter, request.start_verse) == (request.end_chapter, request.end_verse):
        return f"{book} {request.start_chapter}:{request.start_verse}"
    if request.start_chapter == request.end_chapter:
        return f"{book} {request.start_chapter}:{request.start_verse}-{request.end_verse}"
    return (
        f"{book} {request.start_chapter}:{request.start_verse}-"
        f"{request.end_chapter}:{request.end_verse}"
    )


def discover_references(
    query: str,
    top_k: int,
    connection: sqlite3.Connection,
    rag_api,
    book: Book | None = None,
) -> dict:
    normalized_query = query.strip()
    if not normalized_query:
        raise AdapterConfigError("--query must not be blank")
    requested = max(1, min(int(top_k), 50))
    filters = {"app_id": APP_ID}
    if book is not None:
        filters["book_id"] = str(book.id)
    contract_request = DiscoveryRequest(
        plugin_id=APP_ID,
        app_id=APP_ID,
        namespace=RAG_NAMESPACE,
        query=normalized_query,
        filters=filters,
        limit=min(requested * 3, 150),
        corpus_identity="cuv-public-v1",
        model_identity="BAAI/bge-large-zh-v1.5@79e7739b6ab944e86d6171e44d24c997fc1e0116",
    )
    try:
        result = rag_api.retrieve_data(
            normalized_query,
            top_k=contract_request.limit,
            filters=filters,
            config=rag_api.default_retrieval_config,
        )
        validate_discovery_results(contract_request, result.results)
    except AdapterContractError as error:
        raise AdapterRuntimeError(str(error)) from error
    except Exception as error:
        raise AdapterRuntimeError("RAG discovery failed") from error

    current_hashes = read_source_hashes(connection)
    state_row = connection.execute(
        "SELECT value FROM metadata WHERE key = 'rag_index_state'"
    ).fetchone()
    globally_stale = state_row is not None and state_row[0] == "stale"
    candidates: list[dict] = []
    seen: set[str] = set()
    invalid_count = 0
    duplicate_count = 0
    for retrieved in result.results:
        try:
            raw_reference = str(retrieved.chunk.metadata.get("canonical_reference", ""))
            request = parse_reference(raw_reference)
            canonical = format_request(request)
        except (AttributeError, TypeError, ValueError):
            invalid_count += 1
            continue
        if canonical in seen:
            duplicate_count += 1
            continue
        seen.add(canonical)

        try:
            passage = fetch_passage(connection, request)
            explicit_same_chapter = (
                request.start_verse is not None
                and request.end_verse is not None
                and request.start_chapter == request.end_chapter
            )
            expected = (
                list(range(request.start_verse, request.end_verse + 1))
                if explicit_same_chapter else []
            )
            actual = [
                record.verse
                for record in passage.records
                if record.chapter == request.start_chapter
            ]
            complete = explicit_same_chapter and actual == expected
            trust_status = (
                "verified" if complete and passage.verified
                else "unverified" if complete
                else "missing"
            )
            source_files = sorted({record.source_file for record in passage.records})
            source_pages = sorted({record.source_page for record in passage.records})
        except LookupError:
            trust_status = "missing"
            source_files = []
            source_pages = []

        indexed_hashes = parse_source_hashes(retrieved.chunk.metadata.get("source_hashes", ""))
        rag_index_status = (
            "stale" if globally_stale
            else "unknown" if not indexed_hashes
            else "current" if all(
                current_hashes.get(name) == digest for name, digest in indexed_hashes.items()
            )
            else "stale"
        )
        candidates.append({
            "reference": canonical,
            "rank": len(candidates) + 1,
            "retrieval_source": retrieved.source,
            "trust_status": trust_status,
            "rag_index_status": rag_index_status,
            "source_files": source_files,
            "source_pages": source_pages,
        })
        if len(candidates) == requested:
            break

    return {
        "status": "ok",
        "query": normalized_query,
        "app_id": APP_ID,
        "candidates": candidates,
        "diagnostics": {
            "retrieved_count": len(result.results),
            "returned_count": len(candidates),
            "invalid_reference_count": invalid_count,
            "duplicate_reference_count": duplicate_count,
        },
    }


def main(argv: list[str] | None = None, rag_api_loader=load_rag_api) -> int:
    forwarded = list(sys.argv[1:] if argv is None else argv)
    try:
        if rag_api_loader is load_rag_api:
            managed_environment, runtime_report = managed_runtime_environment(os.environ)
            if runtime_report.status != "rag_ready":
                print(json.dumps({
                    "status": "setup_required",
                    "rag_status": runtime_report.status,
                    "core_ready": runtime_report.core_ready,
                    "reasons": list(runtime_report.reasons),
                    "next_command": "python scripts/cool_bible_tutor.py setup-rag",
                }, ensure_ascii=True, indent=2))
                return 4
            os.environ.update(managed_environment)
        reexec_code = reexec_if_configured(Path(__file__), forwarded)
        if reexec_code is not None:
            return reexec_code

        arguments = _parser().parse_args(forwarded)
        os.environ.update(build_bundled_rag_environment(os.environ))
        data_dir = resolve_data_dir(arguments.data_dir)
        database = data_dir / DATABASE_NAME
        if not database.is_file():
            raise MissingCorpusError("Private CUV corpus was not found")
        book = resolve_book(arguments.book) if arguments.book else None
        rag_api = rag_api_loader()
        with closing(sqlite3.connect(database)) as connection:
            payload = discover_references(
                arguments.query,
                arguments.top_k,
                connection,
                rag_api,
                book,
            )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
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
