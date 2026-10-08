# Plugin Builder Runtime Capability Realization v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Plan status:** APPROVED — NATIVE/SEQUENTIAL EXECUTION

**Approval evidence:** The decision owner approved this implementation plan
and selected Native/sequential execution in the originating Codex conversation
on 2026-10-08. This authorizes scoped local implementation and verification;
dependency installation, hosted deployment, publication, and other external
release actions remain unauthorized.

**Goal:** Extend Plugin Builder's existing tool foundation with target-aware capability realization, pre-W1 feasibility enforcement, deterministic MCP Streamable HTTP exposure, and digest-closed installed Skill-to-result evidence without weakening existing approval, preservation, or build guarantees.

**Architecture:** Keep the existing implementation kinds as the operation-ownership layer and add a separate capability register plus per-runtime realization records. Planning validates these records and blocks infeasible required paths before W1; candidate creation deterministically projects approved adapter configuration; verification keeps build-host, local MCP, and installed-runtime evidence separate; runtime-result v3 alone can close the installed Skill-to-result path.

**Tech Stack:** Python 3.11+ standard library; repository `plugin_authoring` APIs; JSON Schema 2020-12; deterministic JSON and ZIP builders; `unittest`; PowerShell canonical Windows test runner; Markdown Skill contracts; OpenAI portable `plugin.json` and `mcp.json` formats.

**Spec:** `docs/superpowers/specs/2026-10-07-plugin-builder-runtime-capability-realization-v2-design.md`

## Global Constraints

- Runtime scope remains exactly `OPENAI_ONLY_PHASE_ONE`: Codex and ChatGPT Work Local/Desktop.
- Preserve exact canonical requirement IDs, source bindings, verbatim text, source bytes, and strict SHA-256 validation.
- Preserve W1 as the only approval permitting candidate mutation and W2 as the only approval permitting packaging.
- Preserve deterministic candidate and ZIP bytes for identical approved inputs.
- Preserve update baseline identity, unaffected members, and unexplained-member decisions.
- Preserve direct argv, `shell=False`, clean environments, fixed timeouts, safe paths, and deny-by-default network behavior.
- Keep credentials and secret values out of plans, candidates, evidence, logs, and test fixtures.
- Keep feasibility, test results, and evidence states separate; `FEASIBLE` is never `RUNTIME VERIFIED`.
- A local direct-argv or MCP client test never proves installed Skill invocation, result delivery, or conversational behavior.
- Existing W1-approved application-tool v1 plans retain exact hashes and are never silently rewritten.
- New or materially revised plans use proposal v2, capability v1, and application-tool v2.
- Runtime-result v1/v2 remain readable historical evidence but cannot close a v3 installed-realization gate.
- Do not install dependencies, start external tunnels, deploy MCP services, contact undeclared endpoints, push, tag, publish, mutate a marketplace, or perform external release actions.
- Preserve the unrelated untracked Vibe Coding Designer files.
- Run tests through `scripts/invoke_windows_test_environment.ps1`; use genuine system temp, disposable isolated roots, and UTF-8 subprocess settings.
- Classify failures as implementation, test/fixture, environment, or transient before modifying production code.

## Review Focus

- A required capability with one target marked `NOT VERIFIED`, `UNSUPPORTED`, or `BLOCKED` must fail before W1 unless a behavior-preserving approved alternative covers that exact target; Task 3 owns the tests.
- A build-host direct-argv pass or local loopback MCP pass must not upgrade installed-runtime invocation, result delivery, or Skill behavior; Tasks 5 and 7 own the tests.
- Legacy v1 plans and runtime-result v1/v2 must remain readable without changing hashes or acquiring v2/v3 claims; Tasks 3 and 7 own the tests.
- A target record that references an undeclared dependency, permission, adapter version, operation, capability, Skill, or requirement must fail deterministically and identify the exact broken binding; Tasks 1 and 2 own the tests.
- MCP configuration containing credentials, unsafe paths, undeclared endpoints, non-HTTPS remote URLs, or inconsistent root/compatibility projections must fail before candidate approval; Tasks 4 and 6 own the tests.

## Locked v2 Contract Shapes

Application-tool v2 keeps every v1 root key and adds exactly
`capability_ids`, `operation`, and `realizations`. The strengthened fields use
these exact shapes:

- `operation`: `id`, `protocol`, `input_schema_sha256`,
  `output_schema_sha256`, `side_effect_class`, `idempotent`, and
  `capability_ids`;
- dependency: `id`, `type`, `provider`, `version`, `sha256`,
  `runtime_targets`, `setup_owner`, `required`, and `absence_policy`;
- permission: `id`, `target_runtime`, `grant_source`, `required`, `purpose`,
  and `verification`;
