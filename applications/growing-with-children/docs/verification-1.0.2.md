# Growing with Children 1.0.2 verification summary

## Scope and immutable identities

- Source version: 1.0.1
- Derived version: 1.0.2
- Source ZIP SHA-256: `e20ab7f970565dde1d2bfa8529d82da12366dfbed6a6672aed9dc51eedb6d1f1`
- Repaired ZIP SHA-256: `92fdcc725afe1a772386d78d07e5c685a7ef7f2bdf5062029dde4a52614f4b01`
- Package metadata SHA-256: `8a5003d79217d677f8ddf8c8a5fc839c0348f78467bc2a60b1921f0921cf2c1c`
- Member-manifest SHA-256: `d0d46060895cb0cd3d994c7699abf8577cc24e98ae0582a38b21d048c5244520`
- Onboarding proposal SHA-256: `1f5ddb0f64ab0b67946d8adaf5934c729918ad3a9cfd2d841749485475b300d9`

The source archive remained immutable. Two independent clean builds produced
byte-identical repaired ZIP and metadata outputs.

## Structural and behavior-preservation results

- Five skills remain present.
- RM-04A and RM-04B remain byte-identical and occur only below
  `skills/guiding-biblical-study`.
- Each of the four non-owner skills contains two `HANDOFF` records with
  `local_copy: false` and no stale local PDF binding.
- The generated root `THIRD_PARTY_NOTICES.md` records both exact owner paths and
  SHA-256 values under the owner-approved `PUBLIC_DOMAIN` classification.
- All JSON members parse, both plugin manifests declare version 1.0.2, and the
  repaired tree passes current plugin-authoring validation.
- The five-skill architecture and approved application behavior were not
  changed.

## Test and onboarding results

- Generic framework: 461 passed; 2 documented platform skips.
- Plugin Builder: 236 passed; 1 documented Windows symlink-privilege skip.
- Cool Plugin Design Assistant: 47 passed.
- Growing with Children: 5 passed.
- Repository and Windows contracts: 15 passed.
- `git diff --check`: passed.
- ZIP onboarding against the clean adoption baseline: `PASS`.

The approved plan named `tests.test_agent_contract`; the tracked module is
`tests.test_agents_contract`. The incorrect command failed only at import. The
corrected smallest set passed without product-code changes and is classified as
a test-command defect rather than an implementation failure.

## Evidence state

The repaired artifact and onboarding proposal are `STATICALLY VERIFIED`.
Installation, skill invocation, reference use, result delivery, conversation
behavior, and cross-runtime equivalence remain `NOT VERIFIED`. OpenClaw,
ClawHub, and the OpenAI universal directory are outside this Codex-only
publication action.
