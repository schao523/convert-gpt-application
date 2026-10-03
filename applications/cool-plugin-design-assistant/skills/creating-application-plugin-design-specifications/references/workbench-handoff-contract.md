# Application Workbench handoff contract

Create a handoff only from an explicitly approved, identified specification
version. Record the approval evidence and preserve every blocking or nonblocking
unresolved owner decision.

## Required package

- approved Design Statement;
- approved Application Plugin Design Specification;
- workflow definitions and Instruction Module contracts;
- Reference Material inventory, evaluation, and behavior-level usage map;
- application invariants and HITL checkpoints;
- deterministic-operation candidates;
- tool, data, runtime, and service requirements;
- acceptance criteria and representative scenarios;
- rights and redistribution decisions; and
- unresolved owner decisions and explicit exclusions.

For every artifact, record identifier, version, state, provenance, and relation
to specification requirements. A rights decision that is required for intended
distribution remains a blocking owner decision until confirmed; do not replace
it with a technical workaround.

New full and delta packages use the `WORKBENCH_HANDOFF_V1_1` contract. A package
contains exactly one semantic authority; a canonical pair must not be combined
with `handoff_manifest.json`, `delta_handoff_manifest.json`, or another legacy
authority. Mixed authorities are ambiguous and remain blocked.

The portable package boundary has two distinct machine-readable documents:

- `package-manifest.json` inventories the package, artifact roles, immutable
  hashes, source-package hash, and normalization metadata; and
- `workbench-handoff.json` contains the canonical semantic payload consumed by
  the Workbench handoff validator.

Both create and update packages carry a non-empty canonical `requirements`
array. Every requirement record preserves the exact `id`, `source`, and `verbatim`
text supplied by the approved design. Artifact-level `requirements`
arrays index those exact IDs. Do not infer IDs from headings or filename
patterns, paraphrase approved text, or create a source binding that the package
does not supply. An update record also carries `change`, and the handoff binds
the approved baseline archive and preservation contract.

When an approved legacy package uses `handoff_manifest.json` or
`delta_handoff_manifest.json`, normalize it only when it already supplies exact
requirement records and, for updates, the baseline and preservation contract.
Preserve every approved artifact byte for byte, record the source archive hash,
validate the canonical payload before committing the derived archive, and never
overwrite the approved source or an existing output. Format-only normalization
does not grant new rights or reopen approved product behavior.

Represent each unresolved owner decision as an object with a stable
`decision_id`, concise `summary`, named `owner`, and boolean `blocking` value.
The handoff validator rejects malformed or blocking entries but preserves valid
nonblocking entries for Workbench.

## Reserved Workbench decisions

Application Workbench determines:

- required Skills and their responsibilities;
- Skill collaboration and routing;
- Reference Material technical mapping;
- deterministic tools and MCP integrations;
- runtime adapters and manifests;
- Application Implementation tests and packaging; and
- Codex and OpenClaw realization.

The handoff may state behavioral needs for deterministic operations, external
capabilities, retrieval exactness, portability, and runtime targets. It may not
select concrete Skills, folders, technical material bindings, tools, MCP
servers, storage, indexes, RAG, adapters, manifests, test frameworks, or
packaging on Workbench's behalf.

## Gate result

Report one state:

- `READY FOR WORKBENCH` — complete specification explicitly approved and no
  blocking owner decision prevents faithful, lawful implementation;
- `APPROVED WITH NONBLOCKING DECISIONS` — approved version plus clearly owned
  decisions that Workbench may carry without guessing; or
- `HANDOFF BLOCKED` — specification unapproved or a blocking scope, rights,
  safety, distribution, or authority decision remains.

Never use handoff readiness as evidence that implementation, runtime behavior,
testing, packaging, installation, or publication has occurred.