- fallback: `policy`, `trigger_conditions`, `alternative_operation_id`,
  `preserved_requirement_ids`, and `degraded_requirement_ids`; and
- realization: `target_runtime`, `mechanism`, `adapter_id`,
  `adapter_version`, `exposed_capability`, `operation_id`, `transport`,
  `execution_location`, `dependency_ids`, `permission_ids`,
  `setup_requirements`, `setup_owner`, `feasibility_state`, and
  `evidence_policy`.

The exact enums are:

- operation protocol: `JSON_STDIN_STDOUT`, `MCP_TOOL_CALL`, or
  `RUNTIME_API`;
- side-effect class: `NONE`, `READ_ONLY`, `WORKSPACE_WRITE`, or
  `EXTERNAL_WRITE`;
- dependency type: `EXECUTABLE`, `PYTHON_PACKAGE`, `NODE_PACKAGE`,
  `RUNTIME_CAPABILITY`, or `SERVICE`;
- dependency provider: `BUNDLED`, `RUNTIME_PROVIDED`, `OWNER_CONFIGURED`, or
  `REMOTE_SERVICE`;
- setup owner: `BUILDER`, `OWNER`, `RUNTIME`, or `SERVICE_OPERATOR`;
- absence policy: `BLOCK` or `FALLBACK`;
- grant source: `RUNTIME`, `OWNER`, or `SERVICE`;
- fallback policy: `BLOCK`, `ALTERNATIVE`, or `OMIT_OPTIONAL`;
- evidence policy: `REQUIRED_BEFORE_W2` or `DEFERRED_ALLOWED`; and
- capability evidence targets: `STRUCTURE`, `OPERATION`,
  `INSTALLED_REALIZATION`, and `BEHAVIOR`.

Nullable `version`, `sha256`, and `alternative_operation_id` fields remain
present with JSON `null`; validators never accept shape changes based on kind.
Bundled dependencies require an immutable SHA-256. A fallback with policy
`ALTERNATIVE` requires an alternative operation; other policies require it to
be `null`.

---

### Task 1: Add capability and runtime-realization contract primitives

**Files:**
- Create: `src/obvious_one_plugin_framework/plugin_authoring/capabilities.py`
- Create: `src/obvious_one_plugin_framework/plugin_authoring/runtime_realization.py`
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/tools.py`
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/__init__.py`
- Create: `tests/framework/test_plugin_authoring_capabilities.py`
- Create: `tests/framework/test_plugin_authoring_runtime_realization.py`
- Modify: `tests/framework/test_plugin_authoring_tools.py`

**Interfaces:**
- Produces: `CapabilityContract`, `validate_capability_contract(payload: object) -> CapabilityContract`, and `validate_capability_register(payloads: object, *, requirement_ids: set[str], skill_names: set[str]) -> tuple[tuple[str, ...], tuple[str, ...]]`.
- Produces: `RuntimeRealizationContract`, `validate_runtime_realization(payload: object, *, operation_id: str, runtime_targets: set[str], dependency_ids: set[str], permission_ids: set[str]) -> RuntimeRealizationContract`.
- Extends: `validate_application_tool_contract(payload: object) -> ApplicationToolContract` to accept v1 unchanged and validate v2 through the new primitives.

- [ ] **Step 1: Write failing capability-register tests**

Add tests for exact keys, stable IDs, `SKILL_ONLY`/`TOOL_REQUIRED` rules, unknown requirements and Skills, duplicate IDs, missing tool IDs, target closure, and deterministic sorted diagnostics.

- [ ] **Step 2: Run the capability tests and verify RED**

```powershell
.\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument "-B","-m","unittest","tests.framework.test_plugin_authoring_capabilities","-v"
```

Expected: FAIL because the capability module does not exist.

- [ ] **Step 3: Implement the capability contract**

Implement the exact `plugin-builder-capability-v1` fields from the spec. Return immutable payload copies plus separate validation errors and planning blockers; never normalize requirement text or infer missing bindings.

- [ ] **Step 4: Write failing realization and application-tool v2 tests**

Cover all mechanism and feasibility enums, one record per target, adapter and operation identities, dependency/permission closure, structured fallbacks, credential rejection, unsafe URLs and paths, exact runtime coverage, and the unchanged v1 fixtures.

- [ ] **Step 5: Run the realization/tool tests and verify RED**

```powershell
.\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument "-B","-m","unittest","tests.framework.test_plugin_authoring_runtime_realization","tests.framework.test_plugin_authoring_tools","-v"
```

Expected: FAIL on missing v2 realization support while v1 tests continue passing.

- [ ] **Step 6: Implement realization and tool-v2 validation**

Keep `IMPLEMENTATION_KINDS` unchanged. Add exact structured operation, dependency, permission, fallback, and realization validation. A realization's `adapter_id`, version, operation, permissions, and dependencies must resolve within the same W1-bound contract.

