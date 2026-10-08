# Plugin Builder Runtime Capability Realization v2 Design

**Status:** APPROVED
**Date:** 2026-10-07  
**Product:** Plugin Builder  
**Runtime scope:** `OPENAI_ONLY_PHASE_ONE`

**Approval evidence:** The decision owner approved this exact written
specification in the originating Codex conversation on 2026-10-07. The
approval authorizes implementation planning, not implementation, dependency
installation, hosted deployment, publication, or external release actions.

## 1. Purpose

Extend Plugin Builder's existing application-tool foundation so that every
capability requiring execution has a target-aware, evidence-bearing path from
an owning Skill to an exposed capability, a deterministic operation, and a
result returned to that Skill.

The current implementation already validates, plans, binds, packages, and
build-host-verifies `BUNDLED_LOCAL`, `FRAMEWORK_ADAPTER`, `RUNTIME_NATIVE`, and
`MCP_ADAPTER` tools. This design preserves those mechanisms. It closes the
remaining installed-runtime gap without treating successful local execution,
configuration files, or manifest bindings as proof that ChatGPT or Codex can
invoke the operation after installation.

Success means Plugin Builder:

1. identifies every application capability before W1;
2. distinguishes operation implementation from target-runtime exposure;
3. blocks infeasible required paths at W1 rather than during candidate build;
4. represents dependencies, permissions, setup, and fallbacks as validated
   contracts;
5. can materialize an approved MCP-backed realization and test it locally;
6. reports installed execution as `RUNTIME VERIFIED` only when a digest-bound
   record proves the complete Skill-to-result path; and
7. preserves current deterministic build, approval, integrity, and
   fail-closed guarantees.

## 2. Approved intent and constraints

The decision owner approved the recommended sequence leading to this written
design. That approval permits specification work; it does not yet authorize
implementation, dependency installation, hosted-service deployment,
publication, or external release actions.

The implementation must preserve:

- the `OPENAI_ONLY_PHASE_ONE` scope: Codex and ChatGPT Work Local/Desktop;
- exact canonical requirement identity and source bytes;
- strict SHA-256 verification;
- W1 as the only approval permitting candidate mutation;
- W2 as the only approval permitting final packaging;
- deterministic archive output for identical approved inputs;
- baseline preservation and unexplained-member protection for updates;
- direct argument vectors, clean environments, bounded execution, and no
  shell interpolation for local operations;
- credential exclusion and deny-by-default network behavior;
- `EXPECTED`, `STATICALLY VERIFIED`, `RUNTIME VERIFIED`, `NOT VERIFIED`, and
  `NOT APPLICABLE` as evidence states; and
- `PASS`, `FAIL`, `NOT VERIFIED`, and `NOT APPLICABLE` as test-result states.

The implementation must not weaken validation to obtain a passing test, infer
owner approval, synthesize runtime evidence, contact an MCP service without
authorization, install dependencies implicitly, deploy infrastructure,
publish a plugin, or expand phase one to OpenClaw or Claude.

## 3. Current foundation and precise gap

Plugin Builder currently supplies four useful layers:

1. **Operation ownership:** application-tool v1 classifies an operation as
   bundled local, framework adapter, runtime native, MCP adapter, or unresolved.
2. **Safe local execution:** bundled and framework operations use approved
   direct argv, clean environments, timeouts, fixtures, and output comparison.
3. **Candidate binding:** generated manifests retain tool-to-Skill,
   requirement, permission, dependency, and runtime-target bindings.
4. **Honest evidence:** absent runtime-native capabilities and MCP services stay
   `NOT VERIFIED` rather than receiving a fabricated pass.

What is missing is a runtime-consumed exposure contract. A Skill can mention a
tool and the candidate manifest can describe it, while no installed client is
proved to expose that tool or return its result to the Skill. Existing local
verification proves the operation on the build host. It does not prove this:

```text
Installed Skill invocation
        -> runtime-exposed capability
        -> deterministic operation
        -> structured result
        -> result delivered to the Skill
        -> Skill uses the result correctly
```

This design calls that complete chain **runtime realization**.

## 4. Alternatives considered

### 4.1 Chosen: orthogonal runtime-realization layer

Retain each tool's implementation kind and add one explicit realization record
per target runtime. This separates where an operation comes from from how a
runtime exposes it. A bundled deterministic operation may, for example, be
tested directly on the build host and separately exposed through an MCP
adapter. This approach reuses the current engine and makes unsupported paths
visible without multiplying tool kinds.

### 4.2 Rejected: add a new tool kind for every runtime mechanism

