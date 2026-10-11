# Growing with Children 1.0.2 verification summary

## Scope and immutable identities

- Source version: 1.0.1
- Derived version: 1.0.2
- Source ZIP SHA-256: `e20ab7f970565dde1d2bfa8529d82da12366dfbed6a6672aed9dc51eedb6d1f1`
- Repaired ZIP SHA-256: `e35b5fe14d2a9b0fa2330ad28572aff76df2e907d027444147e4691396e0c25b`
- Package metadata SHA-256: `3c59ca7cc7188ac6ead19ecbd3262ac6ff1034af764422c0cadf138691f31b6b`
- Member-manifest SHA-256: `776437ac30c4d16c940ff700963167d1ede8d172651d7c034fe7e742eb045b3d`
- Onboarding proposal document SHA-256: `bf2ef7db9ab08656cb08c3c12215e550326d001f5ce7aa9077d31cd9a942142a`
- Onboarding proposal identity SHA-256: `b54a3a97b5a28f65952bb7922f700b7722534b3005407ae6e2ebc18ddaf307c5`
- Staged Codex artifact content SHA-256: `d7378703283ff62f98e6e7b680f36d5fdc2e82b53f0c5973dea8b98160492c0d`

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
- The staged and installed Codex plugin includes the owner-approved MIT
  `LICENSE`; its SHA-256 is
  `e31ef2620c66c2bd09ef56abd6d43264132415e2d1d4cad31452b12143aea8b5`.
- All JSON members parse, both plugin manifests declare version 1.0.2, and the
  repaired tree passes current plugin-authoring validation.
- The five-skill architecture and approved application behavior were not
  changed.

## Test and onboarding results

- Generic framework: 465 passed; 2 documented platform skips.
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
Local Codex installation and discovery of version 1.0.2 are also
`STATICALLY VERIFIED`.

Installed Codex runtime verification used fresh non-interactive processes
against the installed marketplace package. The package was discovered and its
tracked skills were invoked in five controlled scenarios:

- `coaching-parenting-and-sensitive-conversations` handed exact-CUV work to
  `guiding-biblical-study`, verified Ephesians 4:32 against RM-04B PDF page
  228, and returned the result to the coaching response: `PASS`.
- `guiding-parenting-sessions` performed the same owner handoff and return:
  `PASS`.
- `designing-family-devotions` performed the same owner handoff and returned
  the verified text to a five-minute devotion: `PASS`.
- `supporting-parent-reflection` performed the same owner handoff and returned
  the verified text to the reflection response: `PASS`.
- With the owner skill and RM-04B explicitly unavailable, the originating
  skill disclosed the limitation, did not claim exact text, and used the
  documented fallback: `PASS`.

Four additional fresh processes exercised formal ten-step study from each
non-owner skill. Every process named its originating skill, handed execution
to `guiding-biblical-study`, consulted RM-04B page 228, returned only the
first observation step, and waited for the learner before continuing: `PASS`.

These observations make Codex Skill invocation, owner routing, RM-04B visual
consultation, result return, and representative conversation behavior
`RUNTIME VERIFIED` for the tested exact-CUV, formal-study, and fallback
scenarios. The first read-only probe could
not render the scanned PDF and was classified as an environment-only failure;
the unchanged scenario passed after the exact packaged page was rendered in a
disposable root and supplied to the fresh process.

## Obvious One publication result

- Marketplace release commits: `6663cd7a21e577ac292d37d6c17145b8d6b35a5d`
  and corrective commit `b3c24a5de0185d7d879d2aa4c5d88b3984b7cbed`.
- Pull request: `schao523/obvious-one-plugins#6`.
- Published `main` merge commit:
  `8682092411d8899d2cd24fbcbad0d75ad7607527`.
- Exact remote-commit verification: filesystem, Git index, commit, and fresh
  checkout all `PASS` across the 731-file marketplace catalog.
- Published marketplace tree SHA-256:
  `2bfd893862d626efd547e8f6c24d6385f90ea98fb2903296385e4f1e7fa078ed`.
- Fresh Obvious One installation: 228 installed files matched the published
  plugin tree byte for byte; plugin version was 1.0.2 and the installed
  `LICENSE` SHA-256 remained
  `e31ef2620c66c2bd09ef56abd6d43264132415e2d1d4cad31452b12143aea8b5`.
- A fresh read-only Codex process loaded the published Obvious One skill files,
  routed a formal Ephesians 4:32 study from
  `coaching-parenting-and-sensitive-conversations` to
  `guiding-biblical-study`, used RM-04B page 228, returned only the first
  observation step, and waited: `PASS`.

OpenClaw runtime behavior and cross-runtime equivalence remain `NOT VERIFIED`.
ClawHub and the OpenAI universal directory are `NOT APPLICABLE` to this
Codex-only Obvious One publication action.
