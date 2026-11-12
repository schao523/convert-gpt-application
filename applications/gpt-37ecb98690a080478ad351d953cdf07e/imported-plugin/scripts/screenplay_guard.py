#!/usr/bin/env python3
"""Local, side-effect-free SW-01 stage checks. JSON object on stdin, JSON on stdout."""
import argparse
import csv
import hashlib
import io
import json
import sys

GATES = (
    "SOURCE_AND_AUTHORITY", "RIGHTS_FOR_INTENDED_USE", "SCRIPTURE_SOURCE",
    "CANONICAL_CONTINUITY", "APPROVAL_INTEGRITY", "REFERENCE_CONSULTATION",
)
STATUSES = {"PASS", "BLOCK", "NOT_CHECKED", "NOT_APPLICABLE"}
LINEAGE = {"SCRIPT_DERIVED", "BEAT_SHEET_RECONCILED"}
BRIDGE_REFS = {"RM-W03", "RM-P01", "RM-P05"}


def unique_ids(rows, key, issues):
    values = [r.get(key) if isinstance(r, dict) else None for r in rows]
    if any(not isinstance(x, str) or not x for x in values) or len(values) != len(set(values)):
        issues.append("INVALID_OR_DUPLICATE_" + key.upper())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     separators=(',', ':')).encode()).hexdigest()


def result(operation, status, issues, **extra):
    return {"operation": operation, "status": status, "issues": sorted(set(issues)), **extra}


def check_consultations(data, required, issues):
    rows = data.get("consultations", [])
    if not isinstance(rows, list):
        issues.append("INVALID_CONSULTATIONS")
        return
    for ref in required:
        matched = [r for r in rows if isinstance(r, dict) and r.get("reference_id") == ref]
        if not any(r.get("resolved_version_or_sha256") and r.get("actual_access_evidence")
                   and r.get("knowledge_applied") and r.get("output_anchor")
                   and r.get("consultation_state") == "CONSULTED" for r in matched):
            issues.append("REFERENCE_CONSULTATION_UNVERIFIED:" + ref)


def check_gates(data, issues):
    gates = data.get("gates")
    if not isinstance(gates, dict) or set(gates) != set(GATES):
        issues.append("NONCANONICAL_GATE_REGISTRY")
        return
    for name in GATES:
        entry = gates[name]
        if not isinstance(entry, dict) or entry.get("status") not in STATUSES:
            issues.append("INVALID_GATE_STATUS:" + name)
            continue
        status = entry["status"]
        if status == "NOT_APPLICABLE":
            if not entry.get("reason") or entry.get("required") is True or name != "SCRIPTURE_SOURCE":
                issues.append("INVALID_GATE_NONAPPLICABILITY:" + name)
        elif entry.get("required") is False:
            issues.append("INVALID_GATE_APPLICABILITY:" + name)
        elif status != "PASS":
            issues.append("GATE_NOT_PASS:" + name)