Kinds such as `CODEX_LOCAL_MCP`, `CHATGPT_REMOTE_MCP`, and
`CODEX_NATIVE_FILE_PICKER` would combine operation ownership, transport, and
runtime support. The combinations would proliferate, obscure shared
operations, and make compatibility changes rewrite W1 identities unnecessarily.

### 4.3 Rejected: force every application tool through MCP

Some capabilities are fully realized by Skill reasoning or existing runtime
capabilities. Some bundled operations need local verification but not a live
service. Mandatory MCP would add deployment, authentication, and operational
burden without improving those cases.

### 4.4 Rejected: documentation-only correction

Changing wording to say that runtime execution is unverified would preserve
honesty but would not prevent infeasible W1 plans or establish a callable
runtime path.

## 5. Conceptual architecture

```text
Approved requirements
        |
        v
Capability register
        |
        +--> SKILL_ONLY ------------------------------+
        |                                             |
        `--> TOOL_REQUIRED                            |
                 |                                    |
                 v                                    |
        Application-tool v2 operation                 |
                 |                                    |
                 v                                    |
        Per-target realization records                |
          |          |             |                  |
          |          |             +--> Unsupported --+--> W1 decision
          |          +--> Runtime-native adapter      |
          +--> MCP exposure adapter                   |
                 |                                    |
                 v                                    |
        Deterministic operation and structured result |
                 +------------------------------------+
                                      |
                                      v
                          Owning Skill behavior
