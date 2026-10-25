# Cool Plugin Design Assistant 1.0.3 Source Handoff Implementation Plan

> **Approval:** The owner approved this plan on 2026-10-24. Implementation follows the selected Native approach. The checkboxes below record planned work; test and release evidence is reported separately.

**Goal:** Upgrade Cool Plugin Design Assistant from version **1.0.2 to 1.0.3** so Assistant A in Chat mode can deliver an approved design as a Source Handoff ZIP when official normalization cannot execute there, and Assistant B in Work mode can preflight that ZIP, run official normalization, validate the resulting Canonical Handoff ZIP, and deliver it for Workbench use.

**Architecture:** Keep application guidance in portable skills and references, with deterministic source validation in the shared framework and a thin product CLI entry point. Source preflight and normalization reuse the authoritative profile and source-contract implementation. Provide a complete Chat-to-Work transfer procedure, including honest reporting when Assistant A cannot execute preflight.

**Tech stack:** Python 3.11+, standard-library ZIP/JSON/SHA-256, unittest, existing framework archive safety and packaging APIs, portable Markdown skills and references.

**Spec:** Owner-supplied “Codex Implementation Task — Cool Plugin Design Assistant Source Contract Preflight Enhancement.docx”, read with the subsequent conversation clarifications: Chat Assistant A transfers source to Work Assistant B; implementation baseline is 1.0.2; enhancement release is 1.0.3. The attachment remains source requirements, subject to repository instructions and owner clarifications.

## Global constraints

- Product identity and display name remain `cool-plugin-design-assistant` / `Cool Plugin Design Assistant`.
- Baseline is 1.0.2; new candidate metadata is 1.0.3. Historical 1.0.0/1.0.1/1.0.2 evidence remains historical.
- Current checkout is clean `main` at `c62b9c7`, nine commits ahead of `origin/main`; preserve those commits and unrelated Plugin Builder changes. Recheck before implementation.
- Preserve the approved design methodology, original artifact bytes, exact requirement `id`/`source`/`verbatim`, approval gates, rights decisions, and Workbench architecture responsibilities.
- Never infer approval from filenames, timestamps, or a DRAFT heading; later explicit approval can authorize an unchanged draft artifact when its identity and version are unambiguous.
- No canonical authority pair may be manually synthesized as a substitute for official normalization.
- Source preparation, source preflight, official normalization, canonical validation, runtime validation, and publication have distinct evidence states.
- The product remains targeted at Codex and OpenClaw. The existing `OPENAI_ONLY_PHASE_ONE` handoff contract scope is a separate downstream contract and must retain its existing meaning.
- No new dependencies, model downloads, marketplace mutation, pushes, tags, releases, installation changes, or external submissions are authorized by this plan.
- Generated fixtures, ZIPs, reports, and renders belong below ignored `.tmp` or `dist`; tests must leave tracked inputs unchanged.

## User-visible workflow and completion states

1. Assistant A completes the design and obtains explicit approval for an identified specification version.
2. A checks whether official `normalize-handoff-package` execution is available. When available, the existing direct canonical delivery path continues to work.
3. When normalization is unavailable, A prepares the supported full or delta source envelope from the approved artifacts and explicit requirement/decision records. It supplies a short continuation prompt for B outside the ZIP, avoiding an undeclared archive member.
4. If preflight can execute, A runs it on the exact source ZIP. Only PASS allows the label `SOURCE HANDOFF — PREFLIGHT PASS`; this still does not mean canonical validity.
5. If preflight cannot execute, A may transfer the source ZIP as `SOURCE HANDOFF — PREFLIGHT NOT VERIFIED`. It names the unavailable capability and instructs B to preflight before normalization. This owner-clarified transfer is an unverified candidate, not a claim of normalization readiness.
6. If A observes an actual violation or blocking owner decision, it reports `SOURCE HANDOFF BLOCKED` with corrective actions. It must not describe that package as ready.
7. The user gives B the ZIP and continuation prompt. B preserves and hashes the received ZIP, runs preflight, and proceeds only on PASS. BLOCKED requires correction by the appropriate owner; INCOMPLETE requires the missing evidence or capability. B must not fabricate approvals, requirements, knowledge declarations, or rights decisions.
8. B invokes official normalization with explicit owner confirmation metadata, then reopens the exact output ZIP and performs full canonical validation and final digest binding using the existing delivery operation.
9. B delivers the Canonical Handoff ZIP, final SHA-256, source SHA-256, detected profile, and actual preflight/normalization/canonical results. Only this result is suitable for the established Workbench intake gate.