def p7_check(data):
    operation = "p7-check"
    issues = []
    if data.get("route") in {"QUICK_STORYBOARD", "NON_NARRATIVE_MUSIC"}:
        return result(operation, "NOT_APPLICABLE", issues)
    if data.get("route") != "PROFESSIONAL":
        return result(operation, "BLOCKED_PENDING_FIX_OR_EVIDENCE", ["ROUTE_UNVERIFIED"])
    script = data.get("screenplay", {})
    approval = data.get("approval", {})
    if not isinstance(script, dict) or not script.get("id") or not script.get("revision"):
        issues.append("SCRIPT_ID_REVISION_REQUIRED")
        script = {}
    source_text = script.get("source_text")
    source_sha = script.get("source_sha256")
    if not isinstance(source_text, str) or not isinstance(source_sha, str) or \
            hashlib.sha256(source_text.encode('utf-8')).hexdigest() != source_sha:
        issues.append("EXACT_SOURCE_DIGEST_UNVERIFIED")
    if not isinstance(approval, dict) or any(approval.get(k) != script.get(v)
            for k, v in (("screenplay_id", "id"), ("revision", "revision"))) \
            or not approval.get("actor") or not approval.get("decision_proof") \
            or approval.get("scope") != "SCREENPLAY_AND_MAP_TO_STORYBOARD" \
            or approval.get("source_sha256") != source_sha:
        issues.append("EXACT_OWNER_APPROVAL_REQUIRED")
    scenes = script.get("scenes", [])
    mapping = data.get("mapping", [])
    if not isinstance(scenes, list) or not isinstance(mapping, list):
        issues.append("SCENE_MAP_REQUIRED")
        scenes, mapping = [], []
    if not scenes or not mapping:
        issues.append("SCENE_MAP_EMPTY")
    unique_ids(scenes, "scene_id", issues)
    scene_ids = {s.get("scene_id") for s in scenes if isinstance(s, dict)}
    if any(not isinstance(m, dict) or m.get("screenplay_scene_id") not in scene_ids
           or m.get("screenplay_revision") != script.get("revision") for m in mapping):
        issues.append("UNMATCHED_OR_STALE_MAPPING")
    if {m.get("screenplay_scene_id") for m in mapping if isinstance(m, dict)} != scene_ids:
        issues.append("SCENE_MAP_INCOMPLETE")
    for scene in scenes:
        if not isinstance(scene, dict):
            issues.append("SCENE_INVALID")
            continue
        beats = scene.get("beat_ids", [])
        if not isinstance(beats, list) or not beats or any(not isinstance(b, str) or not b for b in beats):
            issues.append("BEAT_IDS_MISSING:" + str(scene.get("scene_id")))
            beats = []
        matched = [m for m in mapping if isinstance(m, dict) and m.get("screenplay_scene_id") == scene.get("scene_id")
                   and m.get("screenplay_revision") == script.get("revision")]
        mapped_rows = [b for m in matched if isinstance(m.get("beat_ids"), list) for b in m["beat_ids"]]
        mapped_beats = set(mapped_rows)
        if len(mapped_rows) != len(mapped_beats):
            issues.append("DUPLICATE_BEAT_MAPPING:" + str(scene.get("scene_id")))
        if not matched or set(beats) != mapped_beats or not all(m.get("source_anchors") for m in matched):
            issues.append("SCENE_BEAT_MAPPING_INCOMPLETE:" + str(scene.get("scene_id")))
    if data.get("beat_lineage_mode") not in LINEAGE or not data.get("beat_source_anchors"):
        issues.append("BEAT_LINEAGE_UNVERIFIED")
    if data.get("beat_lineage_mode") == "SCRIPT_DERIVED" and data.get("beat_source_revision") != script.get("revision"):
        issues.append("BEAT_SOURCE_REVISION_STALE")
    map_source = data.get("p7_map_source")
    if map_source is None:
        map_digest = digest(mapping)
    elif isinstance(map_source, dict) and map_source.get("format") == "BEAT_LEVEL_CSV_V1" and \
            isinstance(map_source.get("text"), str):
        raw = map_source["text"]
        map_digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        try:
            records = list(csv.DictReader(io.StringIO(raw.lstrip('\ufeff'))))
            expected_rows = sorted((r["scene_id"], r["beat_id"], r["source_anchor"]) for r in records)
            observed_rows = sorted((m["screenplay_scene_id"], b, a)
                                   for m in mapping for b in m["beat_ids"] for a in m["source_anchors"])
            if not records or expected_rows != observed_rows:
                issues.append("MAP_SOURCE_PROJECTION_MISMATCH")
        except (KeyError, TypeError, ValueError):
            issues.append("MAP_SOURCE_PROJECTION_INVALID")
    else:
        map_digest = None
        issues.append("MAP_SOURCE_FORMAT_UNSUPPORTED")
    if not isinstance(approval, dict) or approval.get("p7_map_sha256") != map_digest:
        issues.append("EXACT_MAP_APPROVAL_REQUIRED")
    if data.get("dependency_check_status") != "CHECKED_PASS":
        issues.append("DEPENDENCY_NOT_CURRENT")
    if data.get("nonhard_issues") and not data.get("nonhard_issue_acknowledgment"):
        issues.append("NONHARD_ISSUES_UNACKNOWLEDGED")
    check_gates(data, issues)
    supplied_refs = data.get("required_reference_ids", [])
    if not isinstance(supplied_refs, list) or any(not isinstance(r, str) for r in supplied_refs):
        supplied_refs = []
        issues.append("REFERENCE_REGISTER_INVALID")
    if not BRIDGE_REFS.issubset(set(supplied_refs)):
        issues.append("MANDATORY_BRIDGE_REFERENCES_UNDECLARED")
    check_consultations(data, sorted(BRIDGE_REFS | set(supplied_refs)), issues)
    identity = {"screenplay_id": script.get("id"), "revision": script.get("revision"),
                "source_sha256": source_sha, "p7_map_sha256": map_digest,
                "decision_proof": approval.get("decision_proof") if isinstance(approval, dict) else None}
    return result(operation, "P7_APPROVED_FOR_P8_ENTRY" if not issues else "BLOCKED_PENDING_FIX_OR_EVIDENCE",
                  issues, identity=identity, evidence_digest=digest(identity))


def p8_entry_check(data):
    operation = "p8-entry-check"
    base = p7_check(data)
    if base["status"] == "NOT_APPLICABLE":
        return result(operation, "NOT_APPLICABLE", [])
    issues = list(base["issues"])
    if data.get("stage") != "P8" or data.get("previous_stage") != "P7":
        issues.append("P7_ONLY_INBOUND")
    proof = data.get("p7_result")
    if not isinstance(proof, dict) or proof.get("status") != "P7_APPROVED_FOR_P8_ENTRY" or \
            proof.get("evidence_digest") != base.get("evidence_digest") or \
            proof.get("identity") != base.get("identity"):
        issues.append("CURRENT_P7_RESULT_REQUIRED")
    return result(operation, "READY_TO_DRAFT_STORYBOARD" if not issues else "BLOCKED_PENDING_FIX_OR_EVIDENCE",
                  issues, identity=base.get("identity"), evidence_digest=base.get("evidence_digest"))