```

Three boundaries remain independent:

- **operation implementation** — the existing application-tool kind;
- **runtime exposure** — the target-specific realization mechanism; and
- **evidence** — what was directly observed in a named environment.

No boundary may infer the state of another.

## 6. Capability register

Plan proposal v2 adds a canonical, sorted `capabilities` array. Each record has
exactly these semantic fields:

| Field | Meaning |
| --- | --- |
| `schema` | `plugin-builder-capability-v1` |
| `id` | Stable lowercase hyphenated capability ID |
| `requirement_ids` | Exact approved requirements needing the capability |
| `skill_bindings` | Skills responsible for deciding when to use it |
| `realization_need` | `SKILL_ONLY` or `TOOL_REQUIRED` |
| `tool_id` | Required for `TOOL_REQUIRED`; otherwise `null` |
| `runtime_targets` | Declared phase-one targets |
| `evidence_targets` | Required structural, operation, and behavioral evidence |

Every approved requirement must be covered by at least one capability or an
existing non-capability implementation decision. A capability cannot silently
change requirement text, combine IDs, or drop a target runtime.

`SKILL_ONLY` means that the approved behavior needs no application-specific
executable operation. It does not mean the behavior is runtime verified.
Behavioral evidence remains separate.

## 7. Application-tool v2 contract

New plans use `plugin-builder-application-tool-v2`. The v2 contract retains
the existing identity, implementation kind, schemas, side effects, files,
fixtures, redistribution evidence, and Skill/requirement bindings. It adds or
strengthens the following fields:

### 7.1 Operation identity

`operation` identifies the deterministic application-facing operation:

- stable `id`;
- input and output schema identities;
- invocation protocol, such as `JSON_STDIN_STDOUT` or `MCP_TOOL_CALL`;
- side-effect classification;
- idempotency declaration; and
- owning capability IDs.

Plugin Builder may generate wrappers, manifests, and adapters. It must not
invent application-domain semantics absent from the approved design or W1
proposal.

### 7.2 Structured dependencies

Each dependency record identifies:

- dependency ID and type;
- provider: `BUNDLED`, `RUNTIME_PROVIDED`, `OWNER_CONFIGURED`, or
  `REMOTE_SERVICE`;
- exact version or immutable identity when applicable;
- target runtimes;
- setup responsibility;
- integrity evidence when distributed; and
- whether absence blocks the operation or activates an approved fallback.

A plain package name or prose setup note is insufficient for a required
dependency.

### 7.3 Structured permissions

Each permission record identifies:

- an allowlisted permission ID;
- target runtime;
- grant source: runtime, owner, or service;
- required or optional status;
- purpose; and
- verification method.

Declaring a permission does not prove it was granted. Credentials and secret
values remain forbidden in plans and artifacts.

### 7.4 Executable fallback

The fallback record has one of these policies:

- `BLOCK` — no approved alternative exists;
- `ALTERNATIVE` — invoke a named alternative operation;
- `OMIT_OPTIONAL` — omit an optional capability without claiming its behavior.

An alternative names its trigger conditions, alternative operation ID,
preserved requirement IDs, degraded or excluded requirement IDs, and evidence
policy. If any required behavior changes, the session returns for design-owner
approval rather than treating the fallback as a W1-only adjustment.

### 7.5 Per-target realizations

Every tool contains one realization record for each declared runtime target.
The record includes:

- `target_runtime`;
- `mechanism`: `DIRECT_LOCAL`, `RUNTIME_NATIVE`, `MCP_REGISTERED`,
  `MCP_REMOTE_HTTPS`, `MCP_LOCAL_PROCESS`, or `UNSUPPORTED`;
- `adapter_id` and adapter contract version;
- runtime-exposed capability name;
- deterministic operation ID;
- transport and execution location;
- dependency and permission IDs;
- setup requirements and responsible owner;
- `feasibility_state`; and
- evidence policy.

Allowed feasibility states are:

- `FEASIBLE` — the adapter and prerequisites are established for planning;
- `FEASIBLE_WITH_SETUP` — a supported path exists and exact setup ownership is
  declared, but setup or installed evidence remains outstanding;
- `NOT VERIFIED` — the proposed path has not established feasibility;
- `UNSUPPORTED` — the named runtime does not support the mechanism under the
  declared installation channel; and
- `BLOCKED` — a required decision, dependency, permission, or authority is
  missing.

Feasibility is a planning claim, not runtime evidence. `FEASIBLE` never means
`RUNTIME VERIFIED`.

## 8. Adapter registry and first supported path

Plugin Builder gains an application-owned adapter registry. An adapter entry
defines the exact target runtime, installation channel, transport,
configuration files, dependency rules, permission rules, and evidence layers
it supports. Unknown adapters and unknown adapter versions fail closed.

The first new exposure adapter is **MCP Streamable HTTP**. Its automated local
test closes the operation-to-MCP-result path; installed Skill-to-result closure
still requires the separate runtime evidence in Section 11:

- Plugin Builder can materialize W1-approved MCP server source or an approved
  application-operation wrapper without inventing domain behavior.
- It generates canonical root `mcp.json` and, where required for the selected
  local Codex installation profile, the compatible `.mcp.json` projection.
- It validates tool name, input schema, optional output schema, annotations,
  server identity, transport, and Skill routing.
- It can run a local loopback MCP server and a deterministic client test in an
  isolated disposable root when the declared SDK/runtime dependency is already
  available or separately approved for installation.
- A loopback or MCP Inspector pass proves local server behavior only. It does
  not prove installed ChatGPT or Codex invocation.
- `MCP_REMOTE_HTTPS` requires an explicit service URL contract, authorization
  decision, and network permission. Plugin Builder does not deploy the service.
- `MCP_LOCAL_PROCESS` remains target-specific and may be `FEASIBLE` only when
  the named installed runtime and distribution channel document and prove that
  launch path. It cannot be inferred from a local test server.
- `DIRECT_LOCAL` likewise describes an installed realization only when the
  named target exposes an approved direct-operation bridge. Ordinary
  build-host direct-argv execution is verification evidence, not a target
  realization.

OpenAI's portable plugin contract supports root `mcp.json` and Streamable HTTP
MCP configuration. Public cross-runtime submission expects a reachable HTTPS
endpoint; locally running MCP servers therefore remain development evidence or
runtime-specific integrations unless separately supported. The governing
references are:

- <https://developers.openai.com/plugins/build/plugins>
- <https://developers.openai.com/plugins/concepts/mcp-server>
- <https://developers.openai.com/plugins/build/mcp-server>

No hosted MCP deployment, account credential, public tunnel, or external
service operation is authorized by this design.

## 9. W1 feasibility gate

Capability and realization validation occurs during plan compilation, before
the plan hash is presented for W1 approval.

For every required capability and required target runtime:

- `FEASIBLE` may reach W1;
- `FEASIBLE_WITH_SETUP` may reach W1 only when setup steps, owner,
  permissions, dependencies, fallback, and expected evidence are complete and
  visible in the W1 review;
- `NOT VERIFIED`, `UNSUPPORTED`, or `BLOCKED` prevents W1 unless an approved,
  behavior-preserving alternative realization is `FEASIBLE` or
  `FEASIBLE_WITH_SETUP` for that target.

For an optional capability, W1 may proceed with `OMIT_OPTIONAL` or an approved
alternative, but the omitted capability remains visible and cannot receive a
passing behavior claim.

The W1 review summarizes, per capability and target:

- implementation kind and operation ID;
- realization mechanism and feasibility;
- setup, dependency, permission, and authentication decisions;
- fallback and any degradation;
- planned evidence; and
- exact blockers.

Candidate build revalidates the W1-bound realization records but is no longer
the first place a predictable runtime-native or MCP feasibility problem is
reported.

## 10. Candidate and packaging behavior

Candidate manifest v3 retains the exact W1 hashes for:

- capability register;
- application-tool contracts;
- per-target realization records;
- adapter registry version;
- generated runtime configuration;
- dependency and permission records; and
- preflight evidence.

Generated runtime configuration must be derived deterministically from the
approved records. Any change to a tool, realization, dependency, permission,
fallback, generated MCP declaration, or Skill route changes the plan identity
and requires renewed W1 approval.

Packaging validates that:

- every declared MCP or runtime component is present and safe;
- no undeclared server, executable, credential, absolute path, or network
  endpoint entered the candidate;
- root portable and compatibility manifests agree;
- Skill references name the exact runtime-exposed capability;
- all bindings close over valid requirements and capabilities; and
- the packaged content matches the candidate and verification hashes.

## 11. Runtime evidence v3

`plugin-builder-runtime-result-v3` retains artifact, runtime, scenario, and
overall state information. Each tool realization result additionally records:

- installed plugin identity, version, ZIP SHA-256, and member-manifest SHA-256;
- target runtime, version, OS, and installation channel;
- Skill ID and Skill invocation evidence digest;
- capability ID, tool ID, operation ID, adapter ID, and their contract hashes;
- runtime-exposed capability name and discovery evidence digest;
- sanitized input digest;
- execution state, network-contact flag, and permission observations;
- structured result digest;
- result-delivery-to-Skill evidence digest;
- final behavior assertion and evidence digest; and
- limitations without raw private content or credentials.

Evidence layers are independently classified:

1. structural validation;
2. installation;
3. Skill invocation;
4. capability discovery;
5. deterministic operation execution;
6. result delivery;
7. Skill behavioral use;
8. reference consultation; and
9. conversation behavior.

A tool realization is `RUNTIME VERIFIED` only when layers 1 through 7 are
directly observed for the exact installed artifact and all required digests
validate. A local direct-argv test or MCP client test may prove layer 5 in its
named environment; it cannot promote installation, Skill invocation, result
delivery, or Skill behavior.

Evidence v1 and v2 remain readable and bundleable for historical results. They
cannot satisfy the new v3 installed-realization claim.

## 12. Compatibility and migration

The change is additive for existing artifacts and fail-closed for new claims:

- Existing W1-approved application-tool v1 plans retain their exact hashes and
  may complete under the old contract with current honest evidence states.
- Plugin Builder never rewrites an approved v1 plan into v2 silently.
- A new or materially revised plan emitted after this feature activates uses
  plan proposal v2, the capability register, and application-tool v2.
- Migrating a pre-W1 v1 proposal produces a new deterministic proposal and
  plan hash for owner review.
- Migrating an already approved v1 plan requires an explicit new W1 approval.
- Existing runtime-result v1/v2 evidence stays historical; only v3 can close
  the installed runtime-realization gate.
- Generated plugins without executable capabilities remain valid skills-only
  packages and do not receive unnecessary MCP files.

## 13. Failure and recovery behavior

| Condition | Required behavior |
| --- | --- |
| Required realization unsupported | Block before W1 and name target, capability, and missing path |
| Supported path requires setup | Surface exact setup and owner at W1; retain `NOT VERIFIED` until observed |
| Permission or dependency unresolved | Block the affected required path; do not guess or install |
| Optional capability unavailable | Apply only an approved `OMIT_OPTIONAL` or alternative fallback |
| MCP server unreachable | Record `NOT VERIFIED` or `FAIL` according to whether execution was attempted; do not retry with undeclared network access |
| Local MCP test passes | Record local operation evidence only |
| Installed tool executes but result is not returned to the Skill | Operation layer may pass; realization remains `NOT VERIFIED` or `FAIL` according to the scenario contract |
| Evidence digest missing or mismatched | Reject the runtime result and emit no upgraded claim |
| Runtime configuration changes after W1 | Invalidate W1 and all downstream artifacts |
| Required runtime test fails | Block W2/package under the approved verification policy |

Every diagnostic identifies the capability ID, tool ID, target runtime,
adapter, affected requirement IDs, and allowed recovery transition.

## 14. Testing strategy

Implementation is test-first and follows the repository's canonical Windows
test discipline: genuine system temp storage, isolated disposable roots,
UTF-8 Python subprocesses, one-time capability probes, and failure
classification before production-code changes.

Required automated coverage includes:

- capability-register closure and exact requirement identity;
- v2 tool contract validation and deterministic canonical bytes;
- one realization per declared target and no undeclared targets;
- required `NOT VERIFIED`, `UNSUPPORTED`, and `BLOCKED` paths rejected before
  W1;
- `FEASIBLE_WITH_SETUP` W1 summaries containing exact owner and prerequisites;
- optional omission and behavior-preserving alternative fallbacks;
- dependency and permission closure;
- no credentials, shell commands, unsafe paths, or undeclared network access;
- deterministic MCP manifest generation and root/compatibility agreement;
- local MCP tool discovery, valid and invalid calls, structured result, and
  deterministic operation output when its declared dependency is available;
- build-host success not upgrading installed-runtime evidence;
- fabricated, incomplete, stale, cross-artifact, and digest-mismatched runtime
  evidence rejected;
- complete installed Skill-to-result evidence accepted;
- legacy v1 plans and runtime-result v1/v2 remain readable without gaining v3
  claims;
- create and update preservation; and
- repeated candidate and ZIP builds remain byte-identical.

The installed-runtime kit adds one representative executable-capability
scenario to both Codex and ChatGPT Work Local/Desktop. It records discovery,
Skill invocation, capability invocation, deterministic operation, result
delivery, and final behavior independently. If the development task cannot
run either installed environment, it emits the deterministic kit and retains
`CONVERSION COMPLETE — RUNTIME VALIDATION PENDING` until owner-returned evidence
passes validation.

## 15. Verification and release gates

Before implementation can be reported complete, run:

1. focused capability, tool-contract, W1, adapter, evidence, and migration
   tests;
2. the complete Plugin Builder product suite;
3. relevant generic framework tests;
4. configured repository verification;
5. official plugin and Skill structural validators;
6. deterministic two-build comparisons;
7. extracted generated-artifact tests, not source-only tests;
8. installed Codex and ChatGPT scenarios when callable, otherwise retain their
   exact `NOT VERIFIED` states; and
9. `git diff --check` with tracked files unchanged by tests.

Release claims follow observed evidence:

- Contract, W1, packaging, and local adapter tests can be complete while
  installed execution remains pending.
- A realization type may be advertised as installed-runtime capable only for
  the target runtime and installation channel directly proven.
- Public or portable MCP support requires the separately deployed reachable
  HTTPS service and its authorization evidence.
- No `READY` claim is allowed while a required installed-runtime or behavior
  gate remains unverified.

## 16. Documentation changes

Implementation updates the four Plugin Builder Skills and their references so
that:

- the session Skill routes capability decisions and surfaces one blocking
  question at a time;
- the planning Skill compiles the capability register and W1 realization
  matrix;
- the build Skill materializes only W1-approved adapters and configuration;
- the verification Skill distinguishes operation, exposure, delivery, and
  behavior evidence; and
- runtime compatibility, coverage, application invariants, and the runtime kit
  use the new terminology consistently.

Documentation must use **local MCP execution** only for a server or operation
actually run in the named local test environment. It must use **installed MCP
realization** only for the complete installed Skill-to-result path.

## 17. Explicit non-goals

This design does not authorize or require:

- a hosted MCP deployment platform;
- automatic service deployment, tunneling, DNS, TLS, or secret management;
- arbitrary package installation during plugin generation;
- automatic launch of a local MCP process by every ChatGPT or Codex surface;
- a claim that ChatGPT Desktop supports bundled local process launch;
- replacement of existing local direct-argv verification;
- conversion of skills-only plugins into MCP plugins without need;
- OpenClaw or Claude runtime support;
- publication, marketplace mutation, tag creation, or external release; or
- reinterpretation of approved application behavior.

## 18. Acceptance criteria

The design is satisfied when all of the following are true:

1. New plans contain a deterministic capability register and tool v2 records.
2. Every required executable capability has a W1-visible realization for each
   required target or a valid approved fallback.
3. Predictably infeasible required paths fail before W1 approval.
4. Candidate manifests and packages bind exact realization, permission,
   dependency, adapter, and Skill identities.
5. One MCP Streamable HTTP realization can be generated and locally exercised
   without treating that local result as installed-runtime proof.
6. Runtime-result v3 rejects any `RUNTIME VERIFIED` tool claim lacking the
   complete installed Skill-to-result evidence chain.
7. Existing v1 plans and v1/v2 evidence remain readable without silent
   migration or upgraded claims.
8. Existing deterministic, approval, preservation, integrity, and security
   guarantees remain intact.
9. Full verification identifies every remaining installed-runtime limitation.
10. No dependency installation, hosted deployment, or publication occurs
    without separate owner authorization.
