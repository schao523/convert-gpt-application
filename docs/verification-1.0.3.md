# Cool Plugin Design Assistant 1.0.3 local candidate verification

## Scope and behavior

This candidate builds on the published 1.0.2 design and digest-bound canonical
handoff behavior. When Chat Assistant A cannot execute the official normalizer,
it can transfer an approved full or delta Source Handoff ZIP. If preflight is
available, A reports its result; otherwise it labels the transfer `PREFLIGHT
NOT VERIFIED`. Work Assistant B preserves the ZIP, runs preflight, and only on
PASS invokes official normalization and validates the final Canonical Handoff
ZIP. Preflight is read-only and does not grant approval, rights or canonical
validity. The existing direct normalization route remains available.

The new `preflight-source-handoff SOURCE.zip --json` command uses the same
profile classifier and source analyzer as normalization. It reports PF01–PF10,
source digest, supported profiles, per-check results and structured diagnostic
actions. Full and delta Design Assistant source profiles are v1.1 eligible;
recognition of historical profiles alone does not imply v1.1 eligibility.
Unknown or conflicting profiles and known contract violations are BLOCKED.
Unavailable shared runtime capability is INCOMPLETE. Exit codes are 0, 2 and
3 respectively.

## Tests and artifact evidence

| Gate | Result |
| --- | --- |
| Source preflight, normalization, canonical contract, interoperability and application-config focused suite | PASS: 41 tests |
| Product suite | PASS: 50 tests |
| Changed owning Skill quick validator | PASS |
| Schema-v3 distribution contract | PASS |
| OpenClaw candidate build and `verify` | PASS: 69 files, 299873 bytes, content digest `a714e6208848230ef83923759eb690164d277c9c1f1d7b8f64486fd394f8e966` |
| Codex candidate build | PASS: two build manifests had SHA-256 `a3f6b302561e1ba35b686be43ac1f35b9ff1d9b41d7c0a2f194ee3511b5c3637` |
| OpenClaw candidate determinism | PASS: two content manifests had SHA-256 `933df8dbe9b57f0d7f3d9fc152bd21eb75c873efa889f3a61f0d181e290d1099` |
| Packaged Codex command with isolated Python imports | PASS: status 1.0.3, source preflight PASS, official normalization PASS |
| Synthetic source ZIP preservation | PASS: preflight source SHA-256 `3048f72528bea2e9983ddfd9689ced7aa655759292eb9bca7cf37e29a3342255` |
| Canonical output binding | PASS: both packaged Codex and OpenClaw commands returned and produced the same ZIP SHA-256 `d311e7786e36d574dcb3ecc9e155af686ade243cf18b64c0306150a039b25ee1`; each normalizer reopened its ZIP and validated canonical v1.1 |
| Repository product verifier | PASS: shared framework, product, provenance, deterministic builds and package verification; marketplace gate NOT VERIFIED because no marketplace was supplied |
| `git diff --check` | PASS |

The full framework suite passes: 573 tests, 3 skips, using an elevated Windows
test process with its system temporary directory outside this Git checkout.
Earlier failures arose from restricted hard-link and checkout operations and
from placing nominally non-Git test fixtures under the repository's `.tmp`
root. The repository product verifier subsequently passed in the corrected
environment; its marketplace gate was NOT VERIFIED because no marketplace
path was supplied. Raw logs are below ignored `.tmp/cpda-1.0.3/` and
`.tmp/verification/run-20261024T235911Z-39704-ac239df1/`.

The prior STEAM R02 archive was not available in this checkout. A synthetic
unknown-profile staging ZIP is used for the `profile.unrecognized` regression.
The Source Contract Preflight check and acceptance mapping is in
`applications/cool-plugin-design-assistant/tests/coverage-matrix.md`.

## Limitations and release state

The source analyzer validates declared reference inventory type, artifact
provenance/version and bindings. It cannot prove whether design prose contains
all required professional knowledge or independently audit redistribution
rights. It checks declared artifact hashes and sizes when supplied; the
existing source contract does not require those fields. An optional source
preparation command was not added because no separate verified input authority
for generating manifests and requirement records is established.

The Codex candidate contains a bundled Workbench runtime. The OpenClaw package
now declares and bundles the same required framework modules. An isolated
Python subprocess confirms it loads that bundled copy; packaged preflight
passes. Installed discovery, representative Chat/Work execution and
cross-runtime equivalence for 1.0.3 are NOT VERIFIED. Historical 1.0.2
runtime evidence is not attributed to this candidate. The 1.0.3 candidate is
unpublished, and no marketplace mutation, Git push, tag or release occurred.

Candidate paths:

- `.tmp/verification/run-20261024T235911Z-39704-ac239df1/applications/cool-plugin-design-assistant/codex-marketplace/plugins/cool-plugin-design-assistant`
- `.tmp/verification/run-20261024T235911Z-39704-ac239df1/applications/cool-plugin-design-assistant/openclaw-a/cool-plugin-design-assistant`
- `.tmp/cpda-1.0.3/approved-source.zip` (synthetic test input)
- `.tmp/cpda-1.0.3/canonical-codex-verified.zip` and
  `.tmp/cpda-1.0.3/canonical-openclaw-verified.zip` (synthetic test outputs)

## Changed-file inventory

- Framework: `contract.py`, `package_builder.py`, and
  `workbench_handoff/{__init__,contract,normalization,preflight,source_contract}.py`.
- Product CLI and metadata: `scripts/cool_plugin_design_assistant.py`,
  `scripts/workbench_handoff_bootstrap.py`, `scripts/distribution_audit.py`,
  `plugin.json`, `.codex-plugin/plugin.json`, `openclaw/distribution.json`.
- Product guidance: `README.md`, `DISTRIBUTION.md`, `scripts/README.md`,
  `openclaw/README.md`, `docs/runtime-compatibility.md`, the
  `creating-application-plugin-design-specifications` Skill, its
  `workbench-handoff-contract.md` reference, and new `source-handoff-guide.md`.
- Tests and coverage: product `test_conversion_contract.py`,
  `test_marketplace_release.py`, `test_skill_contracts.py`, `test_tools.py`,
  `coverage-matrix.md`; framework `test_contract.py`, `test_package_builder.py`,
  `test_workbench_handoff_preflight.py`;
  repository `test_workbench_handoff_interoperability.py`.
- Repository guidance: `docs/GPT_TO_PLUGIN_USER_GUIDE.md`,
  `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`, this evidence report, and the approved plan in
  `docs/superpowers/plans/2026-10-24-cool-plugin-design-assistant-1.0.3-source-handoff.md`.
