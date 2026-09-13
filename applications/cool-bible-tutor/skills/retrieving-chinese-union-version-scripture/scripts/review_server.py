from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import secrets
import sys
import traceback
from urllib.parse import parse_qs, urlsplit

from review_mutations import (
    BackupError, ReviewConflictError, ReviewValidationError, VerseEdit,
)
from review_sources import SourceValidationError
from review_store import ReviewFilters, VerseSnapshot
from rag_metadata_sync import (
    RagMetadataSyncError, RagMetadataSyncIneligible, RagMetadataSyncUnavailable,
)


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes


class ReviewApplication:
    def __init__(
        self, store, mutator, sources, assets, token: str, origin: str, rag_sync=None
    ):
        self.store = store
        self.mutator = mutator
        self.sources = sources
        self.assets = Path(assets).resolve()
        self.token = token
        self.origin = origin
        self.rag_sync = rag_sync
        self._review_items: dict[str, tuple[str, dict]] = {}

    @staticmethod
    def _json(status: int, payload: dict) -> HttpResponse:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return HttpResponse(
            status,
            (("Content-Type", "application/json; charset=utf-8"),
             ("Content-Length", str(len(body)))),
            body,
        )

    @staticmethod
    def _binary(status: int, content_type: str, body: bytes, extra=()) -> HttpResponse:
        return HttpResponse(
            status,
            tuple(extra) + (
                ("Content-Type", content_type),
                ("Content-Length", str(len(body))),
                ("X-Content-Type-Options", "nosniff"),
            ),
            body,
        )

    def _error(self, status: int, code: str, message: str) -> HttpResponse:
        return self._json(status, {
            "status": "error", "error": {"code": code, "message": message},
        })

    def _authorized(self, query: dict[str, list[str]]) -> bool:
        return secrets.compare_digest(query.get("token", [""])[0], self.token)

    def _mutation_authorized(self, headers: dict[str, str]) -> bool:
        normalized = {key.casefold(): value for key, value in headers.items()}
        return (
            secrets.compare_digest(normalized.get("x-review-token", ""), self.token)
            and secrets.compare_digest(normalized.get("origin", ""), self.origin)
        )

    @staticmethod
    def _snapshot(payload: dict) -> VerseSnapshot:
        fields = (
            "book_id", "chapter", "verse", "text", "source_file", "source_page",
            "ocr_confidence", "verified",
        )
        try:
            return VerseSnapshot(**{field: payload[field] for field in fields})
        except (KeyError, TypeError) as error:
            raise ReviewValidationError("A complete expected verse snapshot is required") from error

    @staticmethod
    def _edit(payload: dict) -> VerseEdit:
        fields = (
            "book_id", "chapter", "verse", "text", "source_file", "source_page",
            "ocr_confidence", "verified",
        )
        try:
            return VerseEdit(**{field: payload[field] for field in fields})
        except (KeyError, TypeError) as error:
            raise ReviewValidationError("A complete replacement verse is required") from error

    @staticmethod
    def _integer(query, name, default=None):
        raw = query.get(name, [""])[0]
        if raw == "":
            return default
        try:
            return int(raw)
        except ValueError as error:
            raise ReviewValidationError(f"{name} must be an integer") from error

    def _filters(self, query) -> ReviewFilters:
        return ReviewFilters(
            testament=query.get("testament", [None])[0] or None,
            book_id=self._integer(query, "book_id"),
            chapter=self._integer(query, "chapter"),
            source_page=self._integer(query, "source_page"),
        )

    @staticmethod
    def _decode_json(body: bytes) -> dict:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise _InvalidJson("Request body must be one UTF-8 JSON object") from error
        if not isinstance(payload, dict):
            raise _InvalidJson("Request body must be one UTF-8 JSON object")
        return payload

    def _issues(self, query) -> HttpResponse:
        kind = query.get("kind", [""])[0]
        offset = self._integer(query, "offset", 0)
        limit = self._integer(query, "limit", 50)
        filters = self._filters(query)
        if kind == "gap":
            result = self.store.list_gaps(filters, offset=offset, limit=limit)
        elif kind == "unverified":
            result = self.store.list_unverified_pages(filters, offset=offset, limit=limit)
        else:
            raise ReviewValidationError("kind must be gap or unverified")
        items = []
        for item in result["items"]:
            item_id = secrets.token_urlsafe(18)
            self._review_items[item_id] = (kind, dict(item))
            items.append({**item, "id": item_id})
        result = {**result, "items": items}
        return self._json(200, {"status": "ok", "result": result})

    def _review_item(self, query) -> HttpResponse:
        item_id = query.get("id", [""])[0]
        kind = query.get("kind", [""])[0]
        try:
            saved_kind, saved = self._review_items[item_id]
        except KeyError as error:
            raise LookupError("Review item is not available in this session") from error
        if kind != saved_kind:
            raise LookupError("Review item kind does not match")
        public_by_filename = {
            source["filename"]: source for source in self.sources.public_sources()
        }
        if kind == "unverified":
            snapshots = self.store.page_snapshots(saved["source_file"], saved["source_page"])
            item = {
                **saved,
                "verses": [snapshot.as_dict() for snapshot in snapshots],
                "source": public_by_filename[saved["source_file"]],
            }
        else:
            filenames = {
                saved["previous"]["source_file"], saved["next"]["source_file"]
            }
            item = {
                **saved,
                "sources": [public_by_filename[name] for name in sorted(filenames)],
            }
        return self._json(200, {"status": "ok", "item": item})

    def _source(self, target_path: str, headers: dict[str, str]) -> HttpResponse | None:
        match = re.fullmatch(r"/source/([A-Za-z0-9_-]+)\.pdf", target_path)
        if match is None:
            return None
        try:
            self.sources.get(match.group(1))
        except SourceValidationError:
            return self._error(404, "not_found", "Source document not found")
        normalized = {key.casefold(): value for key, value in headers.items()}
        result = self.sources.read_slice(match.group(1), normalized.get("range"))
        if result.status == 416:
            return self._binary(
                416, "application/pdf", b"", (("Content-Range", f"bytes */{result.total}"),)
            )
        extra = (("Accept-Ranges", "bytes"),)
        if result.status == 206:
            extra += (("Content-Range", f"bytes {result.start}-{result.end}/{result.total}"),)
        return self._binary(result.status, "application/pdf", result.content, extra)

    def _static(self, target_path: str) -> HttpResponse | None:
        if target_path == "/":
            relative = Path("index.html")
        elif target_path.startswith("/review_web/"):
            relative = Path(target_path.removeprefix("/review_web/"))
        else:
            return None
        if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 1:
            return None
        asset = (self.assets / relative).resolve()
        if self.assets != asset.parent or not asset.is_file():
            return None
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
        }.get(asset.suffix.casefold(), mimetypes.guess_type(asset.name)[0] or "application/octet-stream")
        content = asset.read_bytes()
        extra = ()
        if asset.suffix.casefold() == ".html":
            content = content.replace(b"__REVIEW_TOKEN__", self.token.encode("ascii"))
            extra = ((
                "Content-Security-Policy",
                "default-src 'self'; frame-src 'self'; object-src 'self'",
            ),)
        return self._binary(200, content_type, content, extra)

    def _mutate(self, target_path: str, payload: dict) -> HttpResponse | None:
        note = payload.get("note", "")
        if target_path == "/api/verses/update":
            verse = self.mutator.update_verse(
                self._snapshot(payload.get("expected", {})),
                self._edit(payload.get("replacement", {})), note=note,
            )
            return self._json(200, {"status": "ok", "verse": verse.as_dict()})
        if target_path == "/api/verses/insert":
            verse = self.mutator.insert_verse(self._edit(payload.get("replacement", {})), note=note)
            return self._json(201, {"status": "ok", "verse": verse.as_dict()})
        if target_path == "/api/verses/verification":
            rows = tuple(self._snapshot(item) for item in payload.get("expected", ()))
            verses = self.mutator.set_verification(rows, payload.get("verified"), note=note)
            return self._json(200, {"status": "ok", "verses": [row.as_dict() for row in verses]})
        if target_path == "/api/pages/verify":
            rows = tuple(self._snapshot(item) for item in payload.get("expected", ()))
            verses = self.mutator.verify_page(rows, note=note)
            return self._json(200, {"status": "ok", "verses": [row.as_dict() for row in verses]})
        if target_path == "/api/rag/metadata-sync":
            if payload.get("confirmation") != "同步 RAG 核實資料":
                raise ReviewValidationError("請輸入完整確認文字後再同步 RAG 核實資料")
            if self.rag_sync is None:
                raise RagMetadataSyncUnavailable("RAG metadata synchronization is not configured")
            return self._json(200, {
                "status": "ok", "result": self.rag_sync.synchronize(),
            })
        return None

    def dispatch(self, method: str, path: str, headers: dict[str, str], body: bytes) -> HttpResponse:
        target = urlsplit(path)
        if method.upper() in {"GET", "HEAD"} and target.path == "/favicon.ico":
            return HttpResponse(204, (("Content-Length", "0"),), b"")
        query = parse_qs(target.query, keep_blank_values=True)
        if not self._authorized(query):
            return self._error(403, "forbidden", "A valid review-session token is required")
        if method.upper() == "POST" and not self._mutation_authorized(headers):
            return self._error(403, "forbidden", "Mutation origin or token is invalid")
        try:
            if method.upper() in {"GET", "HEAD"}:
                if target.path == "/api/summary":
                    return self._json(200, {
                        "status": "ok", "summary": self.store.summary(),
                        "sources": self.sources.public_sources(),
                        "review": {
                            "backup_created": self.mutator.backup_created,
                            **self.store.review_state(),
                            "rag_metadata_sync": (
                                self.rag_sync.availability() if self.rag_sync is not None
                                else {"available": False, "reason": "not_configured"}
                            ),
                        },
                    })
                if target.path == "/api/issues":
                    return self._issues(query)
                if target.path == "/api/review-item":
                    return self._review_item(query)
                if target.path == "/api/history":
                    return self._json(200, {"status": "ok", "history": self.mutator.history()})
                source = self._source(target.path, headers)
                if source is not None:
                    return source
                static = self._static(target.path)
                if static is not None:
                    return static
            elif method.upper() == "POST":
                response = self._mutate(target.path, self._decode_json(body))
                if response is not None:
                    return response
            return self._error(404, "not_found", "Review resource not found")
        except _InvalidJson as error:
            return self._error(400, "invalid_json", str(error))
        except ReviewConflictError as error:
            return self._error(409, "conflict", str(error))
        except RagMetadataSyncIneligible as error:
            return self._error(409, "rag_metadata_sync_ineligible", str(error))
        except RagMetadataSyncUnavailable as error:
            return self._error(422, "rag_metadata_sync_unavailable", str(error))
        except (ReviewValidationError, SourceValidationError, ValueError) as error:
            return self._error(422, "validation_error", str(error))
        except LookupError as error:
            return self._error(404, "not_found", str(error))
        except BackupError:
            return self._error(500, "backup_failed", "無法建立核對前備份；語料未被修改。")
        except RagMetadataSyncError:
            return self._error(500, "rag_metadata_sync_failed", "RAG 核實資料同步失敗；原索引備份已保留。")
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return self._error(500, "internal_error", "Unexpected local review error")


class _InvalidJson(ValueError):
    pass


class _ReviewHttpServer(ThreadingHTTPServer):
    daemon_threads = True


def serve(application: ReviewApplication, port: int = 0) -> ThreadingHTTPServer:
    if not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format, *args):
            return

        def do_GET(self):
            self._dispatch()

        def do_HEAD(self):
            self._dispatch(head_only=True)

        def do_POST(self):
            self._dispatch()

        def _dispatch(self, head_only=False):
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = -1
            if length < 0 or length > 1024 * 1024:
                response = application._error(400, "invalid_request", "Invalid request length")
            else:
                body = self.rfile.read(length) if length else b""
                response = application.dispatch(
                    self.command, self.path, dict(self.headers.items()), body
                )
            self.send_response(response.status)
            for name, value in response.headers:
                self.send_header(name, value)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if not head_only and response.body:
                self.wfile.write(response.body)

    server = _ReviewHttpServer(("127.0.0.1", port), Handler)
    application.origin = f"http://127.0.0.1:{server.server_address[1]}"
    return server
