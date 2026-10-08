# Plugin Builder installed-runtime scenarios T1–T7

This is the retained historical v2 replay contract. For the runtime-realization-v2 extension, use the separate `T8-runtime-realization-scenario.md` and v3 result/schema/template; do not merge the historical v2 result with a v3 installed claim.

Use this contract only with the generated Plugin Builder artifact. It records application evidence; it does not authorize publication, marketplace mutation, credentials, external messages, or network access.

## Clean-environment preconditions

- Start in a new empty workspace with no pre-existing generated outputs.
- Install or copy the reviewed artifact, then invoke its `scripts/plugin_builder.py`; do not invoke development-source files.
- Clear `PYTHONPATH` and `PYTHONHOME`, use a working directory outside the repository, and reject any repository or Workbench import.
- Start from `runtime-result-v2-template.json`. Record runtime/app version, operating system, artifact ZIP SHA-256, exact member-manifest SHA-256, and wrapped `PORTABLE_SINGLE_DIRECTORY` upload and discovery as separate observations.
- For every tool, preserve `declared_argv` exactly and record the actual `observed_argv` plus `adapter`; never rewrite a declaration to resemble the host command.
- Record `structural_validation`, `installation`, `tool_execution`, `reference_consultation`, and `conversation` independently. Upload or discovery evidence must not promote tool, reference, or conversation evidence.
- Do not place credentials, tokens, private paths, or source-package contents in the result. Network access is forbidden unless separately authorized for the named scenario.
- Preserve each outcome as `EXPECTED`, `STATICALLY VERIFIED`, `RUNTIME VERIFIED`, `NOT VERIFIED`, or `NOT APPLICABLE`; absence of a capability is never `PASS`.

The raw `sample-legacy-handoff-v1.1.zip`, its canonical `sample-normalized-handoff-v1.1.zip`, `create-plan.json`, exact T3/T5/T6 proposals, and `prepare-runtime-scenarios.py` accompany the runtime kit. Use the raw legacy ZIP for at least T1 or T2 to directly observe normalization. Replace `<plugin-builder>` and `<workspace>` with paths inside the clean test root. Every CLI invocation must emit exactly one JSON result document.

## T1 — behavior-only planning

Run `plugin_builder.py inspect <design.zip> --workspace <workspace>/t1 --operation create --json`, then `plan --session <workspace>/t1/session.json --proposal <create-plan.json> --json`. Expect stage `W1`, no candidate directory, and a plain-language review of requirements, skills, tools, permissions, and evidence. Do not run `approve-w1`.

## T2 — successful create and bundled tool

Repeat create inspection and planning, record explicit W1 with `approve-w1`, then run `build`, `verify`, explicit `approve-w2`, and `package`. The declared `BUNDLED_LOCAL` tool must execute through direct argv with digest-only stdout/stderr evidence. Expect a deterministic plugin ZIP whose exact members and extracted tree validate.

## T3 — missing or conflicting behavior

Use `t3-unresolved-plan.json`. Expect planning/W1 to block, identify the affected requirement, produce no candidate, and require a newly approved specification. Plugin Builder must not self-approve the change.

## T4 — update protection

After T2, run `python prepare-runtime-scenarios.py --base-plan create-plan.json --baseline <t2.zip> --output <scenario-inputs>`. Use the emitted `t4-update-baseline.zip` and `t4-update-plan.json` with `inspect ... --operation update --baseline <baseline.zip>`, `plan`, and `approve-w1`. Expect `build` to block until `resolve-update` records an explicit keep decision. Resume build/verify/W2/package and confirm preserved bytes, including unchanged application-tool files and skill bindings.

## T5 — required failure

Use `t5-failing-tool-plan.json`. After W1 and build, expect `verify` to block, `approve-w2` and `package` to remain unavailable, and no final ZIP to exist. Record the tool and owning requirements as failed without embedding process output.

## T6 — environment-limited tool evidence

Use `t6-runtime-native-plan.json`, whose tool kind is `RUNTIME_NATIVE`. Confirm it is planned, W1-approved, built, bound to its skill and requirements, and structurally reported. Without separately authorized capability, service, credentials, or network access, the tool remains `NOT VERIFIED` and is not contacted. An owner-supplied `MCP_ADAPTER` variant follows the same no-contact rule; it is not required for this exact T6 replay. Other required evidence may pass; W2 must show the limitation before explicit acceptance.

## T7 — standalone create/update

From the installed artifact copy, with the repository absent from environment variables and working directory, repeat the T2 create and T4 update flows. Confirm the bundled-local-tool execution, package both results, validate each extracted ZIP with Plugin Creator and Skill Creator, and compare declared members, bindings, dependencies, permissions, and distribution audit evidence.

## Result delivery

Return one `plugin-builder-runtime-result-v2` JSON document conforming to `runtime-result-schema.json`. Include all T1–T7 rows even when a scenario could not run. A `RUNTIME VERIFIED` reference-consultation or conversation claim requires a digest-addressed scenario evidence record. Store each scenario evidence file under its exact SHA-256 filename and run `plugin_builder.py package-runtime-evidence --result <result.json> --evidence-root <digest-files> --output <evidence.zip> --json`; do not manually construct the evidence ZIP. The command retains read-only validation and deterministic bundling of historical v1 results, rejects absent, duplicated, altered, or unindexed evidence, and embeds the result under its own digest.

Attach only that validated digest-addressed bundle; never include credentials. Keep network access prohibited unless a named scenario received separate authorization. A clean local-copy run does not prove Codex or ChatGPT Work installed discovery unless `discovery_observed` is true for that named runtime.
