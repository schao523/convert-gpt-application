# Input and plan contract

## Planning contract

| Key | Outcome |
| --- | --- |
| INPUT_AUTHORITY | APPROVED_SPEC_REQUIRED |
| OUTPUT | REQUIREMENT_COVERAGE_PLAN |
| BEHAVIOR_CHANGE | RETURN_FOR_NEW_APPROVAL |

## Pre-W1 preflight contract

| Key | Outcome |
| --- | --- |
| TREE | MATERIALIZE_PROPOSED_FINAL_TREE |
| ARTIFACT_ROLES | REQUIRE_SEMANTIC_ROLE_AND_KNOWLEDGE_OWNERSHIP |
| DUPLICATES | REPORT_GROUPS_BYTES_AND_APPROVED_RATIONALES |
| PATHS | REJECT_ESCAPES_IN_STRUCTURE_TEXT_AND_ARGV |
| COMMANDS | RESOLVE_DECLARED_AND_OBSERVED_WITH_EXPLICIT_ADAPTER |
| MANIFEST | APPLY_TARGET_AWARE_PROFILE |
| FAILURE | NO_W1_IDENTITY_OR_CANDIDATE_MUTATION |

Run `plan` only from a valid inspected session. Classify each application capability as bundled local, framework adapter, runtime native, MCP adapter, or unresolved; include permissions, configuration, fallback, files, bindings, fixtures, and evidence targets. Present these decisions at W1 and use `approve-w1` only after explicit owner confirmation.

Handoff normalization does not establish approval. Plan only when the canonical handoff records sufficient explicit approval evidence; a filename containing `APPROVED`, a generated sidecar, or a successful format conversion is not planning authority.

For `WORKBENCH_HANDOFF_V1_1`, retain every canonical requirement record with its exact `id`, `source`, and `verbatim` values; an update also retains its exact `change` value. Do not derive IDs from prose or rewrite source text. An update requires the supplied baseline ZIP to match the declared plugin ID, version, and archive SHA-256, plus the approved baseline-preservation contract, before planning can advance.

The plan identifies each behavioral requirement, application invariant, skill owner, reference need, deterministic operation, dependency, runtime adapter, acceptance scenario, and unresolved decision. An existing plugin ZIP is mandatory for update mode; store only its digest and a relative workspace identity.

Evaluate available framework and creator capabilities before proposing new code. Record one decision for each required capability: `REUSE`, `ADAPT`, `BUNDLE`, or `UNRESOLVED`, plus the inspected evidence. Do not replace required retrieval or deterministic processing with model memory.

The W1 review package is plain language: intended skill responsibilities, reused or bundled capabilities, planned files, requirement coverage, risks, and decisions still needed. W1 remains the only approval that permits candidate mutation. W2 remains the only approval that permits final packaging. Neither is permission to publish or deploy.

## Target-aware realization matrix

For each capability, record exact requirement IDs, owning Skill, `TOOL_REQUIRED` or `SKILL_ONLY`, deterministic operation, input/output schema hashes, and evidence targets. For each tool and target (`Codex`, `ChatGPT Work Local/Desktop`), record the mechanism, adapter, exposed capability, dependency and permission IDs, setup owner, fallback, feasibility, and evidence policy. A Skill route must name the exposed capability and specify how its structured result returns to the Skill.

`FEASIBLE_WITH_SETUP` requires explicit steps, setup owner, dependencies, permissions, and expected installed evidence. `NOT VERIFIED`, `UNSUPPORTED`, or `BLOCKED` stops W1 for a required path unless a behavior-preserving approved alternative is feasible. `OMIT_OPTIONAL` applies only to genuinely optional behavior. State one blocking owner question; do not select a new provider, MCP server, credential source, or degraded behavior on the owner's behalf.

`DEFERRED_ALLOWED` permits an installed-runtime evidence gap to remain visible after a passing approved local operation check. `REQUIRED_BEFORE_W2` blocks W2 until exact installed evidence is validated. Neither policy turns a build-time check into installed-runtime verification.
