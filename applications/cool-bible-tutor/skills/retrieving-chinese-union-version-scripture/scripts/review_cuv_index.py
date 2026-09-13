import argparse
from contextlib import closing
import os
from pathlib import Path
import secrets
import sqlite3
import sys
import webbrowser

from corpus_db import DATABASE_NAME, resolve_data_dir
from review_mutations import ReviewMutator
from review_server import ReviewApplication, serve
from review_sources import SourceRegistry
from review_store import ReviewStore
from rag_metadata_sync import RagMetadataSynchronizer
from scripture_sources import resolve_bundled_sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review the private CUV corpus against validated local PDFs."
    )
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--source-pdf", type=Path, action="append", default=[])
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-open", action="store_true")
    return parser


def resolve_source_paths(explicit, environ=None) -> tuple[Path, ...]:
    environ = os.environ if environ is None else environ
    values = tuple(explicit)
    if not values:
        configured = environ.get("COOL_BIBLE_TUTOR_SOURCE_PDFS", "")
        values = tuple(Path(value) for value in configured.split(os.pathsep) if value.strip())
    if not values:
        return resolve_bundled_sources()
    return tuple(Path(value).expanduser().resolve() for value in values)


def build_application(
    data_dir, source_paths, token: str, session_id: str, assets=None, environ=None
) -> ReviewApplication:
    data_dir = Path(data_dir).expanduser().resolve()
    database = data_dir / DATABASE_NAME
    if not database.is_file():
        raise FileNotFoundError(f"CUV database not found: {database}")
    with closing(sqlite3.connect(database)) as connection:
        sources = SourceRegistry.from_database(connection, source_paths)
    allowed_sources = {item["filename"] for item in sources.public_sources()}
    asset_dir = Path(assets).resolve() if assets is not None else Path(__file__).with_name("review_web")
    return ReviewApplication(
        ReviewStore(database),
        ReviewMutator(database, data_dir, session_id, allowed_sources),
        sources,
        asset_dir,
        token=token,
        origin="http://127.0.0.1",
        rag_sync=RagMetadataSynchronizer(
            database, environ=os.environ if environ is None else environ,
        ),
    )


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data_dir = resolve_data_dir(args.data_dir)
        source_paths = resolve_source_paths(args.source_pdf)
        token = secrets.token_urlsafe(32)
        application = build_application(
            data_dir, source_paths, token=token, session_id=secrets.token_urlsafe(18)
        )
        server = serve(application, args.port)
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"Cannot start CUV review tool: {error}", file=sys.stderr)
        return 2

    url = f"{application.origin}/?token={token}"
    print(url, flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
