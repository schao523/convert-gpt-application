"""One-time deterministic repair for the 0.2.1 wheel's missing package markers.

The vendored source commit contains modules in utils/ and vector_store/ but
omits their __init__.py files. Preserve the wheel's code and metadata while
adding the markers, regenerating RECORD, and rebinding runtime manifests.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import os
import zipfile


ROOT = Path(__file__).resolve().parents[1]
WHEEL = ROOT / "vendor" / "rag-subsystem" / "rag_subsystem-0.2.1-py3-none-any.whl"
RECORD = "rag_subsystem-0.2.1.dist-info/RECORD"
MARKERS = (
    "rag_subsystem/utils/__init__.py",
    "rag_subsystem/vector_store/__init__.py",
)


def _record_entry(name: str, data: bytes) -> tuple[str, str, str]:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode("ascii")
    return name, f"sha256={digest}", str(len(data))


def repair() -> str:
    with zipfile.ZipFile(WHEEL) as source:
        entries = {
            name: source.read(name)
            for name in source.namelist()
            if name != RECORD
        }
        missing = [name for name in MARKERS if name not in entries]
        if missing:
            for name in missing:
                entries[name] = b"\"\"\"Python package marker for vendored RAG modules.\"\"\"\n"
    if missing:
        rows = [_record_entry(name, entries[name]) for name in sorted(entries)]
        rows.append((RECORD, "", ""))
        stream = io.StringIO(newline="")
        csv.writer(stream, lineterminator="\n").writerows(rows)
        entries[RECORD] = stream.getvalue().encode("utf-8")
        temporary = WHEEL.with_suffix(".whl.tmp")
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for name in sorted(entries):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                target.writestr(info, entries[name])
        os.replace(temporary, WHEEL)

    wheel_digest = hashlib.sha256(WHEEL.read_bytes()).hexdigest()
    wheel_manifest = ROOT / "vendor" / "rag-subsystem" / "manifest.json"
    lock_manifest = ROOT / "vendor" / "rag-runtime" / "runtime-lock.json"
    openclaw_manifest = ROOT / "openclaw" / "distribution.json"
    vendor = json.loads(wheel_manifest.read_text(encoding="utf-8"))
    lock = json.loads(lock_manifest.read_text(encoding="utf-8"))
    openclaw_text = openclaw_manifest.read_text(encoding="utf-8")
    openclaw = json.loads(openclaw_text)
    previous_lock_id = str(openclaw["rag"]["runtime_lock_digest"])
    vendor["wheel_sha256"] = wheel_digest
    vendor["packaging_patch"] = "explicit package markers for utils and vector_store"
    lock["wheel_sha256"] = wheel_digest
    # A changed wheel must not alias the old, already-installed private venv.
    lock_id = hashlib.sha256(
        bytes.fromhex(lock["requirements_sha256"]) + bytes.fromhex(wheel_digest)
    ).hexdigest()
    lock["runtime_lock_id"] = lock_id
    for path, payload in (
        (wheel_manifest, vendor),
        (lock_manifest, lock),
    ):
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    openclaw_manifest.write_text(
        openclaw_text.replace(previous_lock_id, lock_id), encoding="utf-8"
    )
    return lock_id


if __name__ == "__main__":
    print(repair())