- [ ] **Step 7: Run Task 1 tests and verify GREEN**

Run the three focused framework modules through the Windows runner. Expected: PASS with no repository-local temp artifacts.

- [ ] **Step 8: Commit Task 1**

```powershell
git add src/obvious_one_plugin_framework/plugin_authoring tests/framework/test_plugin_authoring_capabilities.py tests/framework/test_plugin_authoring_runtime_realization.py tests/framework/test_plugin_authoring_tools.py
git commit -m "feat: define runtime realization contracts"
```

---

### Task 2: Introduce the versioned adapter registry

**Files:**
- Create: `applications/plugin-builder/scripts/plugin_builder_core/runtime_adapters.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/bootstrap.py`
- Create: `applications/plugin-builder/tests/test_runtime_adapters.py`

**Interfaces:**
- Produces: `AdapterDefinition` and `adapter_registry() -> tuple[AdapterDefinition, ...]`.
- Produces: `adapter_registry_sha256() -> str` over canonical adapter records.
- Produces: `validate_realization_against_registry(realization: dict[str, Any], *, installation_channel: str) -> tuple[tuple[str, ...], tuple[str, ...]]`.
- Initial registered adapter: `mcp-streamable-http-v1`; existing runtime-native and direct-local mechanisms receive explicit conservative definitions rather than inferred support.

- [ ] **Step 1: Write failing registry tests**

Require stable canonical order and digest, exact runtime/channel/mechanism support, rejection of unknown adapter IDs or versions, HTTPS-only remote endpoints, and fail-closed `MCP_LOCAL_PROCESS`/`DIRECT_LOCAL` target support unless the selected channel definition permits it.

- [ ] **Step 2: Run the registry tests and verify RED**

```powershell
.\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument "-B","-m","unittest","applications.plugin-builder.tests.test_runtime_adapters","-v"
```

Expected: ERROR because `runtime_adapters.py` does not exist.

- [ ] **Step 3: Implement the immutable registry**

Use data-only definitions with no environment probing at import time. Register MCP Streamable HTTP for remote HTTPS packaging and local test-harness verification as separate channels. Keep installed local-process support unsupported until a named channel is explicitly added and proven.

- [ ] **Step 4: Run Task 2 tests and verify GREEN**

Expected: PASS, including unknown-version and channel-confusion cases.

- [ ] **Step 5: Commit Task 2**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/runtime_adapters.py applications/plugin-builder/scripts/plugin_builder_core/bootstrap.py applications/plugin-builder/tests/test_runtime_adapters.py
git commit -m "feat: add target-aware runtime adapter registry"
```

---

### Task 3: Compile capability realization and block infeasible paths before W1

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/tool_contract.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/approvals.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/session_contract.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder.py`
- Modify: `applications/plugin-builder/tests/test_planning_workflow.py`
- Modify: `applications/plugin-builder/tests/test_tool_contracts.py`
- Create: `applications/plugin-builder/tests/test_runtime_feasibility.py`
- Modify: `applications/plugin-builder/tests/fixtures/plan-create.json`
- Create: `applications/plugin-builder/tests/fixtures/plan-create-v1-legacy.json`

**Interfaces:**
- New plans consume `plugin-builder-plan-proposal-v2` with `capabilities` and application-tool v2 records.
- `PlanOutcome` adds `capabilities_sha256`, `realizations_sha256`, and `adapter_registry_sha256`.
- W1 summaries return a sorted `capability_summary` with per-target feasibility, setup owner, dependencies, permissions, fallback, evidence policy, and blockers.
- Existing W1-approved proposal/plan v1 sessions keep their exact completion
  path. A new `plan` invocation with proposal v1 returns
  `BLOCKED`/`plan.proposal_v2_required` and does not mutate session plan or
  approval identity.

- [ ] **Step 1: Add failing proposal-v2 closure tests**

Test exact requirement/Skill/tool/capability bindings, stable hashes, duplicate and missing target records, and byte-identical repeated plans.

- [ ] **Step 2: Add failing W1 feasibility tests**

Add cases for required `NOT VERIFIED`, `UNSUPPORTED`, and `BLOCKED`; `FEASIBLE_WITH_SETUP` with complete and incomplete setup ownership; optional `OMIT_OPTIONAL`; valid `ALTERNATIVE`; alternative behavior degradation requiring a design decision; and one feasible record per required target.

- [ ] **Step 3: Add failing legacy compatibility tests**

Prove that an approved v1 plan's bytes and hashes do not change, a new `plan`
invocation rejects proposal v1 without mutation, migration is never implicit,
and a revised proposal must produce a new v2 plan requiring a new W1 approval.

- [ ] **Step 4: Run focused planning tests and verify RED**

