# Runtime compatibility evidence

Phase-one runtime scope is `OPENAI_ONLY_PHASE_ONE`.

| Runtime | Evidence state | Environment identity |
| --- | --- | --- |
| Codex | RUNTIME VERIFIED | Primitive feasibility only; Codex Desktop local projectless task; codex-cli 0.146.0 |
| ChatGPT Work Local/Desktop | RUNTIME VERIFIED | Primitive feasibility only; user-confirmed native local execution; returned artifact independently inspected |
| Generated standalone Plugin Builder artifact | RUNTIME VERIFIED | Local clean-process T7 create/update execution with repository paths removed from the environment |
| Codex installed Plugin Builder execution | NOT VERIFIED | No installed-plugin T1–T8 execution recorded |
| ChatGPT Work Local/Desktop Plugin Builder execution | NOT VERIFIED | No installed-plugin T1–T8 execution recorded |
| OpenClaw | NOT APPLICABLE | Explicitly excluded from phase one |
| Claude | NOT APPLICABLE | Explicitly excluded from phase one |

## Feasibility capabilities

| Capability | Codex | ChatGPT Work Local/Desktop |
| --- | --- | --- |
| Read the approved normalized package | PASS | PASS |
| Create an isolated workspace | PASS | PASS |
| Write a minimal plugin | PASS | PASS |
| Execute the bundled deterministic validator | PASS | PASS |
| Generate and return a ZIP | PASS | PASS |

Both returned ZIPs were independently checked for their reported SHA-256, exact member closure, safe paths, valid manifest, embedded PASS result, approved input identity, and absence of Workbench imports. This evidence proves required runtime primitives only; it does not prove the Plugin Builder acceptance scenarios end to end.

## Repository-local phase-two verification

The repository-local implementation directly exercises T1–T6, pause/resume/cancel, canonical v1.1 and retained recognized-legacy intake, bundled local tools, optional runtime-native and MCP evidence, portable wrapped ZIPs, digest-closed evidence packaging, and T7 from the generated artifact. Direct Design Assistant-to-Builder interoperability covers full/create and delta/update without manual sidecar repair. These results prove local application execution, not installed runtime discovery.

| Gate | Command or observation | Result |
| --- | --- | --- |
| Product contracts | `python -B -m unittest discover -s applications/plugin-builder/tests -v` | PASS: 233 tests; one native-symlink test skipped because Windows lacks the required privilege, with reparse classification covered separately |
| Repository discovery | `python -B -m unittest tests.test_application_config tests.test_agents_contract -v` | PASS: 10 tests |
| Plugin structure | framework `validate_plugin_tree` on source and extracted install artifact, plus installed Plugin Creator 0.1.22 package-format review | PASS: both executable validations returned no issues; the Plugin Creator review is a static contract review, not a separate executable validator |
| Skill structure | installed Skill Creator `quick_validate.py` for each of four source skills and each extracted-artifact skill | PASS: 8 of 8 |
| Framework | `python -B -m unittest discover -s tests/framework -v` | PASS: 321 tests; 2 platform skips |
| Workbench handoff interoperability | `python -B -m unittest tests.test_workbench_handoff_interoperability -v` | PASS: 4 tests; full/create and delta/update reach S2 without repair, preserving canonical records, UTF-8 source bytes, baseline identity, unaffected baseline content, and repeat ZIP identity |
| Configured verification | `python -B scripts/verify_extraction.py --application plugin-builder` | PASS: provenance, product commands, local Codex build, deterministic schema-v3 package builds, verification, and repository gates |
| Generated Codex artifact | two isolated `build_marketplace_release.py` builds, deterministic host-upload ZIP construction, extracted plugin/skill validation, canonical full/delta intake, T7, and extracted T8 kit preparation | PASS: both 78-member flat-root upload ZIPs were byte-identical; standalone create/update and T8 kit preparation passed |
| Returnable T1–T8 owner kit | Two independent `build-runtime-kit.py` builds from the reviewed ZIP and release manifests | PASS: both kits were byte-identical, with raw/canonical handoffs, v2/v3 schemas, prepared plans, reviewed ZIP, and identity inventory |
| Generated create/update plugins | extracted T7-style create and update ZIPs validated with framework `validate_plugin_tree` and installed Skill Creator `quick_validate.py` | PASS: both plugin trees returned no issues and both generated skills passed |

The configured verifier's schema-v3 bundle construction is package-contract evidence only. It is not OpenClaw discovery or execution evidence and does not change OpenClaw from `NOT APPLICABLE` in the approved phase-one scope.

The CLI commands are `status`, `validate-session`, `inspect`, `plan`, `approve-w1`, `resolve-update`, `build`, `verify`, `approve-w2`, `package`, `package-runtime-evidence`, `pause`, `resume`, and `cancel`; each operational command emits one machine-readable result document. Installed-plugin discovery, installed representative execution, and application conversation behavior remain `NOT VERIFIED`.

Plugin Builder 1.0.1 was published to the Obvious One GitHub Codex marketplace through marketplace PR #5 at commit `5deedc580acb9afa276f81abeca15e91ce20a56c`. Marketplace publication does not establish installation, discovery, installed execution, or application behavior. No OpenAI universal-directory submission, Git tag, or GitHub Release was performed.

## Installed-runtime completion boundary

The retained T1–T7 v2 replay contract and separate T8 contract are tracked under `tests/runtime/`. The standalone artifact carries the T8 MCP plan/loopback fixture, v3 result schema/template, and preparer; `build-runtime-kit.py` creates a separate deterministic owner kit with both sample handoffs, exact install ZIP, release inventory, and generated scenario inputs. T8's explicitly approved `verify --allow-loopback` operation can pass on the build host with `BUILD_HOST_LOCAL_MCP` evidence in the W2 report while every installed Skill-invocation, capability-discovery, result-delivery, and behavior layer remains `NOT VERIFIED`. The remote HTTPS realization still requires separate setup and direct observation. A v3 evidence bundle requires matching reviewed ZIP, W1-approved plan/session, tool routes, and digest-backed observations. A local copy cannot prove installed discovery or execution in Codex or ChatGPT Work.

Current compatibility classification: `CONDITIONALLY PORTABLE`. Current completion state: `CONVERSION COMPLETE — RUNTIME VALIDATION PENDING`. Codex installed-plugin and ChatGPT Work Local/Desktop application rows stay `NOT VERIFIED`; runtime-native and MCP tool execution also stays `NOT VERIFIED` unless the named capability or service is actually authorized and observed. Obvious One GitHub marketplace publication is `PUBLISHED`; OpenAI universal-directory submission remains `NOT_PERFORMED`.
