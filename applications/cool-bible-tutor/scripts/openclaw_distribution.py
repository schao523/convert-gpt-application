"""Cool Bible Tutor-specific audit hook for lightweight generated packages."""

from __future__ import annotations

import json
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from distribution_audit import audit_public_corpus


EXPECTED_SKILLS = {
    "applying-biblical-truth",
    "comparing-biblical-words-and-translations",
    "discussing-biblical-theology",
    "guiding-bible-tutor-sessions",
    "interpreting-biblical-passages",
    "observing-biblical-passages",
    "retrieving-chinese-union-version-scripture",
    "supporting-biblical-exegesis",
}


def audit_cool_bible_tutor(stage: Path, _contract) -> list[str]:
    errors = audit_public_corpus(stage)
    skills_root = stage / "skills"
    actual_skills = {
        candidate.name for candidate in skills_root.iterdir()
        if candidate.is_dir() and (candidate / "SKILL.md").is_file()
    } if skills_root.is_dir() else set()
    if actual_skills != EXPECTED_SKILLS:
        errors.append("Bible Tutor skill allowlist mismatch")
    if any("church" in candidate.name.lower() and "ministry" in candidate.name.lower()
           for candidate in stage.rglob("*")):
        errors.append("church ministry prompt-template module is present")
    try:
        runtime = json.loads(
            (stage / "assets/scripture/cuv-runtime-manifest.json").read_text(encoding="utf-8")
        )
        gaps = json.loads(
            (stage / "assets/scripture/cuv-approved-gaps.json").read_text(encoding="utf-8")
        )
        if runtime.get("approved_source_gaps") != 71 or len(gaps.get("gaps", [])) != 71:
            errors.append("approved source-gap count mismatch")
        if runtime.get("sqlite_integrity") != "ok" or runtime.get("row_count") != 31008:
            errors.append("production CUV readiness mismatch")
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append("production CUV manifests are invalid")
    return sorted(set(errors))
