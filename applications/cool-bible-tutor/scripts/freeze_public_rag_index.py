"""Convert an authoring JSON vector store into an immutable public SQLite index."""

from __future__ import annotations

import argparse
from array import array
from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
from typing import Iterator, Sequence


APP_ID = "cool-bible-tutor"
MODEL_ID = "BAAI/bge-large-zh-v1.5"
MODEL_ROUTE = "bge-large-zh"
NAMESPACE = f"{APP_ID}:zh:{MODEL_ROUTE}"
PRODUCTION_ITEM_COUNT = 9_942
PRODUCTION_DIMENSIONS = 1_024
FORMAT_VERSION = 1
PUBLIC_METADATA_KEYS = {
    "app_id",
    "book_id",
    "book_name",
    "canonical_reference",
    "chapter",
    "corpus",
    "end_verse",
    "source_files",
    "source_hashes",
    "source_pages",
    "start_verse",
    "unverified_count",
    "verified_all",
}

FINAL_SCHEMA = """
CREATE TABLE index_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    source_order INTEGER NOT NULL UNIQUE,
    doc_id TEXT NOT NULL,
    text TEXT NOT NULL,
    section_path TEXT,
    chunk_order INTEGER NOT NULL,
    language TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    namespace TEXT NOT NULL,
    app_id TEXT,
    embedding BLOB NOT NULL,
    metadata_json TEXT NOT NULL,
    content_hash TEXT NOT NULL
);
CREATE INDEX chunks_namespace_app_id_idx ON chunks(namespace, app_id);
CREATE INDEX chunks_doc_id_idx ON chunks(doc_id);
"""

STAGING_SCHEMA = """
CREATE TABLE staging_chunks (
    chunk_id TEXT PRIMARY KEY,
    source_order INTEGER NOT NULL UNIQUE,
    doc_id TEXT NOT NULL,
    text TEXT NOT NULL,
    section_path TEXT,
    chunk_order INTEGER NOT NULL,
    language TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    namespace TEXT NOT NULL,
    app_id TEXT,
    embedding BLOB NOT NULL,
    metadata_json TEXT NOT NULL,
    content_hash TEXT NOT NULL
);
"""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(payload) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _pretty_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def encode_float32(values: Sequence[float]) -> bytes:
    encoded = array("f", values)
    if encoded.itemsize != 4:
        raise RuntimeError("This Python runtime does not provide 32-bit array('f') values")
    if sys.byteorder != "little":
        encoded.byteswap()
    return encoded.tobytes()


class _JsonStream:
    """Small incremental JSON reader used to avoid loading the 333 MB store."""

    def __init__(self, path: Path, chunk_size: int = 1024 * 1024):
        self.handle = Path(path).open("r", encoding="utf-8")
        self.chunk_size = chunk_size
        self.buffer = ""
        self.position = 0
        self.eof = False
        self.decoder = json.JSONDecoder()

    def close(self) -> None:
        self.handle.close()

    def _fill(self) -> bool:
        if self.eof:
            return False
        if self.position:
            self.buffer = self.buffer[self.position:]
            self.position = 0
        block = self.handle.read(self.chunk_size)
        if block:
            self.buffer += block
            return True
        self.eof = True
        return False

    def _ensure(self) -> bool:
        if self.position < len(self.buffer):
            return True
        return self._fill()

    def skip_space(self) -> None:
        while self._ensure() and self.buffer[self.position].isspace():
            self.position += 1

    def consume(self, expected: str) -> None:
        self.skip_space()
        if not self._ensure() or self.buffer[self.position] != expected:
            raise ValueError(f"invalid JSON vector store: expected {expected!r}")
        self.position += 1

    def peek(self) -> str:
        self.skip_space()
        if not self._ensure():
            return ""
        return self.buffer[self.position]

    def decode(self):
        self.skip_space()
        start = self.position
        while True:
            try:
                value, end = self.decoder.raw_decode(self.buffer, start)
                self.position = end
                return value
            except json.JSONDecodeError as error:
                if self.eof:
                    raise ValueError("invalid JSON vector store") from error
                prefix = self.buffer[start:]
                block = self.handle.read(self.chunk_size)
                if not block:
                    self.eof = True
                    continue
                self.buffer = prefix + block
                self.position = 0
                start = 0


