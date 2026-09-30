# Plugin Builder installed-runtime scenarios T1–T7

Use this contract only with the generated Plugin Builder artifact. It records application evidence; it does not authorize publication, marketplace mutation, credentials, external messages, or network access.

## Clean-environment preconditions

- Start in a new empty workspace with no pre-existing generated outputs.
- Install or copy the reviewed artifact, then invoke its `scripts/plugin_builder.py`; do not invoke development-source files.
- Clear `PYTHONPATH` and `PYTHONHOME`, use a working directory outside the repository, and reject any repository or Workbench import.
- Record runtime/app version, operating system, artifact ZIP SHA-256, exact member-manifest SHA-256, and whether plugin discovery was directly observed.
- Do not place credentials, tokens, private paths, or source-package contents in the result. Network access is forbidden unless separately authorized for the named scenario.
- Preserve each outcome as `EXPECTED`, `STATICALLY VERIFIED`, `RUNTIME VERIFIED`, `NOT VERIFIED`, or `NOT APPLICABLE`; absence of a capability is never `PASS`.

The fixture package and plan accompany the runtime kit. Replace `<plugin-builder>` and `<workspace>` with paths inside the clean test root. Every CLI invocation must emit exactly one JSON result document.

## T1 — behavior-only planning

Run `plugin_builder.py inspect <design.zip> --workspace <workspace>/t1 --operation create --json`, then `plan --session <workspace>/t1/session.json --proposal <create-plan.json> --json`. Expect stage `W1`, no candidate directory, and a plain-language review of requirements, skills, tools, permissions, and evidence. Do not run `approve-w1`.

## T2 — successful create and bundled tool

Repeat create inspection and planning, record explicit W1 with `approve-w1`, then run `build`, `verify`, explicit `approve-w2`, and `package`. The declared `BUNDLED_LOCAL` tool must execute through direct argv with digest-only stdout/stderr evidence. Expect a deterministic plugin ZIP whose exact members and extracted tree validate.

## T3 — missing or conflicting behavior

Use a proposal with a required `UNRESOLVED` application tool or a conflict with approved behavior. Expect planning/W1 to block, identify the affected requirement, produce no candidate, and require a newly approved specification. Plugin Builder must not self-approve the change.

## T4 — update protection

Use the T2 ZIP as the explicit update baseline and add one unrelated baseline member. Run `inspect ... --operation update --baseline <baseline.zip>`, `plan`, and `approve-w1`. Expect `build` to block until `resolve-update` records an explicit keep decision. Resume build/verify/W2/package and confirm preserved bytes, including unchanged application-tool files and skill bindings.

## T5 — required failure

Use an approved plan whose required bundled tool exits nonzero. After W1 and build, expect `verify` to block, `approve-w2` and `package` to remain unavailable, and no final ZIP to exist. Record the tool and owning requirements as failed without embedding process output.

## T6 — environment-limited tool evidence

Use one optional `RUNTIME_NATIVE` or `MCP_ADAPTER` design. Confirm it is planned, W1-approved, built, bound to its skill and requirements, and structurally reported. Without separately authorized capability, service, credentials, or network access, the tool remains `NOT VERIFIED` and is not contacted. Other required evidence may pass; W2 must show the limitation before explicit acceptance.

## T7 — standalone create/update

From the installed artifact copy, with the repository absent from environment variables and working directory, repeat the T2 create and T4 update flows. Confirm the bundled-local-tool execution, package both results, validate each extracted ZIP with Plugin Creator and Skill Creator, and compare declared members, bindings, dependencies, permissions, and distribution audit evidence.

## Result delivery

Return one JSON document conforming to `runtime-result-schema.json`. Include all T1–T7 rows even when a scenario could not run. Attach only digest-addressed logs or artifacts; never include credentials. A clean local-copy run does not prove Codex or ChatGPT Work installed discovery unless `discovery_observed` is true for that named runtime.
