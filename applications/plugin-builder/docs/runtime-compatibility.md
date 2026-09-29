# Runtime compatibility evidence

Phase-one runtime scope is `OPENAI_ONLY_PHASE_ONE`.

| Runtime | Evidence state | Environment identity |
| --- | --- | --- |
| Codex | RUNTIME VERIFIED | Primitive feasibility only; Codex Desktop local projectless task; codex-cli 0.146.0 |
| ChatGPT Work Local/Desktop | RUNTIME VERIFIED | Primitive feasibility only; user-confirmed native local execution; returned artifact independently inspected |
| Codex installed Plugin Builder execution | NOT VERIFIED | No installed-plugin T1–T7 execution in this foundation slice |
| ChatGPT Work Local/Desktop Plugin Builder execution | NOT VERIFIED | No installed-plugin T1–T7 execution in this foundation slice |
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

## Foundation verification

On 2026-09-29, the repository-local foundation produced the following evidence:

| Gate | Command or observation | Result |
| --- | --- | --- |
| Product contracts | `python -B -m unittest discover -s applications/plugin-builder/tests -v` | PASS: 38 tests; one native-symlink test skipped because Windows lacks the required privilege, with reparse classification covered separately |
| Repository discovery | `python -B -m unittest tests.test_application_config -v` | PASS: 4 tests |
| Plugin structure | bundled `validate_plugin.py applications/plugin-builder` | PASS |
| Skill structure | bundled `quick_validate.py` for each of four skills | PASS: 4 of 4 |
| Framework | `python -B -m unittest discover -s tests/framework -v` | PASS: 273 tests; 2 platform skips |
| Configured verification | `python -B scripts/verify_extraction.py --application plugin-builder` | PASS: provenance, product commands, local Codex build, deterministic schema-v3 package builds, verification, and repository gates |
| Generated Codex artifact | two isolated `build_marketplace_release.py` builds plus generated-artifact plugin validation | PASS: 30 declared members equal 30 actual members, no forbidden internal members, identical release manifests |

The configured verifier's schema-v3 bundle construction is package-contract evidence only. It is not OpenClaw discovery or execution evidence and does not change OpenClaw from `NOT APPLICABLE` in the approved phase-one scope.

The only implemented product CLI commands are `status --json` and `validate-session <session.json> --json`. Candidate inspection, implementation, verification, final ZIP generation, installed-plugin discovery, and representative create/update execution remain `NOT VERIFIED`.

No marketplace installation, publication, or release is authorized or recorded for Plugin Builder.