def iter_json_vector_items(path: Path) -> Iterator[dict]:
    stream = _JsonStream(path)
    found_items = False
    try:
        stream.consume("{")
        while stream.peek() != "}":
            key = stream.decode()
            if not isinstance(key, str):
                raise ValueError("invalid JSON vector store object key")
            stream.consume(":")
            if key == "items":
                if found_items:
                    raise ValueError("invalid JSON vector store: duplicate items key")
                found_items = True
                stream.consume("[")
                first = True
                while stream.peek() != "]":
                    if not first:
                        stream.consume(",")
                    item = stream.decode()
                    if not isinstance(item, dict):
                        raise ValueError("invalid JSON vector item")
                    yield item
                    first = False
                stream.consume("]")
            else:
                stream.decode()
            if stream.peek() == ",":
                stream.consume(",")
            elif stream.peek() != "}":
                raise ValueError("invalid JSON vector store object")
        stream.consume("}")
        if stream.peek():
            raise ValueError("invalid JSON vector store trailing content")
        if not found_items:
            raise ValueError("invalid JSON vector store: items array is missing")
    finally:
        stream.close()


def _read_manifest(path: Path, label: str) -> dict:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid {label} manifest") from error
    if not isinstance(payload, dict):
        raise ValueError(f"invalid {label} manifest")
    return payload


def _is_hex_digest(value, length: int) -> bool:
    text = str(value or "")
    return len(text) == length and all(character in "0123456789abcdef" for character in text.lower())


