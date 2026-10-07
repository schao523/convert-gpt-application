"""Target-aware manifest presentation and release-readiness validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


_PROFILES = {"PRIVATE_LOCAL", "RELEASE_READY"}
_PLACEHOLDER = re.compile(r"(?i)^\s*(?:todo|tbd|placeholder|n/?a)\s*$")
_LISTING_FIELDS = ("homepage", "repository", "license", "keywords", "icons", "brand_colors")


@dataclass(frozen=True)
class ManifestProfileReport:
    diagnostics: tuple[str, ...]
    evidence: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return dict(self.evidence)


def _status(value: object, present: bool) -> str:
    if present and value is None:
        return "NOT_APPLICABLE"
    if present and value not in ("", [], {}):
        return "SUPPLIED"
    return "UNRESOLVED"


def validate_manifest_profile(
    root: Path,
    decision: dict[str, Any],
    vocabulary_path: Path,
) -> ManifestProfileReport:
    diagnostics: list[str] = []
    try:
        manifest = json.loads((Path(root) / "plugin.json").read_text(encoding="utf-8"))
        vocabulary = json.loads(Path(vocabulary_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ManifestProfileReport(("manifest.profile_input_invalid",), {})
    expected_keys = {"target", "profile", "vocabulary_version", "extensions"}
    extensions = decision.get("extensions") if isinstance(decision, dict) else None
    if (
        not isinstance(decision, dict)
        or set(decision) != expected_keys
        or decision.get("target") != "OPENAI_DESKTOP"
        or decision.get("profile") not in _PROFILES
        or decision.get("vocabulary_version") != "obvious-one-openai-interface-v1"
        or not isinstance(extensions, dict)
        or set(extensions) != {"categories", "capabilities"}
        or any(not isinstance(extensions[key], list) or extensions[key] != sorted(set(extensions[key])) for key in extensions)
    ):
        diagnostics.append("manifest.profile_decision_invalid")
        extensions = {"categories": [], "capabilities": []}
    if vocabulary.get("schema") != "obvious-one-openai-interface-v1":
        diagnostics.append("manifest.vocabulary_invalid")
    interface = (((manifest.get("extensions") or {}).get("com.openai") or {}).get("interface") or {})
    author = manifest.get("author")
    if not isinstance(author, dict) or not isinstance(author.get("name"), str) or not author["name"].strip():
        diagnostics.append("manifest.author_invalid")
    required_text = {
        "description": manifest.get("description"),
        "developer_name": interface.get("developerName"),
        "display_name": interface.get("displayName"),
        "short_description": interface.get("shortDescription"),
        "long_description": interface.get("longDescription"),
        "default_prompt": interface.get("defaultPrompt"),
    }
    for field, value in required_text.items():
        if not isinstance(value, str) or not value.strip():
            diagnostics.append(f"manifest.{field}_invalid")
        elif _PLACEHOLDER.fullmatch(value):
            diagnostics.append(f"manifest.{field}_placeholder")
    category = interface.get("category")
    categories = set(vocabulary.get("categories", [])) | set(extensions.get("categories", []))
    if category not in categories:
        diagnostics.append(f"manifest.category_unknown:{category}")
    capabilities = interface.get("capabilities")
    known_capabilities = set(vocabulary.get("capabilities", [])) | set(extensions.get("capabilities", []))
    if not isinstance(capabilities, list):
        diagnostics.append("manifest.capabilities_invalid")
    else:
        for capability in capabilities:
            if capability not in known_capabilities:
                diagnostics.append(f"manifest.capability_unknown:{capability}")
    listing_values = {
        "homepage": (manifest.get("homepage"), "homepage" in manifest),
        "repository": (manifest.get("repository"), "repository" in manifest),
        "license": (manifest.get("license"), "license" in manifest),
        "keywords": (manifest.get("keywords"), "keywords" in manifest),
        "icons": (
            [manifest.get("logo"), manifest.get("logoDark"), interface.get("iconSmall"), interface.get("iconLarge")],
            any(key in manifest for key in ("logo", "logoDark")) or any(key in interface for key in ("iconSmall", "iconLarge")),
        ),
        "brand_colors": (
            [manifest.get("brandColor"), manifest.get("brandColorDark")],
            any(key in manifest for key in ("brandColor", "brandColorDark")),
        ),
    }
    listing_status = {
        field: _status(*listing_values[field]) for field in _LISTING_FIELDS
    }
    if decision.get("profile") == "RELEASE_READY":
        diagnostics.extend(
            f"manifest.release_metadata_unresolved:{field}"
            for field, status in listing_status.items()
            if status == "UNRESOLVED"
        )
    evidence = {
        "schema": "plugin-builder-manifest-profile-v1",
        "target": decision.get("target"),
        "profile": decision.get("profile"),
        "vocabulary_version": decision.get("vocabulary_version"),
        "listing_status": dict(sorted(listing_status.items())),
    }
    return ManifestProfileReport(tuple(sorted(set(diagnostics))), evidence)


__all__ = ["ManifestProfileReport", "validate_manifest_profile"]
