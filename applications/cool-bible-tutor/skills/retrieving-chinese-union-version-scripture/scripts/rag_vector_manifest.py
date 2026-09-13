import hashlib
import json
from pathlib import Path


def vector_identity_sha256(items: list[dict], app_id: str) -> str:
    identities = []
    for item in items:
        metadata = item.get("metadata") or {}
        if metadata.get("app_id") != app_id:
            continue
        try:
            identity = (
                str(item["doc_id"]), str(item["chunk_id"]), int(item["order"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("invalid vector chunk identity") from error
        identities.append(identity)
    return hashlib.sha256(json.dumps(
        sorted(identities), ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def read_json_vector_manifest(path: Path, app_id: str) -> dict:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("invalid JSON vector store") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError("invalid JSON vector store")
    items = payload["items"]
    targeted = sum(
        isinstance(item, dict)
        and (item.get("metadata") or {}).get("app_id") == app_id
        for item in items
    )
    return {
        "targeted_items": targeted,
        "identity_sha256": vector_identity_sha256(items, app_id),
    }