```powershell
.\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument "-B","-m","unittest","applications.plugin-builder.tests.test_planning_workflow","applications.plugin-builder.tests.test_tool_contracts","applications.plugin-builder.tests.test_runtime_feasibility","-v"
```

Expected: FAIL because v2 identities and pre-W1 realization blockers are absent.

- [ ] **Step 5: Implement proposal-v2 compilation and W1 validation**

Validate the capability register before tools, tools before realizations, and realizations against the registry. Canonically sort records before hashing. Store all three new hashes in the session and W1 evidence while retaining the v1 shape for untouched legacy sessions.

Migrate the active create fixture to proposal/tool v2 and preserve its former
bytes as `plan-create-v1-legacy.json` for compatibility tests. Update existing
planning assertions to expect v2; do not rewrite any persisted user session.

- [ ] **Step 6: Expose feasibility in CLI results without changing exit semantics**

`plan` returns `BLOCKED`/exit 2 for feasibility blockers and `FAIL`/exit 3 for malformed contracts. `approve-w1` revalidates exact bytes and refuses stale registry, capability, tool, or realization identities.

- [ ] **Step 7: Run Task 3 tests and verify GREEN**

Expected: PASS; no candidate directory is created by any blocked W1 case.

- [ ] **Step 8: Commit Task 3**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/tool_contract.py applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py applications/plugin-builder/scripts/plugin_builder_core/approvals.py applications/plugin-builder/scripts/plugin_builder_core/session_contract.py applications/plugin-builder/scripts/plugin_builder.py applications/plugin-builder/tests/test_planning_workflow.py applications/plugin-builder/tests/test_tool_contracts.py applications/plugin-builder/tests/test_runtime_feasibility.py applications/plugin-builder/tests/fixtures/plan-create.json applications/plugin-builder/tests/fixtures/plan-create-v1-legacy.json
git commit -m "feat: gate runtime feasibility before W1"
```

---

### Task 4: Generate deterministic MCP Streamable HTTP configuration

**Files:**
- Create: `applications/plugin-builder/scripts/plugin_builder_core/mcp_realization.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/manifest_profile.py`
- Create: `applications/plugin-builder/tests/test_mcp_realization.py`
- Modify: `applications/plugin-builder/tests/test_preflight_artifact_quality.py`

**Interfaces:**
- Produces: `project_mcp_configuration(plan: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]` for portable root `mcp.json` and optional Codex compatibility `.mcp.json`.
- Produces: `validate_mcp_projection(plan: dict[str, Any], tree: Path) -> tuple[str, ...]`.
- Consumes only W1-plan data: server ID, `streamable-http` transport, approved HTTPS URL for remote realization, tool names, and Skill routes.

- [ ] **Step 1: Write failing deterministic projection tests**

Cover skills-only omission, one and multiple MCP servers, stable ordering, root/compatibility equivalence, repeat-byte identity, and manifest-profile membership.

- [ ] **Step 2: Write failing safety tests**

Reject embedded credentials, URL user info, query-string secrets, non-HTTPS remote endpoints, loopback endpoints in a remote/public profile, unknown transports, duplicate server or tool names, undeclared generated members, and path escapes.

- [ ] **Step 3: Run MCP projection tests and verify RED**

```powershell
.\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument "-B","-m","unittest","applications.plugin-builder.tests.test_mcp_realization","applications.plugin-builder.tests.test_preflight_artifact_quality","-v"
```

Expected: ERROR or FAIL because no projection boundary exists.

- [ ] **Step 4: Implement canonical MCP projections**

Generate root `mcp.json` using the portable Agent Plugins schema. Generate `.mcp.json` only when the approved target profile requires the compatibility projection. Do not add an MCP file to a skills-only candidate and do not invent service URLs.

- [ ] **Step 5: Integrate projection into proposed-tree preflight**

Materialize generated MCP configuration before artifact-quality and manifest validation so predictable configuration defects fail before W1 hashing.

- [ ] **Step 6: Run Task 4 tests and verify GREEN**

Expected: PASS with deterministic bytes and no external network contact.

- [ ] **Step 7: Commit Task 4**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/mcp_realization.py applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py applications/plugin-builder/scripts/plugin_builder_core/manifest_profile.py applications/plugin-builder/tests/test_mcp_realization.py applications/plugin-builder/tests/test_preflight_artifact_quality.py
git commit -m "feat: project approved MCP runtime configuration"
```

---

### Task 5: Exercise approved MCP operations locally without upgrading runtime claims

**Files:**
- Create: `applications/plugin-builder/scripts/plugin_builder_core/mcp_local_verification.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/tool_verification.py`
- Create: `applications/plugin-builder/tests/fixtures/mcp_server_fixture.py`
- Create: `applications/plugin-builder/tests/test_mcp_local_verification.py`
- Modify: `applications/plugin-builder/tests/test_candidate_verification.py`

