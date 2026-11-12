# Screenplay guard runtime contract (1.0.4 candidate)

The installed Skill resolves the plugin root from its own file location (`skills/professional-screenwriting/SKILL.md` → two parents up). Invoke `[python_executable, plugin_root/scripts/screenplay_guard.py, operation]` with a bounded direct process call, JSON object on stdin and JSON stdout. Python 3.10+, bundled file access and runtime command permission are required. No shell, network, credentials or provider actions. A manifest declaration does not register a callable tool. In Work, use the Work installation path; in local Codex, use the local installation path. If command execution is absent, return `NOT_VERIFIED` and hold the protected transition.

| Operation | Required stage data | Successful status |
| --- | --- | --- |
| `p7-check` | `route=PROFESSIONAL`, `screenplay` with ID, revision, exact UTF-8 `source_text`, `source_sha256`, scenes and beat IDs; source-anchored `mapping`; owner `approval` bound to script, source hash and `p7_map_sha256`; lineage, current dependencies, six gates, required reference IDs and consultation records | `P7_APPROVED_FOR_P8_ENTRY` |
| `p8-entry-check` | Freshly checked P7 fields plus `stage=P8`, `previous_stage=P7`, and exact structured `p7_result` from the approved P7 check | `READY_TO_DRAFT_STORYBOARD` |
| `p8-draft-check` | All P8-entry data plus actual `shot_mapping` rows with scene, revision, beat IDs and ordered `storyboard_shot_ids` or an explicit owner-proof disposition | `DRAFT_STORYBOARD_VALIDATED` |
| `revision-check` | Previous/new revision and authorized change ledger | `VERIFIED` |

The P7 map can be a canonical JSON array, with `p7_map_sha256` equal to its sorted-key compact JSON digest, **only when that exact representation is approved**. For an approved `Beat_Level_Source_Map.csv`, supply `p7_map_source={"format":"BEAT_LEVEL_CSV_V1","text":<the exact UTF-8 file text including BOM if present>}` and bind `approval.p7_map_sha256` to the SHA-256 of those source bytes. The guard compares the scene/beat/source-anchor projection to the supplied rows. Record the actual approval package and manifest provenance outside the guard; a caller cannot manufacture owner approval by filling JSON fields. Do not equate a newly normalized map digest with the owner's approval of the CSV.

On P8, retain the approved P7 map hash and check fresh dependencies. The `shot_mapping` has a distinct digest returned only by `p8-draft-check`. P7 does not require shot IDs. A failed draft validation keeps the draft blocked; no production approval follows. `bridge-check` returns a structured blocked result requiring an explicit stage operation. A process exit code of zero can accompany a blocked result, so inspect `status` and `issues`.