def _validate_manifests(corpus: dict, model: dict) -> int:
    for key in ("database_sha256", "corpus_structure_sha256"):
        if not _is_hex_digest(corpus.get(key), 64):
            raise ValueError(f"invalid corpus manifest {key}")
    if model.get("model_id") != MODEL_ID or model.get("route") != MODEL_ROUTE:
        raise ValueError("embedding model route or model identity is incompatible")
    if not _is_hex_digest(model.get("revision"), 40):
        raise ValueError("embedding model revision must be a pinned 40-character commit")
    try:
        dimensions = int(model["dimensions"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid embedding model dimensions") from error
    files = model.get("files")
    if not isinstance(files, dict) or not files or any(
        not isinstance(name, str) or not _is_hex_digest(digest, 64)
        for name, digest in files.items()
    ):
        raise ValueError("embedding model file digests are required")
    return dimensions


def _public_metadata(metadata: dict) -> dict:
    public = {key: metadata[key] for key in PUBLIC_METADATA_KEYS if key in metadata}
    public["app_id"] = APP_ID
    if public.get("corpus") == "cuv-private":
        public["corpus"] = "cuv-public-runtime"
    return public


def _validated_row(
    item: dict, dimensions: int, source_order: int
) -> tuple[tuple, tuple[str, str, int]]:
    metadata = item.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("invalid vector chunk metadata")
    try:
        doc_id = str(item["doc_id"])
        chunk_id = str(item["chunk_id"])
        order = int(item["order"])
        text = str(item["text"])
        embedding = item["embedding"]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid vector chunk identity or content") from error
    if not doc_id or not chunk_id or not text:
        raise ValueError("invalid vector chunk identity or content")
    if item.get("embedding_model") != MODEL_ROUTE or item.get("namespace") != NAMESPACE:
        raise ValueError("vector chunk model route or namespace is incompatible")
    if item.get("language") != "zh":
        raise ValueError("vector chunk language must be zh")
    if not isinstance(embedding, list) or len(embedding) != dimensions:
        raise ValueError(
            f"embedding dimension mismatch for {chunk_id}: expected={dimensions}"
        )
    try:
        floats = [float(value) for value in embedding]
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid embedding values for {chunk_id}") from error
    if not all(math.isfinite(value) for value in floats):
        raise ValueError(f"invalid embedding values for {chunk_id}")
    public_metadata = _public_metadata(metadata)
    row = (
        chunk_id,
        source_order,
        doc_id,
        text,
        None if item.get("section_path") is None else str(item.get("section_path")),
        order,
        "zh",
        MODEL_ROUTE,
        NAMESPACE,
        APP_ID,
        encode_float32(floats),
        _canonical_json(public_metadata),
        str(item.get("hash", "")),
    )
    return row, (doc_id, chunk_id, order)


def freeze_rag_index(
    json_path: Path,
    output_path: Path,
    corpus_manifest: Path,
    model_manifest: Path,
    *,
    production: bool = False,
) -> dict:
    json_path = Path(json_path).resolve()
    output_path = Path(output_path).resolve()
    corpus_manifest = Path(corpus_manifest).resolve()
    model_manifest = Path(model_manifest).resolve()
    if not json_path.is_file():
        raise FileNotFoundError(json_path)
    corpus = _read_manifest(corpus_manifest, "corpus")
    model = _read_manifest(model_manifest, "embedding model")
    dimensions = _validate_manifests(corpus, model)
    if production and dimensions != PRODUCTION_DIMENSIONS:
        raise ValueError("production embedding dimensions must be 1,024")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".building")
    temporary.unlink(missing_ok=True)
    identities: list[tuple[str, str, int]] = []
    targeted = 0
    try:
        with closing(sqlite3.connect(temporary)) as connection:
            connection.execute("PRAGMA page_size = 4096")
            connection.execute("PRAGMA journal_mode = OFF")
            connection.execute("PRAGMA synchronous = OFF")
            connection.execute("PRAGMA temp_store = MEMORY")
            connection.execute("PRAGMA user_version = 1")
            connection.executescript(STAGING_SCHEMA)
            for item in iter_json_vector_items(json_path):
                metadata = item.get("metadata") or {}
                if metadata.get("app_id") != APP_ID:
                    continue
                row, identity = _validated_row(item, dimensions, targeted)
                try:
                    connection.execute(
                        "INSERT INTO staging_chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        row,
                    )
                except sqlite3.IntegrityError as error:
                    raise ValueError(f"duplicate chunk identity: {identity[1]}") from error
                identities.append(identity)
                targeted += 1

            if targeted == 0:
                raise ValueError(f"no {APP_ID} vector chunks were found")
            if production and targeted != PRODUCTION_ITEM_COUNT:
                raise ValueError(
                    f"production item count mismatch: expected={PRODUCTION_ITEM_COUNT} actual={targeted}"
                )
            identity_sha256 = hashlib.sha256(
                _canonical_json(sorted(identities)).encode("utf-8")
            ).hexdigest()
            metadata_rows = {
                "app_id": APP_ID,
                "corpus_database_sha256": corpus["database_sha256"],
                "corpus_manifest_sha256": _sha256_file(corpus_manifest),
                "corpus_structure_sha256": corpus["corpus_structure_sha256"],
                "dimensions": str(dimensions),
                "format_version": str(FORMAT_VERSION),
                "item_count": str(targeted),
                "model_id": MODEL_ID,
                "model_manifest_sha256": _sha256_file(model_manifest),
                "model_revision": model["revision"],
                "model_route": MODEL_ROUTE,
                "vector_identity_sha256": identity_sha256,
            }
            connection.executescript(FINAL_SCHEMA)
            connection.executemany(
                "INSERT INTO index_metadata(key, value) VALUES (?, ?)",
                sorted(metadata_rows.items()),
            )
            connection.execute(
                """
                INSERT INTO chunks
                SELECT chunk_id, source_order, doc_id, text, section_path, chunk_order, language,
                       embedding_model, namespace, app_id, embedding, metadata_json,
                       content_hash
                  FROM staging_chunks ORDER BY chunk_id
                """
            )
            connection.execute("DROP TABLE staging_chunks")
            connection.commit()
            connection.execute("VACUUM")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise ValueError(f"SQLite integrity check failed: {integrity}")

        manifest = {
            "app_id": APP_ID,
            "corpus_database_sha256": corpus["database_sha256"],
            "corpus_manifest_sha256": _sha256_file(corpus_manifest),
            "corpus_structure_sha256": corpus["corpus_structure_sha256"],
            "dimensions": dimensions,
            "format_version": FORMAT_VERSION,
            "index_sha256": _sha256_file(temporary),
            "item_count": targeted,
            "model_files": model["files"],
            "model_id": MODEL_ID,
            "model_manifest_sha256": _sha256_file(model_manifest),
            "model_revision": model["revision"],
            "model_route": MODEL_ROUTE,
            "schema_version": 1,
            "sqlite_integrity": "ok",
            "vector_identity_sha256": identity_sha256,
        }
        os.replace(temporary, output_path)
        return manifest
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze the public CUV semantic index")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--corpus-manifest", required=True, type=Path)
    parser.add_argument("--model-manifest", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--production", action="store_true")
    arguments = parser.parse_args(argv)
    manifest = freeze_rag_index(
        arguments.source,
        arguments.output,
        arguments.corpus_manifest,
        arguments.model_manifest,
        production=arguments.production,
    )
    _write_text_atomic(arguments.manifest, _pretty_json(manifest))
    print(json.dumps(manifest, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
