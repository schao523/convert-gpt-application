# Source Handoff from Chat to Work

Use this route when Assistant A in Chat mode has an explicitly approved design
but cannot execute the official normalizer. A Source Handoff ZIP is a source
input for a later Work session. It is not a Canonical Handoff ZIP.

## Assistant A: prepare and transfer

Identify the approved specification version and explicit owner approval
evidence. Include the approved Design Statement, specification, workflow and
Instruction Module definitions, Reference Material evaluation and usage map,
invariants and HITL checkpoints, acceptance scenarios, rights and redistribution
decisions, unresolved owner decisions, and exclusions that the design requires.
Preserve each approved artifact's bytes. A historical DRAFT heading does not
override later explicit approval of the identified version, but a filename or
timestamp alone is not approval evidence.

For a full design, use the existing `COOL_DESIGN_ASSISTANT_FULL_V1` source
envelope with root `handoff_manifest.json`; for an update, use
`COOL_DESIGN_ASSISTANT_DELTA_V1` with root `delta_handoff_manifest.json`.
Use the exact supported fields documented by the [Workbench handoff
contract](workbench-handoff-contract.md) and the installed normalizer's
source-profile recognizer. The source manifest identifies `application`,
`spec_version`, `gate`, `approval_evidence`, `artifacts`, `requirements`,
`unresolved_owner_decisions`, `exclusions`, `reserved_workbench_decisions`, and
`readiness_note`. Each artifact records `id`, `file`, `version`, `state`,
`provenance`, `role`, and an array of exact requirement IDs. Each normative
requirement records exact `id`, `source`, and `verbatim`; a delta also records
`change` and the approved `baseline` and `baseline_preservation` contract.
Declare a member hash and size when available and calculate them from the
actual included bytes. Do not reconstruct requirements from headings or infer
rights and approval from possession of files. The ZIP contains one source
authority and its declared artifacts; keep continuation text outside the ZIP.

If file creation is available, create the ZIP and record its actual SHA-256.
If `preflight-source-handoff` can execute, run it on those exact bytes. A PASS
allows `SOURCE HANDOFF — PREFLIGHT PASS`, with the source digest and report;
canonical validation is still pending. If preflight cannot execute, transfer
the ZIP as `SOURCE HANDOFF — PREFLIGHT NOT VERIFIED`, state which capability
was unavailable, and include the following continuation request outside it.
If a known contract failure or blocking owner decision exists, report
`SOURCE HANDOFF BLOCKED` and explain the correction needed. If Chat cannot
create or attach a ZIP, provide the complete source files and packaging
checklist as incomplete transfer; never claim a ZIP or digest exists.

## Assistant B: Work continuation request

> Use the attached Source Handoff ZIP from Cool Plugin Design Assistant 1.0.3.
> Preserve the received ZIP and calculate its SHA-256. Find the installed
> `scripts/cool_plugin_design_assistant.py` launcher. Run
> `python -B scripts/cool_plugin_design_assistant.py preflight-source-handoff SOURCE.zip --json`.
> On BLOCKED, report exact diagnostics and obtain corrected source or owner
> decisions. On INCOMPLETE, restore the missing validation capability or
> evidence. Only on PASS, run
> `python -B scripts/cool_plugin_design_assistant.py normalize-handoff-package SOURCE.zip CANONICAL.zip --confirmed-by <recorded-owner> --json`.
> Verify that the output profile is `WORKBENCH_HANDOFF_V1_1`, the returned
> `output_archive_sha256` matches the final ZIP bytes, and full canonical validation
> passes when the final ZIP is reopened. Deliver that Canonical Handoff ZIP,
> source and output digests, source profile, and observed gate results. Do not
> infer new approval, rights, requirements, or implementation architecture.

The official normalization operation performs its own complete validation even
after preflight PASS. A preflight PASS only supports source contract readiness;
canonical validation and Workbench intake remain separate gates.