**Interfaces:**
- Produces: `verify_local_mcp_realization(tool: dict[str, Any], candidate: Path, *, allow_loopback: bool = False) -> dict[str, Any]`.
- The verifier starts only a W1-approved direct-argv server from the candidate, uses a dynamically assigned loopback port in an isolated temp root, performs MCP initialize/tool-discovery/tool-call checks, validates the structured result, terminates the process, and returns digest-only evidence.
- Local verification result includes `environment = "BUILD_HOST_LOCAL_MCP"` and can satisfy operation execution only; it cannot emit installed-runtime `RUNTIME VERIFIED`.

- [ ] **Step 1: Write failing lifecycle and protocol tests**

Cover initialization, advertised tool identity, valid call, invalid input, structured output, deterministic operation result, startup failure, timeout, premature exit, malformed response, wrong tool, and process cleanup.

- [ ] **Step 2: Write failing authorization and evidence-boundary tests**

Require `allow_loopback=True`, prohibit external hosts, reject undeclared argv and dependencies, verify clean environment/UTF-8, and assert that a passing local MCP call leaves installed invocation, delivery, and Skill behavior `NOT VERIFIED`.

- [ ] **Step 3: Run local MCP tests and verify RED**

```powershell
.\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument "-B","-m","unittest","applications.plugin-builder.tests.test_mcp_local_verification","applications.plugin-builder.tests.test_candidate_verification","-v"
```

Expected: FAIL because local MCP execution is not implemented.

- [ ] **Step 4: Implement the bounded local verifier**

Use the standard library for process, HTTP, JSON, timeout, and digest handling. The test fixture represents protocol behavior only; production MCP server source must still come from approved plan files and declare its real SDK/runtime dependency.

- [ ] **Step 5: Integrate operation-level MCP verification**

Extend `verify_application_tool` to return separate operation and realization evidence. Preserve existing bundled/framework behavior and current runtime-native/MCP `NOT VERIFIED` behavior when local verification is absent or unauthorized.

- [ ] **Step 6: Run Task 5 tests and verify GREEN**

Expected: PASS; all fixture processes terminate and no listener survives the test.

- [ ] **Step 7: Commit Task 5**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/mcp_local_verification.py applications/plugin-builder/scripts/plugin_builder_core/tool_verification.py applications/plugin-builder/tests/fixtures/mcp_server_fixture.py applications/plugin-builder/tests/test_mcp_local_verification.py applications/plugin-builder/tests/test_candidate_verification.py
git commit -m "feat: verify approved MCP operations locally"
```

---

### Task 6: Bind realization identities through candidate, update, verification, and packaging

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/candidate.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/verification.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/approvals.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/packaging.py`
- Modify: `applications/plugin-builder/tests/test_create_candidate.py`
- Modify: `applications/plugin-builder/tests/test_update_candidate.py`
- Modify: `applications/plugin-builder/tests/test_candidate_verification.py`
- Modify: `applications/plugin-builder/tests/test_final_packaging.py`

**Interfaces:**
- New proposal-v2 candidates use `plugin-builder-candidate-manifest-v3`.
- Manifest v3 binds capability, tool, realization, adapter-registry, generated MCP, dependency, permission, and preflight hashes.
- Verification reports distinguish `operation_execution` from per-target `runtime_realization`.
- W2 follows each realization's approved `REQUIRED_BEFORE_W2` or
  `DEFERRED_ALLOWED` evidence policy.

- [ ] **Step 1: Write failing create/update identity tests**

Require every new hash and binding in manifest v3, deterministic member closure, unchanged v1 candidate behavior, update preservation of unaffected files and tools, and W1 invalidation after any realization/configuration change.

- [ ] **Step 2: Write failing verification and W2 policy tests**

Test required installed evidence, explicitly deferred installed evidence, failed operation execution, valid fallback activation, local MCP pass with installed layers still pending, stale registry hash, and cross-candidate evidence rejection.

- [ ] **Step 3: Write failing packaging closure tests**

Reject undeclared MCP files, changed endpoints, mismatched root/compatibility projections, credentials, missing Skill routes, and report/manifest/plan identity mismatch.

- [ ] **Step 4: Run candidate-to-package tests and verify RED**

Run the four modified modules through the Windows runner. Expected: FAIL on absent manifest-v3 and evidence-policy behavior.

- [ ] **Step 5: Implement manifest-v3 and downstream hash binding**

Share one canonical identity helper between create and update. Revalidate all W1 records at every boundary and never repair a candidate after W1.

- [ ] **Step 6: Implement split verification and W2 decisions**

An operation `PASS` can coexist with target realization `NOT VERIFIED`. W2 blocks only according to the exact approved evidence policy and required behavior; any permitted deferral remains visible in package metadata and readiness state.

