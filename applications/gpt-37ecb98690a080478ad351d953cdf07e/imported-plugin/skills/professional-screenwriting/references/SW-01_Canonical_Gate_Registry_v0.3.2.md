# SW-01 Canonical Gate Registry — v0.3.2 RIC-01 DRAFT

**Authority:** Design contract, pending owner approval. Identical semantics to RM-W03 §2A; it is not a new independent gate system. Workflow P5/P7/P8 and IM-SW-04/06/07/09 must use the six exact IDs below.

| Gate ID | When required | Passing evidence | When not checked / blocked |
|---|---|---|---|
| SOURCE_AND_AUTHORITY | Source provenance/authority claims or professional bridge | Verified exact source identity, version, authority for intended claim | Cannot claim supported source compliance or bridge readiness |
| RIGHTS_FOR_INTENDED_USE | Adaptation, quotation, transformation, export, publication, uploads as applicable | Rights supported for the exact intended use, not general possession | Block only the affected use; private critique may still be allowed |
| SCRIPTURE_SOURCE | Bible-mode accuracy or explicit biblical quotation/attribution | Actual relevant passage/translation checked and invented text distinguished | Block unsupported exact quote/fidelity claim or corresponding source-faithful handoff |
| CANONICAL_CONTINUITY | Material affected scene, known fact, provenance/dependency or professional bridge | Exact current scene/beat identity/dependency/knowledge checks pass | Block unresolved contradiction or unchecked mandatory dependency |
| APPROVAL_INTEGRITY | Protected user decisions and professional P7→P8 | Explicit actor/decision/scope for current exact screenplay ID/revision; P7 transaction commits proof | Wrong/absent/inferred/stale approval blocks action |
| REFERENCE_CONSULTATION | Any reference-backed claim, P7/P8 consulted required references | Per-use ConsultationRecords with actual content access and distinct knowledge application | Missing, unread, wrong version or unproven read blocks dependent conformance |

`gate_status` is one of `PASS | BLOCK | NOT_CHECKED | NOT_APPLICABLE`. N/A requires documented reason for nonapplicability and **is not PASS**; if a gate applies and is NOT_CHECKED, no protected transition. `NONE` is a non-gate editorial classification only.

**Legacy aliases:** `OWNER_AUTHORITY` is deprecated; convert to `APPROVAL_INTEGRITY` only for exact decision authority. `RIGHTS` must be refined to `RIGHTS_FOR_INTENDED_USE`. Do not map `SOURCE_AND_AUTHORITY` to `SCRIPTURE_SOURCE`. Unrecognized identifiers fail closed as `NOT_CHECKED`. Status is per requested action and current revision.

**P7 transaction:** Gather current script and beat-lineage and reference/rights evidence → list applicable gate states → seek owner explicit exact-revision storyboard-transfer confirmation → validate and record `APPROVAL_INTEGRITY=PASS` → move to P8 only if all applicable required gates PASS. P8 repeats checks, even after retry/resume. No P8 inbound edge besides P7.

**Consultation evidence:** See `Design_Control/SW-01_Reference_Material_Evaluation_and_Usage_Map.md` §4 for `ConsultationRecord` format and acceptance. Never certify runtime access from ZIP indexes, manual filename lists, or the existence of a package.