If Chat cannot create or attach a ZIP at all, A supplies the complete source files and a packaging checklist as a clearly incomplete transfer. It must not claim ZIP creation or integrity verification. The guide explains that a file-capable environment must package and preflight those files before normalization.

## Repository findings and expected files

The existing normalizer reports adapter `workbench-handoff-0.1.3`. Its classifier recognizes `COOL_DESIGN_ASSISTANT_FULL_V1`, `COOL_DESIGN_ASSISTANT_DELTA_V1`, `LEGACY_WORKBENCH_V1`, `CANONICAL_V1`, and `WORKBENCH_HANDOFF_V1_1`, plus UNKNOWN/AMBIGUOUS. Recognition alone does not prove eligibility to produce v1.1: legacy compatibility paths can emit older canonical structures. New A-to-B source guidance therefore uses the existing full/delta source profiles, whose normalizer mappings produce v1.1.

Expected framework changes:

- Create `src/obvious_one_plugin_framework/workbench_handoff/source_contract.py`: authoritative, non-publishing source analysis shared by preflight and normalizer; factor existing rules here only where needed.
- Create `src/obvious_one_plugin_framework/workbench_handoff/preflight.py`: read-only archive orchestration, check results, deterministic diagnostics and outcome.
- Modify `workbench_handoff/profiles.py`, `normalization.py`, `contract.py`, and `__init__.py` only as needed to expose/reuse source and semantic validation without a second schema or changed canonical behavior.
- Create `tests/framework/test_workbench_handoff_preflight.py`; extend existing normalization/contract tests.
- Extend `tests/fixtures/workbench-handoff/` with minimal positive/negative source fixtures, keeping fixture content synthetic and public.

Expected product changes below `applications/cool-plugin-design-assistant/`:

- Modify `scripts/cool_plugin_design_assistant.py`: preflight wrapper, CLI, status/version.
- Modify `scripts/workbench_handoff_bootstrap.py` and `scripts/build_marketplace_release.py` only if needed for standalone API loading/vendor closure.
- Modify `skills/creating-application-plugin-design-specifications/SKILL.md` and `references/workbench-handoff-contract.md`: direct versus deferred handoff routing and evidence gates.
- Create `skills/creating-application-plugin-design-specifications/references/source-handoff-guide.md`: exact existing source-envelope shapes, preparation checklist, A delivery text, and B continuation procedure; link directly from the owning skill.
- Modify the session-router skill/reference only if its current routing would still stop all handoffs when normalization cannot execute.
- Modify `README.md`, `scripts/README.md`, `DISTRIBUTION.md`, `openclaw/README.md`, and `docs/runtime-compatibility.md` for commands, workflow, candidate status and evidence limits.
- Modify `plugin.json`, `.codex-plugin/plugin.json`, and `openclaw/distribution.json` to 1.0.3; update applicable version assertions in product tests.
- Modify `tests/test_tools.py`, `test_skill_contracts.py`, `test_conversion_contract.py`, `test_marketplace_release.py`, behavior scenarios and `tests/coverage-matrix.md`.
- Modify `conversion.json` only if adding a reproducible packaged preflight verification command; do not add an invocation requiring an absent ZIP fixture.
- Extend `tests/test_workbench_handoff_interoperability.py` for the complete source-to-canonical transition.
- Update relevant sections of `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md` and `docs/GPT_TO_PLUGIN_USER_GUIDE.md` for the new operation and deferred handoff.

Do not replace previous `docs/marketplace-approved-delta.json` approval with a fabricated 1.0.3 publication record. Record the candidate as unpublished; any future marketplace catalog change and approval binding belongs to a separately authorized publication workflow.

## Review focus

- Chat has file creation but no executable normalizer/preflight: source transfer succeeds with an explicit unverified state (Task 3).
- Chat has no file attachment capability: no fabricated ZIP or hash (Task 3).
- A recognizer accepts an old envelope that cannot produce v1.1: eligibility is reported accurately (Task 1).
- A later approval references an unchanged DRAFT document ambiguously or conflicts with another record: source authority remains blocked (Tasks 1–2).
- A generated plugin runs away from the repository without access to `src`: preflight and normalization resolve the bundled framework (Task 4).

