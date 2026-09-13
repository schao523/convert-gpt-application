from array import array
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

from rag_vector_lock import VectorFileBusyError, VectorFileLock
from rag_vector_manifest import vector_identity_sha256


APP_ID = "cool-bible-tutor"


class RagMetadataSyncError(RuntimeError):
    pass


class RagMetadataSyncUnavailable(RagMetadataSyncError):
    pass


class RagMetadataSyncIneligible(RagMetadataSyncError):
    pass


class RagMetadataSynchronizer:
    def __init__(self, database: Path, environ=None, lock_timeout: float = 5.0):
        self.database = Path(database).expanduser().resolve()
        self.environ = os.environ if environ is None else environ
        self.lock_timeout = lock_timeout

    def availability(self) -> dict:
        backend = str(self.environ.get("RAG_VECTOR_STORE_BACKEND", "pgvector")).strip().lower()
        if backend not in {"json", "json_file"}:
            return {
                "available": False,
                "reason": "metadata_only_sync_requires_json_backend",
            }
        raw_path = str(self.environ.get("RAG_VECTOR_STORE_PATH", "")).strip()
        if not raw_path or not Path(raw_path).expanduser().is_file():
            return {
                "available": False,
                "reason": "vector_store_not_available",
            }
        return {"available": True, "reason": None}

    def _vector_path(self) -> Path:
        availability = self.availability()
        if not availability["available"]:
            if availability["reason"] == "metadata_only_sync_requires_json_backend":
                raise RagMetadataSyncUnavailable(
                    "Metadata-only synchronization currently requires the JSON vector backend"
                )
            raise RagMetadataSyncUnavailable("The configured JSON vector store is not available")
        return Path(self.environ["RAG_VECTOR_STORE_PATH"]).expanduser().resolve()

    @staticmethod
    def _utc_stamp() -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        return (
            now.isoformat().replace("+00:00", "Z"),
            now.strftime("%Y%m%dT%H%M%S%fZ"),
        )

    @staticmethod
    def _corpus_snapshot(connection: sqlite3.Connection) -> dict:
        rows = connection.execute(
            """
            SELECT book_id, chapter, verse, text, source_file, source_page,
                   ocr_confidence, verified
            FROM verses ORDER BY book_id, chapter, verse
            """
        ).fetchall()
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        source_hashes = {
            key[14:]: value for key, value in metadata.items()
            if key.startswith("source_sha256:")
        }
        digest = hashlib.sha256()
        structure = hashlib.sha256()
        by_key = {}
        for row in rows:
            values = tuple(row)
            by_key[values[:3]] = values
            structure.update(f"{values[0]}:{values[1]}:{values[2]}\n".encode("ascii"))
            digest.update(json.dumps(
                values, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8"))
            digest.update(b"\n")
        for filename, source_digest in sorted(source_hashes.items()):
            digest.update(filename.encode("utf-8"))
            digest.update(b"=")
            digest.update(source_digest.encode("ascii"))
            digest.update(b"\n")
        return {
            "rows": by_key,
            "source_hashes": source_hashes,
            "metadata": metadata,
            "structure_sha256": structure.hexdigest(),
            "fingerprint": digest.hexdigest(),
        }

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _vector_fingerprints(items: list[dict]) -> dict:
        content = hashlib.sha256()
        embeddings = hashlib.sha256()
        targeted = 0
        for item in items:
            if not isinstance(item, dict):
                raise RagMetadataSyncIneligible("The JSON vector store contains an invalid item")
            metadata = item.get("metadata") or {}
            if metadata.get("app_id") == APP_ID:
                targeted += 1
            for key in ("chunk_id", "text", "hash"):
                content.update(str(item.get(key, "")).encode("utf-8"))
                content.update(b"\0")
            embedding = item.get("embedding")
            if not isinstance(embedding, list):
                raise RagMetadataSyncIneligible("The JSON vector store contains an invalid embedding")
            embeddings.update(str(item.get("chunk_id", "")).encode("utf-8"))
            embeddings.update(b"\0")
            embeddings.update(array("d", (float(value) for value in embedding)).tobytes())
        return {
            "item_count": len(items),
            "targeted_items": targeted,
            "content_sha256": content.hexdigest(),
            "embedding_sha256": embeddings.hexdigest(),
        }

    @staticmethod
    def _expected_trust(item: dict, snapshot: dict) -> tuple[str, str]:
        metadata = item.get("metadata") or {}
        try:
            book_id = int(metadata["book_id"])
            chapter = int(metadata["chapter"])
            start_verse = int(metadata["start_verse"])
            end_verse = int(metadata["end_verse"])
        except (KeyError, TypeError, ValueError) as error:
            raise RagMetadataSyncIneligible(
                "Vector text or provenance does not match the current corpus"
            ) from error
        if start_verse < 1 or end_verse < start_verse:
            raise RagMetadataSyncIneligible(
                "Vector text or provenance does not match the current corpus"
            )
        expected_doc_id = f"cuv:{book_id}:{chapter}"
        chunk_id = str(item.get("chunk_id", ""))
        expected_prefix = expected_doc_id + "::"
        suffix = chunk_id[len(expected_prefix):] if chunk_id.startswith(expected_prefix) else ""
        try:
            int(item.get("order"))
        except (TypeError, ValueError) as error:
            raise RagMetadataSyncIneligible(
                "The JSON vector store has invalid chunk identities"
            ) from error
        if item.get("doc_id") != expected_doc_id or not suffix.isdigit():
            raise RagMetadataSyncIneligible(
                "The JSON vector store has invalid chunk identities"
            )
        rows = []
        for verse in range(start_verse, end_verse + 1):
            row = snapshot["rows"].get((book_id, chapter, verse))
            if row is None:
                raise RagMetadataSyncIneligible(
                    "Vector text or provenance does not match the current corpus"
                )
            rows.append(row)
        expected_text = "\n".join(f"{chapter}:{row[2]} {row[3]}" for row in rows)
        source_files = sorted({row[4] for row in rows})
        source_pages = sorted({row[5] for row in rows})
        try:
            source_hashes = ";".join(
                f"{filename}={snapshot['source_hashes'][filename]}"
                for filename in source_files
            )
        except KeyError as error:
            raise RagMetadataSyncIneligible(
                "Vector text or provenance does not match the current corpus"
            ) from error
        expected_provenance = {
            "source_files": ",".join(source_files),
            "source_pages": ",".join(str(page) for page in source_pages),
            "source_hashes": source_hashes,
        }
        if item.get("text") != expected_text or any(
            str(metadata.get(key, "")) != value
            for key, value in expected_provenance.items()
        ):
            raise RagMetadataSyncIneligible(
                "Vector text or provenance does not match the current corpus"
            )
        unverified = sum(not bool(row[7]) for row in rows)
        return ("true" if unverified == 0 else "false", str(unverified))

    @staticmethod
    def _load_payload(vector_path: Path) -> dict:
        try:
            payload = json.loads(vector_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise RagMetadataSyncIneligible("The JSON vector store is unreadable or invalid") from error
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            raise RagMetadataSyncIneligible("The JSON vector store is unreadable or invalid")
        return payload

    @staticmethod
    def _write_atomic(vector_path: Path, payload: dict) -> None:
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", delete=False, encoding="utf-8",
                dir=str(vector_path.parent), suffix=".metadata-sync.tmp",
            ) as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
                temporary_path = Path(handle.name)
            os.replace(temporary_path, vector_path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    @classmethod
    def _restore_atomic(cls, backup_path: Path, vector_path: Path) -> None:
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "wb", delete=False, dir=str(vector_path.parent), suffix=".restore.tmp",
            ) as handle, backup_path.open("rb") as source:
                shutil.copyfileobj(source, handle)
                handle.flush()
                os.fsync(handle.fileno())
                temporary_path = Path(handle.name)
            os.replace(temporary_path, vector_path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def synchronize(self) -> dict:
        vector_path = self._vector_path()
        try:
            with VectorFileLock(vector_path, timeout=self.lock_timeout):
                return self._synchronize_locked(vector_path)
        except VectorFileBusyError as error:
            raise RagMetadataSyncUnavailable(str(error)) from error

    def _synchronize_locked(self, vector_path: Path) -> dict:
        initial_digest = self._file_sha256(vector_path)
        payload = self._load_payload(vector_path)
        items = payload["items"]
        before = self._vector_fingerprints(items)
        if before["targeted_items"] == 0:
            raise RagMetadataSyncIneligible("No cool-bible-tutor chunks are available")
        with closing(sqlite3.connect(self.database)) as connection:
            corpus = self._corpus_snapshot(connection)

        metadata = corpus["metadata"]
        if metadata.get("rag_index_state") != "stale":
            raise RagMetadataSyncIneligible("The RAG index is not marked stale")
        recorded_count = metadata.get("rag_vector_item_count")
        recorded_structure = metadata.get("rag_corpus_structure_sha256")
        recorded_identity = metadata.get("rag_vector_identity_sha256")
        if recorded_count is None or recorded_structure is None or recorded_identity is None:
            raise RagMetadataSyncIneligible(
                "A successful full ingestion is required before metadata-only synchronization"
            )
        try:
            expected_count = int(recorded_count)
        except ValueError as error:
            raise RagMetadataSyncIneligible("The recorded vector item count is invalid") from error
        if expected_count != before["targeted_items"]:
            raise RagMetadataSyncIneligible("The vector item count changed; run full ingestion")
        if recorded_structure != corpus["structure_sha256"]:
            raise RagMetadataSyncIneligible("The corpus structure changed; run full ingestion")
        try:
            current_identity = vector_identity_sha256(items, APP_ID)
        except ValueError as error:
            raise RagMetadataSyncIneligible(
                "The JSON vector store has invalid chunk identities"
            ) from error
        if recorded_identity != current_identity:
            raise RagMetadataSyncIneligible("The vector chunk identity changed; run full ingestion")

        planned = {}
        for item in items:
            metadata = item.get("metadata") or {}
            if metadata.get("app_id") != APP_ID:
                continue
            chunk_id = str(item.get("chunk_id", ""))
            if not chunk_id or chunk_id in planned:
                raise RagMetadataSyncIneligible("The JSON vector store has invalid chunk identities")
            planned[chunk_id] = self._expected_trust(item, corpus)

        if self._file_sha256(vector_path) != initial_digest:
            raise RagMetadataSyncIneligible("The JSON vector store changed during validation")

        now, stamp = self._utc_stamp()
        backup_path = vector_path.with_name(
            f"{vector_path.stem}.before-metadata-sync-{stamp}{vector_path.suffix}"
        )
        try:
            shutil.copy2(vector_path, backup_path)
        except OSError as error:
            raise RagMetadataSyncError("Unable to create the RAG metadata backup") from error
        if self._file_sha256(vector_path) != initial_digest:
            raise RagMetadataSyncIneligible("The JSON vector store changed during validation")

        changed = 0
        for item in items:
            metadata = item.get("metadata") or {}
            if metadata.get("app_id") != APP_ID:
                continue
            verified_all, unverified_count = planned[item["chunk_id"]]
            if (
                metadata.get("verified_all") != verified_all
                or metadata.get("unverified_count") != unverified_count
            ):
                changed += 1
            metadata["verified_all"] = verified_all
            metadata["unverified_count"] = unverified_count
            item["metadata"] = metadata

        replaced = False
        try:
            self._write_atomic(vector_path, payload)
            replaced = True
            verified_payload = self._load_payload(vector_path)
            verified_items = verified_payload["items"]
            after = self._vector_fingerprints(verified_items)
            for key in ("item_count", "targeted_items", "content_sha256", "embedding_sha256"):
                if before[key] != after[key]:
                    raise RagMetadataSyncError("RAG metadata post-write validation failed")
            verified_by_id = {
                item.get("chunk_id"): item for item in verified_items
                if (item.get("metadata") or {}).get("app_id") == APP_ID
            }
            for chunk_id, expected in planned.items():
                metadata = (verified_by_id.get(chunk_id) or {}).get("metadata") or {}
                if (metadata.get("verified_all"), metadata.get("unverified_count")) != expected:
                    raise RagMetadataSyncError("RAG metadata post-write validation failed")

            with closing(sqlite3.connect(self.database)) as connection:
                connection.execute("BEGIN IMMEDIATE")
                current_corpus = self._corpus_snapshot(connection)
                if current_corpus["fingerprint"] != corpus["fingerprint"]:
                    connection.rollback()
                    raise RagMetadataSyncIneligible(
                        "The corpus changed during RAG metadata synchronization"
                    )
                connection.execute(
                    "DELETE FROM metadata WHERE key IN ('rag_index_state', 'rag_index_stale_at')"
                )
                connection.executemany(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                    (
                        ("rag_metadata_sync_method", "metadata_only_reuse_embeddings"),
                        ("rag_metadata_sync_at", now),
                        ("rag_metadata_sync_vector_items", str(after["targeted_items"])),
                    ),
                )
                connection.commit()
        except Exception:
            if replaced:
                original = sys.exc_info()[1]
                try:
                    self._restore_atomic(backup_path, vector_path)
                except Exception as restore_error:
                    if original is not None and hasattr(original, "add_note"):
                        original.add_note(f"Atomic RAG rollback also failed: {restore_error}")
            raise

        return {
            "targeted_items": after["targeted_items"],
            "changed_items": changed,
            "backup_name": backup_path.name,
            "content_unchanged": before["content_sha256"] == after["content_sha256"],
            "embeddings_unchanged": before["embedding_sha256"] == after["embedding_sha256"],
        }