- [ ] **Step 7: Run Task 6 tests and verify GREEN**

Expected: PASS, including repeated create/update/package byte comparisons.

- [ ] **Step 8: Commit Task 6**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/candidate.py applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py applications/plugin-builder/scripts/plugin_builder_core/verification.py applications/plugin-builder/scripts/plugin_builder_core/approvals.py applications/plugin-builder/scripts/plugin_builder_core/packaging.py applications/plugin-builder/tests/test_create_candidate.py applications/plugin-builder/tests/test_update_candidate.py applications/plugin-builder/tests/test_candidate_verification.py applications/plugin-builder/tests/test_final_packaging.py
git commit -m "feat: bind runtime realization through packaging"
```

---

### Task 7: Implement runtime-result v3 and digest-closed installed evidence

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/evidence.py`
- Create: `applications/plugin-builder/tests/runtime/runtime-result-v3-schema.json`
- Create: `applications/plugin-builder/tests/runtime/runtime-result-v3-template.json`
- Modify: `applications/plugin-builder/tests/test_runtime_evidence_contract.py`
- Modify: `applications/plugin-builder/tests/test_runtime_evidence_packaging.py`

**Interfaces:**
- Produces: `validate_runtime_result_v3(payload: object) -> tuple[str, ...]` and retains the existing public `validate_runtime_result(payload: object) -> tuple[str, ...]` dispatcher.
- Runtime-result v3 contains exact installed artifact/runtime/channel identity and per-realization layer digests for structure, installation, Skill invocation, capability discovery, operation execution, result delivery, and Skill behavior.
- `build_runtime_evidence_bundle(...)` remains deterministic and bundles v1, v2, or v3 only after validating the selected schema.
- Each v3 tool record keeps `tool_id`, `implementation_kind`,
  `contract_sha256`, `skill_bindings`, `operation_execution`, and
  `realizations`. Each realization record has exactly `target_runtime`,
  `installation_channel`, `skill_id`, `capability_id`, `operation_id`,
  `adapter_id`, `exposed_capability`, `input_sha256`, `output_sha256`,
  `executed`, `network_contacted`, `permissions_observed`, `layers`, `state`,
  `result`, and `limitations`.
- `layers` has exactly `structural_validation`, `installation`,
  `skill_invocation`, `capability_discovery`, `operation_execution`,
  `result_delivery`, and `skill_behavior`; each layer has `state` and nullable
  `evidence_sha256`, with a digest required for `RUNTIME VERIFIED`.

- [ ] **Step 1: Write failing v3 positive and negative tests**

Accept one complete exact-artifact installed chain. Reject missing layers, null or malformed digests, mismatched tool/capability/operation/adapter identities, duplicate records, stale artifact hashes, cross-runtime evidence, raw credentials/private payloads, inconsistent states/results, and `RUNTIME VERIFIED` derived only from local argv or MCP evidence.

- [ ] **Step 2: Write failing historical compatibility tests**

Prove unchanged v1/v2 validation and deterministic bundling, while neither schema can satisfy a v3 installed-realization request.

- [ ] **Step 3: Run runtime evidence tests and verify RED**

```powershell
.\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument "-B","-m","unittest","applications.plugin-builder.tests.test_runtime_evidence_contract","applications.plugin-builder.tests.test_runtime_evidence_packaging","-v"
```

Expected: FAIL because v3 is unsupported.

- [ ] **Step 4: Implement the v3 schema and validator**

Use exact-key validation, strict SHA-256 patterns, unique composite realization identities, and layer consistency. Require layers 1-7 for a realization-level `RUNTIME VERIFIED` claim.

- [ ] **Step 5: Extend deterministic evidence packaging**

Index every claimed evidence member by exact digest; reject missing, duplicate, extra, altered, or unindexed evidence. Do not include private raw tool input/output when a digest is sufficient.

- [ ] **Step 6: Run Task 7 tests and verify GREEN**

Expected: PASS for all three schema generations and byte-identical repeated v3 bundles.