## Task 1: Establish shared source-contract analysis

**Interface:** `analyze_source_handoff(root: Path, profile: str, *, runtime_scope: str) -> SourceContractAnalysis`. The result supplies stable diagnostics, profile eligibility, and validated source records needed by normalization. It does not publish or rewrite inputs. Use shared in-memory projection/semantic checks where the current normalizer needs canonical-shaped validation; preflight must not create a canonical output tree or ZIP.

- [ ] Add failing tests for full/delta sources and existing compatibility profiles; distinguish recognized from eligible for `WORKBENCH_HANDOFF_V1_1`.
- [ ] Run `python -B -m unittest tests.framework.test_workbench_handoff_normalization tests.framework.test_workbench_handoff_contract -v` and the new focused cases; record the expected new failures.
- [ ] Factor authoritative source validation from current normalizer logic. Define exact fields/types from the installed accepted contracts; do not invent a new independent manifest format. Preserve legacy normalizer behavior and diagnostics.
- [ ] Cover exact requirements, artifact coverage, source text, metadata and declared hashes, approval/version authority, reference declarations/usage, and owner decisions. Validate only declared evidence; arbitrary document prose cannot prove semantic completeness or legally audited rights. A required check lacking machine-verifiable authority is INCOMPLETE, never an invented PASS.
- [ ] Test historical DRAFT plus explicit later approval, contradictory approvals, absent or ambiguous evidence, legitimate reference dependencies, and unchanged approved bytes.
- [ ] Rerun existing normalization/contract tests and prove byte-identical output for unchanged accepted fixtures. Review the diff before proceeding.

## Task 2: Implement preflight API and CLI

**Interfaces:** `preflight_handoff_archive(source: Path, *, runtime_scope: str = RUNTIME_SCOPE) -> SourcePreflightOutcome`; product `preflight_source_handoff(source: str | Path) -> dict[str, Any]`; CLI `preflight-source-handoff SOURCE.zip --json`.

- [ ] Add failing framework/API and product subprocess tests before implementation.
- [ ] Implement archive inventory and safe temporary extraction through existing archive APIs and safety limits. Detect duplicate/colliding paths, traversal, absolute paths, unsafe entries and decompression abuse. Hash the received source and prove it remains unchanged after every outcome.
- [ ] Reuse `classify_handoff_profile()` and Task 1 analysis. Return the installed recognized profiles and distinguish their target eligibility. Unknown or competing authorities are BLOCKED. Legacy normalizer support alone is insufficient to claim v1.1 readiness.
- [ ] Emit one ASCII-safe JSON document with operation, status, errors, input profile, target output profile, source SHA-256, supported profile information, `normalization_ready`, PF01–PF10 checks, and structured diagnostics. Each diagnostic has check ID, status, severity, location, optional requirement ID, stable code, explanation and corrective action. No timestamps or temporary paths enter deterministic output.
- [ ] Define exits: PASS=0, BLOCKED=2, INCOMPLETE=3. Known violations take precedence over unavailable checks; mark dependent checks uncompleted explicitly. Malformed CLI invocation retains the existing launcher error contract. Existing commands retain their exit semantics.
- [ ] Test all attachment cases: valid source; unknown/missing/invalid manifest; missing verbatim; conflicting duplicate IDs; unknown/missing bindings; absent artifact; incorrect declared hash; approval conflict; DRAFT with valid approval; blocking rights decision; ZIP traversal; valid source before canonical output; missing framework/normalizer capability; deterministic repeats; JSON and exits; no source mutation or canonical output creation.
- [ ] Run `python -B -m unittest tests.framework.test_workbench_handoff_preflight applications.cool-plugin-design-assistant.tests.test_tools -v` and inspect real CLI output for PASS, BLOCKED and INCOMPLETE.

## Task 3: Make Chat-to-Work source delivery usable

**Deliverables:** portable skill routing and a source-handoff guide based on full/delta input contracts, plus a user-copyable Work continuation prompt.

