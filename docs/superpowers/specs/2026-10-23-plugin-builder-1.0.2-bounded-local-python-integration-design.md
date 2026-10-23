# Plugin Builder 1.0.2 bounded local-Python integration design

Status: **proposed for owner review**. This document authorizes no implementation or publication by itself.

## Intent and boundary

Integrate two repairs proposed by `plugin-builder-local-python-repair-1.0.2-review.zip` into the current Workbench-owned Plugin Builder sources: (1) a conditional `direct-local` adapter v2 for OpenAI phase-one portable packages, and (2) safe resolution of explicit plugin-root `tools/` and `skills/` path bindings. The ZIP is review input, not an authority to apply its patch or replace repository files. Preserve the existing v1 adapter, approval gates, strict identity and hash checks, delegated-reference validation, newer MCP local-verification safeguards, and deterministic release process.

The review archive reports 17 local tests but also reports a failed release attempt (`manifest_pair_mismatch` on `skills`). Its snapshot is older than the current repository. Neither those tests nor its source files establish a releasable 1.0.2 artifact.

## Approaches

1. **Adopt the review patch or snapshot wholesale — rejected.** It would import stale MCP and validator code, omit current delegated-reference checks, and preserve the manifest mismatch.
2. **Leave 1.0.1 unchanged — rejected.** It leaves the two identified compatibility gaps unresolved.
3. **Port only the two behaviors into canonical sources — selected.** Use the review tests as examples, rewrite them against current contracts, regenerate vendored validation code through the existing release builder, and verify the resulting artifact.

## Repair A: conditional direct-local v2

- Add registry identity `direct-local` / `2` for `OPENAI_PORTABLE_PLUGIN` and the existing phase-one targets only. Keep `direct-local` / `1` test-only, with unchanged semantics and no silent upgrade of approved plans.
- Require `FEASIBLE_WITH_SETUP`, a nonblank `setup_owner`, nonempty concrete `setup_requirements`, and an explicit `evidence_policy` of `DEFERRED_ALLOWED` or `REQUIRED_BEFORE_W2`. Retain exact mechanism, transport, execution-location, target, dependency, and permission validation. Missing or contradictory fields fail closed.
- This is **conditional packaging support**, not proof that installed Codex or ChatGPT Work can execute a local Python tool. The W1 plan must surface setup, dependency, permission, invocation/result routing, fallback, and unverified runtime state. Build-host execution remains operation evidence only. `REQUIRED_BEFORE_W2` continues to block W2 until installed realization evidence exists; `DEFERRED_ALLOWED` may permit packaging while explicitly retaining `NOT VERIFIED` installed state.
- Do not introduce automatic Python installation, new MCP transports, credentials, network access, or expanded runtime targets.

## Repair B: plugin-root path bindings

- In canonical `src/obvious_one_plugin_framework/plugin_authoring/validation.py`, recognize only explicit `tools/...` and `skills/...` path tokens in `SKILL.md` as plugin-root-relative for **existence and containment validation**. Ordinary `references/...` and other local skill-owned paths remain skill-relative.
- Reject traversal, absolute or drive paths, backslashes, missing targets, and symlink/reparse escapes. Do not turn a textual path into authorization for a Skill to invoke a tool directly; the stable tool ID, declared contract, routing, and Skill ownership rules still apply. Existing reference-closure and delegated-reference validators remain independent gates.
- Do not edit the vendored validator as the source of truth. Regenerate it from the canonical framework source with the repository's materializer/release workflow and compare the generated copy.

## Version and release boundary

After both repairs pass focused tests, update Workbench-owned Plugin Builder version metadata consistently to `1.0.2`, including both manifests and the distribution contract. Keep `.codex-plugin/plugin.json` `skills` exactly `./skills/`. Update compatibility documentation to distinguish conditional adapter support, build-host verification, installed-runtime evidence, and release status. Generate, never hand-edit, release manifests and inventories. No marketplace mutation, Git push, tag, or public release is included.

## Test matrix

| Layer | Required cases | Expected evidence |
| --- | --- | --- |
| Registry/unit | v1 stays local-test-only; v2 accepts only the approved OpenAI targets and portable channel; unknown version, target, channel, mechanism, transport, and execution location fail | Focused adapter tests pass; stable registry digest is intentionally updated only for v2 |
| v2 setup policy | Missing/blank owner, empty/nonstring setup steps, wrong feasibility state or evidence policy fail; declared dependencies and permissions remain checked | Negative cases reject without fallback to v1 or inferred support |
| W1/W2 integration | v2 route compiles with explicit setup and fallback; W1 records exact plan hash; build-host tool execution cannot promote installed state; `REQUIRED_BEFORE_W2` blocks absent installed evidence; `DEFERRED_ALLOWED` preserves `NOT VERIFIED` | Focused planning, approval, verification, and evidence tests pass |
| Path validation | Existing plugin-root `tools/...` and `skills/...` resolve; missing roots, traversal, Windows paths, escaping symlinks/reparse points reject; skill-local references retain their old scope; undeclared direct tool invocation still fails its separate contract gate | Framework path-binding, reference-closure, and product portability tests pass |
| Non-regression | Current MCP timeout/listener/chunked-read tests and delegated-reference tests stay green; canonical and vendored validators agree after materialization | Focused MCP, framework, and packaging tests pass without copying stale snapshot files |
| Repository | Windows environment probe, product suite, framework suite, handoff interoperability, configured `verify_extraction.py --application plugin-builder`, `git diff --check` | Failures classified as implementation, fixture, environment, or transient before code changes; full suites run only after focused tests |
| Artifact | Two independent deterministic 1.0.2 builds; manifests and member hashes match; extracted ZIP validates; standalone create/update and applicable runtime-kit scenarios execute | Byte-identical builds and verified generated artifact, not merely source-tree tests |
| Installed runtime | In actual Codex and ChatGPT Work Local/Desktop, invoke a Skill through v2 to a declared local Python operation and observe result-to-Skill delivery | Only direct, digest-bound observations may become `RUNTIME VERIFIED`; until then report `NOT VERIFIED` and enforce W2 policy |

## Completion and non-goals

Implementation is complete only when the applicable repository suites and deterministic artifact checks pass and the final delta contains only intended behavior, tests, version metadata, and evidence documentation. Installed-runtime success is a separate evidence gate, not inferred from packaging or local execution. Rebuilding any downstream plugin (including Cool Sermon Coach) and marketplace publication are separate decisions.