def p8_draft_check(data):
    operation = "p8-draft-check"
    entry = p8_entry_check(data)
    if entry["status"] == "NOT_APPLICABLE":
        return result(operation, "NOT_APPLICABLE", [])
    issues = list(entry["issues"])
    rows = data.get("shot_mapping")
    scenes = data.get("screenplay", {}).get("scenes", [])
    if not isinstance(rows, list) or not rows:
        rows = []
        issues.append("SHOT_MAP_REQUIRED")
    shot_ids = []
    for scene in scenes if isinstance(scenes, list) else []:
        if not isinstance(scene, dict):
            continue
        matched = [r for r in rows if isinstance(r, dict) and r.get("screenplay_scene_id") == scene.get("scene_id")]
        covered = set()
        for row in matched:
            if row.get("screenplay_revision") != data.get("screenplay", {}).get("revision"):
                issues.append("SHOT_MAP_REVISION_STALE")
            beats = row.get("beat_ids")
            if not isinstance(beats, list) or not beats:
                issues.append("SHOT_MAP_BEATS_INVALID")
                continue
            covered.update(beats)
            shots = row.get("storyboard_shot_ids")
            disposition = row.get("approved_disposition")
            if shots:
                if not isinstance(shots, list) or any(not isinstance(s, str) or not s for s in shots):
                    issues.append("SHOT_IDS_INVALID")
                else:
                    shot_ids.extend(shots)
            elif not isinstance(disposition, dict) or not disposition.get("owner_proof") or \
                    not disposition.get("reason") or disposition.get("beat_ids") != beats:
                issues.append("SHOT_OR_APPROVED_DISPOSITION_REQUIRED:" + str(scene.get("scene_id")))
        if not matched or covered != set(scene.get("beat_ids", [])):
            issues.append("SHOT_COVERAGE_INCOMPLETE:" + str(scene.get("scene_id")))
    if any(not isinstance(r, dict) or r.get("screenplay_scene_id") not in
           {s.get("scene_id") for s in scenes if isinstance(s, dict)} for r in rows):
        issues.append("SHOT_MAP_UNMATCHED_SCENE")
    if len(shot_ids) != len(set(shot_ids)):
        issues.append("DUPLICATE_SHOT_ID")
    return result(operation, "DRAFT_STORYBOARD_VALIDATED" if not issues else "BLOCKED_PENDING_FIX_OR_EVIDENCE",
                  issues, identity=entry.get("identity"), shot_map_sha256=digest(rows))


def bridge(data):
    """Legacy name is deliberately fail-closed; callers must choose a stage."""
    return result("bridge-check", "BLOCKED_PENDING_FIX_OR_EVIDENCE", ["EXPLICIT_STAGE_OPERATION_REQUIRED"])


def revision(data):
    issues = []
    if data.get("original_revision") == data.get("new_revision") or not data.get("original_revision"):
        issues.append("REVISION_IDENTITY_INVALID")
    changes = data.get("changes", [])
    if not isinstance(changes, list):
        changes = []
        issues.append("CHANGE_LEDGER_INVALID")
    if not changes:
        issues.append("CHANGE_LEDGER_EMPTY")
    unique_ids(changes, "change_id", issues)
    for c in changes:
        if not isinstance(c, dict):
            issues.append("CHANGE_INVALID")
            continue
        if c.get("state") in {"APPLIED_UNVERIFIED", "VERIFIED", "REGRESSED"}:
            if not c.get("exact_scope_apply_authorization") or not c.get("original_anchor"):
                issues.append("APPLY_AUTHORIZATION_MISSING:" + str(c.get("change_id")))
            if c.get("state") in {"VERIFIED", "REGRESSED"} and (not c.get("before_after_evidence") or not c.get("cross_scene_regression")):
                issues.append("REVISION_VERIFICATION_MISSING:" + str(c.get("change_id")))
        elif c.get("state") not in {"PROPOSED", "ACCEPTED_NOT_APPLIED", "REJECTED", "DEFERRED"}:
            issues.append("CHANGE_STATE_INVALID:" + str(c.get("change_id")))
    return {"operation": "revision-check", "status": "VERIFIED" if not issues else "NOT_VERIFIED", "issues": sorted(set(issues))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("p7-check", "p8-entry-check", "p8-draft-check",
                                              "bridge-check", "revision-check", "self-test"))
    args = parser.parse_args()
    if args.operation == "self-test":
        example = {"route": "PROFESSIONAL", "stage": "P8", "previous_stage": "PF"}
        assert "EXPLICIT_STAGE_OPERATION_REQUIRED" in bridge(example)["issues"]
        assert "P7_ONLY_INBOUND" in p8_entry_check(example)["issues"]
        assert revision({"original_revision": "r1", "new_revision": "r2", "changes": [{"change_id": "x", "state": "APPLIED_UNVERIFIED"}]})["status"] == "NOT_VERIFIED"
        print(json.dumps({"self_test": "PASS"}))
        return
    data = json.load(sys.stdin)
    outcome = {"p7-check": p7_check, "p8-entry-check": p8_entry_check,
               "p8-draft-check": p8_draft_check, "bridge-check": bridge,
               "revision-check": revision}[args.operation](data)
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