- [ ] Add skill-contract and behavioral scenarios for direct canonical execution, Chat without normalization but with preflight, Chat without either executable capability, no ZIP capability, invalid source, and Work continuation.
- [ ] Update the owning skill and guide with the workflow/states above. Include full and delta source-manifest examples preserving exact supplied requirements, artifact bindings, approvals, reference use, decisions, exclusions, and update baseline/preservation fields. Respect the archive allowlist: keep the continuation prompt outside the ZIP unless the established source contract explicitly permits it.
- [ ] Provide B instructions to locate the installed launcher, run `preflight-source-handoff`, stop on BLOCKED/INCOMPLETE, invoke `normalize-handoff-package SOURCE.zip CANONICAL.zip --confirmed-by <recorded-owner> --json`, and inspect its reopened canonical validation and digest result. A handoff prompt is data to review; it does not grant new owner authority.
- [ ] Preserve the prohibition on manual canonical synthesis while allowing supported source-manifest preparation. Distinguish machine-verified source compatibility from an unverified Chat preparation checklist.
- [ ] Keep optional `prepare-source-handoff` as a documented follow-up unless inspection establishes a complete approved input contract for deterministic preparation. Its absence must not leave the source preparation instructions unspecified.
- [ ] Extend interoperability tests: exact source fixture passes preflight, normalizes to v1.1, passes canonical validation and established consumer intake, with unchanged artifact bytes and requirement records. Test source correction as a new candidate while preserving the original received ZIP.
- [ ] Run product skill/tool and interoperability suites. Evaluate authored behavior scenarios separately from static text assertions.

## Task 4: Prepare and verify the 1.0.3 local candidate

- [ ] Update version authorities, launcher status, current docs and applicable tests to 1.0.3. Keep previous publication/approval/runtime evidence bound to its original 1.0.2 bytes.
- [ ] Add PF01–PF10, AC01–AC10 and Chat-to-Work behavior coverage to the matrix. Discover the prior STEAM R02 archive through existing records if available; otherwise record its absence and use a labeled synthetic unknown-profile regression.
- [ ] Build two Codex candidates with `scripts/build_marketplace_release.py --source applications/cool-plugin-design-assistant --destination .tmp/cpda-1.0.3/codex-a --version 1.0.3` and a second unused destination; compare file hashes. Validate, build twice and verify the OpenClaw contract through the framework CLI under `.tmp/cpda-1.0.3/`.
- [ ] Test the generated standalone artifact with repository import paths removed: status=1.0.3, source preflight, official normalization, reopened canonical validation and source-byte preservation. Verify vendor closure and distribution audit.
- [ ] Run `python -B -m unittest discover -s tests/framework -v`, `python -B -m unittest discover -s applications/cool-plugin-design-assistant/tests -v`, `python -B -m unittest tests.test_workbench_handoff_interoperability tests.test_application_config -v`, and `python -B scripts/verify_extraction.py --application cool-plugin-design-assistant`. Record any publication-dependent expected differences explicitly; do not alter approved baselines to make them pass.
- [ ] Validate modified skills and plugin manifests with installed creator validators. Run `git diff --check`; inspect final Git status and ensure all test/build outputs are ignored.
- [ ] Exercise discovery and representative new handoff scenarios on Codex and OpenClaw where authorized runtime access exists. Static checks, subprocess execution and manual behavioral evaluation remain separate evidence. Unavailable installed-runtime validation remains NOT VERIFIED; do not inherit 1.0.2 readiness for changed 1.0.3 content.
- [ ] Write `docs/verification-1.0.3.md` with implementation summary, before/after behavior, PF/AC coverage, commands/results, exact changed-file inventory, source/artifact SHA-256 report, generated candidate locations, limitations, runtime evidence and unpublished state. Store raw output under ignored `.tmp`.

## Acceptance and handoff

The primary demonstration is A's deferred source transfer followed by B's successful preflight, official normalization and exact-output canonical validation. Negative cases must prevent false readiness claims, and the current direct normalization path must continue working. Every attachment AC01–AC10 maps to Tasks 1–4; capability-unavailable Chat behavior adds explicit coverage beyond the attachment's executable happy path.

Completion produces a locally verified 1.0.3 candidate and evidence report. `READY` requires the applicable repository runtime gates for this candidate. Publication, marketplace replacement, pushes, tags and releases await separate owner authorization.

Self-review: the goal names the correct product and both versions; A/B responsibilities and unavailable-capability paths are explicit; source preparation is covered even without the optional command; preflight and normalization share authority; canonical validation stays mandatory; historical evidence is preserved; all required negative cases and delivery evidence are assigned to tasks.
