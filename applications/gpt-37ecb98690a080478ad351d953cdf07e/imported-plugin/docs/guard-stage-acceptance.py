"""Representative, side-effect-free acceptance scenarios for screenplay_guard.py."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = []
spec = importlib.util.spec_from_file_location("screenplay_guard", ROOT / "scripts/screenplay_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def fixture():
    source = "SC01 Beat B01: A choice changes the scene."
    mapping = [{"screenplay_scene_id": "SC01", "screenplay_revision": "r1",
                "beat_ids": ["B01"], "source_anchors": ["SC01 Beat B01"]}]
    data = {
        "route": "PROFESSIONAL", "stage": "P7", "previous_stage": "P7",
        "screenplay": {"id": "SCRIPT", "revision": "r1", "source_text": source,
                       "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                       "scenes": [{"scene_id": "SC01", "beat_ids": ["B01"]}]},
        "mapping": mapping, "beat_lineage_mode": "SCRIPT_DERIVED",
        "beat_source_revision": "r1", "beat_source_anchors": ["SC01 Beat B01"],
        "approval": {"screenplay_id": "SCRIPT", "revision": "r1", "actor": "OWNER",
                     "decision_proof": "owner-record-1", "scope": "SCREENPLAY_AND_MAP_TO_STORYBOARD",
                     "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                     "p7_map_sha256": guard.digest(mapping)},
        "dependency_check_status": "CHECKED_PASS", "nonhard_issues": ["pacing"],
        "nonhard_issue_acknowledgment": "owner-record-1",
        "gates": {name: ({"status": "NOT_APPLICABLE", "reason": "Original fiction"}
                         if name == "SCRIPTURE_SOURCE" else {"status": "PASS"})
                  for name in guard.GATES},
        "required_reference_ids": sorted(guard.BRIDGE_REFS),
        "consultations": [{"reference_id": ref, "resolved_version_or_sha256": "v1",
                           "actual_access_evidence": "read-event", "knowledge_applied": "rule",
                           "output_anchor": "P7", "consultation_state": "CONSULTED"}
                          for ref in sorted(guard.BRIDGE_REFS)],
    }
    return data


def expect(label, func, data, status, issue=None):
    actual = func(data)
    assert actual["status"] == status, (label, actual)
    if issue:
        assert issue in actual["issues"], (label, actual)
    RESULTS.append({"scenario": label, "status": actual["status"],
                    "issues": actual["issues"]})


d = fixture()
p7 = guard.p7_check(d)
assert p7["status"] == "P7_APPROVED_FOR_P8_ENTRY"
expect("P7 without shots", guard.p7_check, d, "P7_APPROVED_FOR_P8_ENTRY")

split = copy.deepcopy(d)
split["screenplay"]["scenes"][0]["beat_ids"].append("B02")
split["mapping"].append({"screenplay_scene_id": "SC01", "screenplay_revision": "r1",
                         "beat_ids": ["B02"], "source_anchors": ["SC01 Beat B02"]})
split["approval"]["p7_map_sha256"] = guard.digest(split["mapping"])
expect("two beat rows for one scene", guard.p7_check, split, "P7_APPROVED_FOR_P8_ENTRY")

csv_source = copy.deepcopy(d)
csv_text = "\ufeffscene_id,beat_id,source_anchor\nSC01,B01,SC01 Beat B01\n"
csv_source["p7_map_source"] = {"format": "BEAT_LEVEL_CSV_V1", "text": csv_text}
csv_source["approval"]["p7_map_sha256"] = hashlib.sha256(csv_text.encode()).hexdigest()
expect("approved CSV map", guard.p7_check, csv_source, "P7_APPROVED_FOR_P8_ENTRY")
csv_source["mapping"][0]["source_anchors"] = ["invented anchor"]
expect("CSV projection mismatch", guard.p7_check, csv_source,
       "BLOCKED_PENDING_FIX_OR_EVIDENCE", "MAP_SOURCE_PROJECTION_MISMATCH")

e = copy.deepcopy(d)
e["stage"] = "P8"
e["p7_result"] = p7
expect("P8 current entry", guard.p8_entry_check, e, "READY_TO_DRAFT_STORYBOARD")

draft = copy.deepcopy(e)
draft["shot_mapping"] = [{"screenplay_scene_id": "SC01", "screenplay_revision": "r1",
                          "beat_ids": ["B01"], "storyboard_shot_ids": ["SH01"]}]
expect("P8 covered draft", guard.p8_draft_check, draft, "DRAFT_STORYBOARD_VALIDATED")

for label, mutate, func, issue in [
    ("changed source", lambda x: x["screenplay"].update(source_text="changed"), guard.p7_check,
     "EXACT_SOURCE_DIGEST_UNVERIFIED"),
    ("stale map", lambda x: x["mapping"][0].update(screenplay_revision="r0"), guard.p7_check,
     "UNMATCHED_OR_STALE_MAPPING"),
    ("absent approval", lambda x: x.update(approval={}), guard.p7_check,
     "EXACT_OWNER_APPROVAL_REQUIRED"),
    ("missing consultation", lambda x: x["consultations"].pop(), guard.p7_check,
     "REFERENCE_CONSULTATION_UNVERIFIED:RM-W03"),
    ("wrong gate", lambda x: x["gates"].update(OWNER_AUTHORITY={"status": "PASS"}), guard.p7_check,
     "NONCANONICAL_GATE_REGISTRY"),
    ("stale dependency", lambda x: x.update(dependency_check_status="NOT_CHECKED"), guard.p7_check,
     "DEPENDENCY_NOT_CURRENT"),
]:
    item = copy.deepcopy(d)
    mutate(item)
    expect(label, func, item, "BLOCKED_PENDING_FIX_OR_EVIDENCE", issue)

item = copy.deepcopy(e)
item["previous_stage"] = "PF"
expect("PF bypass", guard.p8_entry_check, item, "BLOCKED_PENDING_FIX_OR_EVIDENCE", "P7_ONLY_INBOUND")
item = copy.deepcopy(e)
item["screenplay"]["revision"] = "r2"
expect("P8 changed revision", guard.p8_entry_check, item,
       "BLOCKED_PENDING_FIX_OR_EVIDENCE", "CURRENT_P7_RESULT_REQUIRED")
item = copy.deepcopy(e)
item["shot_mapping"] = [{"screenplay_scene_id": "SC01", "screenplay_revision": "r1",
                         "beat_ids": ["B01"]}]
expect("missing shot or disposition", guard.p8_draft_check, item,
       "BLOCKED_PENDING_FIX_OR_EVIDENCE", "SHOT_OR_APPROVED_DISPOSITION_REQUIRED:SC01")
expect("legacy call fails closed", guard.bridge, d,
       "BLOCKED_PENDING_FIX_OR_EVIDENCE", "EXPLICIT_STAGE_OPERATION_REQUIRED")
for route in ("QUICK_STORYBOARD", "NON_NARRATIVE_MUSIC"):
    item = copy.deepcopy(d)
    item["route"] = route
    expect(route, guard.p7_check, item, "NOT_APPLICABLE")

print(json.dumps({"acceptance": "PASS", "scenario_count": len(RESULTS),
                  "scenarios": RESULTS}, sort_keys=True))
