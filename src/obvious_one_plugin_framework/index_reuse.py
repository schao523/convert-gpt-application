"""Build-time derivation of independent indexes from compatible vector bytes."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sqlite3
import uuid


class IndexReuseError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class ReuseReport:
    eligible: bool
    mismatches: tuple[str, ...]


@dataclass(frozen=True)
class DerivedIndexRecord:
    path: Path
    sha256: str
    vector_identity_sha256: str
    item_count: int
    app_id: str
    namespace: str


def _read_manifest(path: Path) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IndexReuseError("invalid_manifest", str(path)) from exc
    if not isinstance(value, dict):
        raise IndexReuseError("invalid_manifest", str(path))
    return value


def _file_sha(path: Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _compare(source: dict[str, object], target: dict[str, object]) -> set[str]:
    mismatches: set[str] = set()
    for field in ("schema_version", "source_files", "corpus_structure_sha256", "chunks"):
        if source.get(field) != target.get(field):
            mismatches.add(field)
    for group, fields in {
        "chunker": ("id", "config_sha256"),
        "model": ("id", "revision", "dimensions", "normalize"),
        "vector": ("schema", "serialization"),
    }.items():
        source_group = source.get(group)
        target_group = target.get(group)
        if not isinstance(source_group, dict) or not isinstance(target_group, dict):
            mismatches.add(group)
            continue
        for field in fields:
            if source_group.get(field) != target_group.get(field):
                mismatches.add(f"{group}.{field}")
    return mismatches


def _validate_source_index(index: Path, manifest: dict[str, object]) -> set[str]:
    mismatches: set[str] = set()
    try:
        uri = Path(index).resolve().as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                mismatches.add("source_index.integrity")
            columns = {row[1] for row in connection.execute("PRAGMA table_info(chunks)")}
            required = {"chunk_id", "app_id", "namespace", "text", "content_hash", "embedding", "metadata_json"}
            if not required.issubset(columns):
                mismatches.add("source_index.schema")
                return mismatches
            rows = connection.execute(
                "SELECT chunk_id, app_id, namespace, text, content_hash, length(embedding) "
                "FROM chunks ORDER BY chunk_id"
            ).fetchall()
    except (OSError, sqlite3.Error) as exc:
        raise IndexReuseError("invalid_source_index", str(index)) from exc
    if {row[1] for row in rows} != {manifest.get("app_id")}:
        mismatches.add("source_index.app_id")
    if {row[2] for row in rows} != {manifest.get("namespace")}:
        mismatches.add("source_index.namespace")
    chunks = manifest.get("chunks")
    if not isinstance(chunks, list) or len(chunks) != len(rows):
        mismatches.add("source_index.chunks")
    else:
        expected = {
            str(chunk.get("chunk_id")): (
                str(chunk.get("text_sha256")), str(chunk.get("content_hash"))
            )
            for chunk in chunks if isinstance(chunk, dict)
        }
        for chunk_id, _app, _namespace, text, content_hash, vector_size in rows:
            if expected.get(chunk_id) != (sha256(text.encode("utf-8")).hexdigest(), content_hash):
                mismatches.add("source_index.chunks")
            dimensions = manifest.get("model", {}).get("dimensions") if isinstance(manifest.get("model"), dict) else None
            if not isinstance(dimensions, int) or vector_size != dimensions * 4:
                mismatches.add("source_index.vector_dimensions")
    return mismatches


def check_index_reuse(
    source_manifest: Path,
    target_manifest: Path,
    source_index: Path,
) -> ReuseReport:
    source = _read_manifest(source_manifest)
    target = _read_manifest(target_manifest)
    mismatches = _compare(source, target)
    mismatches.update(_validate_source_index(source_index, source))
    source_app = source.get("app_id")
    target_app = target.get("app_id")
    source_namespace = source.get("namespace")
    target_namespace = target.get("namespace")
    if not all(isinstance(value, str) and value for value in (
        source_app, target_app, source_namespace, target_namespace
    )):
        mismatches.add("identity")
    elif not str(target_namespace).startswith(str(target_app) + ":"):
        mismatches.add("target.namespace")
    return ReuseReport(not mismatches, tuple(sorted(mismatches)))


def _vector_identity(connection: sqlite3.Connection, app_id: str, namespace: str) -> str:
    digest = sha256()
    digest.update(app_id.encode("utf-8") + b"\0" + namespace.encode("utf-8") + b"\0")
    for chunk_id, content_hash, embedding in connection.execute(
        "SELECT chunk_id, content_hash, embedding FROM chunks ORDER BY chunk_id"
    ):
        digest.update(chunk_id.encode("utf-8") + b"\0")
        digest.update(content_hash.encode("ascii") + b"\0")
        digest.update(sha256(embedding).digest())
    return digest.hexdigest()


def derive_index(
    source_index: Path,
    destination: Path,
    source_manifest: Path,
    target_manifest: Path,
) -> DerivedIndexRecord:
    report = check_index_reuse(source_manifest, target_manifest, source_index)
    if not report.eligible:
        raise IndexReuseError("reembedding_required", ",".join(report.mismatches))
    source = _read_manifest(source_manifest)
    target = _read_manifest(target_manifest)
    source_app = str(source["app_id"])
    source_namespace = str(source["namespace"])
    target_app = str(target["app_id"])
    target_namespace = str(target["namespace"])
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = destination.with_name(f".{destination.name}.stage-{uuid.uuid4().hex}")
    try:
        shutil.copyfile(source_index, stage)
        with closing(sqlite3.connect(stage)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute("SELECT chunk_id, metadata_json FROM chunks").fetchall()
            for chunk_id, metadata_json in rows:
                metadata = json.loads(metadata_json)
                metadata["app_id"] = target_app
                metadata["namespace"] = target_namespace
                connection.execute(
                    "UPDATE chunks SET app_id=?, namespace=?, metadata_json=? WHERE chunk_id=?",
                    (target_app, target_namespace,
                     json.dumps(metadata, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                     chunk_id),
                )
            connection.executemany(
                "INSERT OR REPLACE INTO index_metadata(key,value) VALUES (?,?)",
                (("app_id", target_app), ("namespace", target_namespace),
                 ("derived_from_app_id", source_app),
                 ("derived_from_namespace", source_namespace)),
            )
            vector_identity = _vector_identity(connection, target_app, target_namespace)
            connection.execute(
                "INSERT OR REPLACE INTO index_metadata(key,value) VALUES (?,?)",
                ("vector_identity_sha256", vector_identity),
            )
            if connection.execute(
                "SELECT COUNT(*) FROM chunks WHERE app_id<>? OR namespace<>? OR metadata_json LIKE ? OR metadata_json LIKE ?",
                (target_app, target_namespace, f"%{source_app}%", f"%{source_namespace}%"),
            ).fetchone()[0]:
                raise IndexReuseError("source_identity_remains")
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise IndexReuseError("derived_index_integrity")
            item_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            connection.commit()
        os.replace(stage, destination)
    finally:
        stage.unlink(missing_ok=True)
    return DerivedIndexRecord(
        path=destination,
        sha256=_file_sha(destination),
        vector_identity_sha256=vector_identity,
        item_count=int(item_count),
        app_id=target_app,
        namespace=target_namespace,
    )