- [ ] **Step 7: Commit Task 7**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/evidence.py applications/plugin-builder/tests/runtime/runtime-result-v3-schema.json applications/plugin-builder/tests/runtime/runtime-result-v3-template.json applications/plugin-builder/tests/test_runtime_evidence_contract.py applications/plugin-builder/tests/test_runtime_evidence_packaging.py
git commit -m "feat: require installed Skill-to-result evidence"
```

---

### Task 8: Update Skills, runtime kit, standalone artifact, and traceability

**Files:**
- Modify: `applications/plugin-builder/skills/guiding-plugin-builder-sessions/SKILL.md`
- Modify: `applications/plugin-builder/skills/planning-plugin-implementations/SKILL.md`
- Modify: `applications/plugin-builder/skills/planning-plugin-implementations/references/input-and-plan-contract.md`
- Modify: `applications/plugin-builder/skills/building-and-updating-plugins/SKILL.md`
- Modify: `applications/plugin-builder/skills/building-and-updating-plugins/references/application-tool-contract.md`
- Modify: `applications/plugin-builder/skills/verifying-and-packaging-plugins/SKILL.md`
- Modify: `applications/plugin-builder/skills/verifying-and-packaging-plugins/references/tool-evidence-contract.md`
- Modify: `applications/plugin-builder/tests/runtime/T1-T7-runtime-scenarios.md`
- Create: `applications/plugin-builder/tests/runtime/T8-runtime-realization-scenario.md`
- Modify: `applications/plugin-builder/tests/runtime/prepare-runtime-scenarios.py`
- Modify: `applications/plugin-builder/scripts/build_marketplace_release.py`
- Modify: `applications/plugin-builder/tests/test_skill_contracts.py`
- Modify: `applications/plugin-builder/tests/test_end_to_end_scenarios.py`
- Modify: `applications/plugin-builder/tests/test_standalone_artifact.py`
- Modify: `applications/plugin-builder/tests/test_marketplace_release.py`
- Modify: `applications/plugin-builder/docs/application-invariants.md`
- Modify: `applications/plugin-builder/docs/runtime-compatibility.md`
- Modify: `applications/plugin-builder/tests/coverage-matrix.md`
- Modify: `applications/plugin-builder/README.md`

**Interfaces:**
- Adds installed scenario `T8` in its own contract file for one approved
  executable capability while retaining the T1-T7 contract and filename.
- The generated runtime kit carries v2 proposal fixtures, v3 result/schema/template, exact artifact identities, and digest-addressed evidence instructions.
- The standalone artifact vendors the new contract, adapter, MCP projection, local verification, and evidence modules without repository imports.

- [ ] **Step 1: Write failing Skill-contract tests**

Require capability identification, W1 target matrix, one-question blockers, dependency/permission/fallback disclosure, no implicit MCP choice, build-time versus installed-runtime separation, and exact v3 evidence rules.

- [ ] **Step 2: Write failing T8 and standalone tests**

Generate a small non-sensitive deterministic operation, expose it through the local MCP test profile, preserve installed layers as `NOT VERIFIED`, package the v3 kit, and run create/update from the extracted standalone Plugin Builder artifact with repository paths removed.

- [ ] **Step 3: Run Skill, end-to-end, standalone, and release tests and verify RED**

Run the four affected product modules through the Windows runner. Expected: FAIL on missing guidance, fixtures, vendored modules, and T8 outputs.

- [ ] **Step 4: Update the four Skills and focused references**

Keep routing and non-negotiable gates in each `SKILL.md`; put detailed contract fields and examples in the existing references. Do not duplicate the full schemas in prose.

- [ ] **Step 5: Extend runtime-kit generation and standalone vendoring**

Generate T8 inputs and v3 templates deterministically. Include all new runtime modules and schema files in the built Plugin Builder artifact; reject repository imports and machine-specific paths.

- [ ] **Step 6: Update invariants, compatibility, coverage, and README**

Record local MCP operation evidence separately from installed Codex and ChatGPT evidence. Retain `CONDITIONALLY PORTABLE` and `CONVERSION COMPLETE — RUNTIME VALIDATION PENDING` until direct installed results exist.

- [ ] **Step 7: Run Task 8 tests and verify GREEN**

Expected: PASS, including extracted-artifact execution and deterministic release ZIP comparison.

- [ ] **Step 8: Commit Task 8**

```powershell
git add applications/plugin-builder/skills applications/plugin-builder/tests/runtime applications/plugin-builder/scripts/build_marketplace_release.py applications/plugin-builder/tests/test_skill_contracts.py applications/plugin-builder/tests/test_end_to_end_scenarios.py applications/plugin-builder/tests/test_standalone_artifact.py applications/plugin-builder/tests/test_marketplace_release.py applications/plugin-builder/docs/application-invariants.md applications/plugin-builder/docs/runtime-compatibility.md applications/plugin-builder/tests/coverage-matrix.md applications/plugin-builder/README.md
git commit -m "docs: route and test runtime realization workflows"
```

---

### Task 9: Complete verification and prepare installed-runtime evidence

**Files:**
- Modify if required by observed results: `applications/plugin-builder/tests/runtime/T1-T7-runtime-scenarios.md`
- Modify if required by observed results: `applications/plugin-builder/tests/runtime/T8-runtime-realization-scenario.md`
- Modify if directly observed: `applications/plugin-builder/docs/runtime-compatibility.md`
- Modify if directly observed: `applications/plugin-builder/tests/coverage-matrix.md`
- Generated only under ignored roots: `dist/plugin-builder/`

**Interfaces:**
- Consumes the exact reviewed Plugin Builder source and generated install artifact.
- Produces deterministic install ZIP, runtime kit, member manifest, SHA-256 report, and either validated installed runtime-result v3 evidence or explicit `NOT VERIFIED` rows.

- [ ] **Step 1: Run the focused regression set through the Windows runner**

Run framework capability/tool tests and all product planning, adapter, MCP, candidate, evidence, standalone, and marketplace-release modules. Expected: PASS with any environment-only failure corrected without changing product behavior, followed by rerunning only the affected set.

- [ ] **Step 2: Run complete framework and product suites**

```powershell
.\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument "-B","-m","unittest","discover","-s","tests/framework","-v"
.\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument "-B","-m","unittest","discover","-s","applications/plugin-builder/tests","-v"
```

Expected: PASS, with only documented platform skips and no tracked-file changes.

- [ ] **Step 3: Run repository and configured product verification**

```powershell
.\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument "-B","scripts/verify_extraction.py","--application","plugin-builder"
python -B -m unittest tests.test_application_config tests.test_agents_contract -v
git diff --check
```

Expected: PASS. Classify any failure before changing code.

- [ ] **Step 4: Build twice and compare exact release artifacts**

Use two separate disposable output roots with `build_marketplace_release.py`. Compare install ZIP SHA-256, release manifest bytes, member manifests, v3 runtime-kit bytes, extracted plugin validation, Skill validation, and absence of repository/private paths.

- [ ] **Step 5: Execute the installed Codex scenario when callable**

Install the exact generated artifact in a fresh task, run T1-T8, and return one schema-valid runtime-result v3 plus digest-addressed evidence. Do not infer installed execution from the standalone artifact or local MCP verifier.

- [ ] **Step 6: Execute the installed ChatGPT Work Local/Desktop scenario when callable**

Run the same exact-artifact T1-T8 contract. If the development task cannot invoke that surface, return the deterministic runtime kit to the decision owner and retain all unobserved layers as `NOT VERIFIED`.

- [ ] **Step 7: Reconcile evidence and compatibility classification**

Validate returned evidence before updating documentation. Advertise only the realization mechanism, runtime, and installation channel directly proven. Keep `CONVERSION COMPLETE — RUNTIME VALIDATION PENDING` if either required installed target is unverified.

- [ ] **Step 8: Request one fresh whole-branch review**

Use `superpowers:requesting-code-review` against the approved spec and this plan. Fix Critical and Important findings test-first; record genuine Minor findings without weakening validation.

- [ ] **Step 9: Run final fresh verification**

Repeat the smallest affected tests after review fixes, then both full suites, configured verification, deterministic build comparison, installed-evidence validation, and `git diff --check`.

- [ ] **Step 10: Commit directly observed evidence and final documentation**

```powershell
git add applications/plugin-builder/tests/runtime/T1-T7-runtime-scenarios.md applications/plugin-builder/tests/runtime/T8-runtime-realization-scenario.md applications/plugin-builder/docs/runtime-compatibility.md applications/plugin-builder/tests/coverage-matrix.md
git commit -m "test: record runtime realization evidence"
```

Commit only evidence directly observed. Generated ZIPs remain below ignored `dist` roots. Do not push, tag, publish, or mutate any marketplace.

---

## Plan Self-Review

- **Spec coverage:** Tasks 1-3 cover capability identification, tool v2, per-target realizations, dependencies, permissions, fallbacks, compatibility, and W1 feasibility. Tasks 4-6 cover deterministic MCP configuration, local operation execution, manifests, W2, and packaging. Task 7 covers installed evidence v3. Task 8 covers Skill behavior, standalone portability, T8, traceability, and documentation. Task 9 covers full verification and installed-runtime evidence.
- **Interface consistency:** Capability IDs bind requirements and Skills; tool v2 binds capability and operation IDs; realizations bind the same operation plus adapter/dependency/permission IDs; plan/W1 hashes bind every record; manifest v3 carries those hashes; verification and runtime-result v3 refer back to the same identities.
- **Compatibility:** Existing v1 plans and evidence remain byte-stable and readable. Only new or revised work enters v2/v3, and any migration changes the plan hash and requires W1 approval.
- **Evidence honesty:** Local direct argv and MCP results never close installed layers. Only runtime-result v3 with layers 1-7 for the exact installed artifact can claim a realized tool as `RUNTIME VERIFIED`.
- **Scope:** No dependency install, hosted service deployment, public tunnel, marketplace mutation, publication, OpenClaw expansion, or application-behavior reinterpretation is included.
- **Review-focus coverage:** W1 unsupported paths are Task 3; evidence-layer confusion is Tasks 5/7; legacy compatibility is Tasks 3/7; broken binding closure is Tasks 1/2; MCP safety and projection consistency are Tasks 4/6.
