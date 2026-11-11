# Cool Bible Tutor 2.4.9 ZIP publication

## Scope and authority

Publish the supplied Desktop ZIP as the Codex artifact for `cool-bible-tutor` 2.4.9 in Obvious One. The archive SHA-256 is `5f8b7a1b5f5ef7705885cda8458b6ea6db8ec5f824e588642f9324872d0d59cb`. It has 138 files. Relative to the published 2.4.8 Codex tree, only `.codex-plugin/plugin.json` and eight `skills/*/SKILL.md` files differ. All bundled executables, PDFs, databases, references, license, and notices have identical bytes. Keep the existing OpenClaw artifact and release assets unchanged; installed conversation behavior remains `NOT VERIFIED` until separately tested. The owner approved Codex-only 2.4.9 and this bounded Workbench correction in chat.

## Workbench compatibility correction

The current Workbench application version is tied to its OpenClaw distribution contract (2.4.7). The marketplace catalog's Codex `verify_existing` target currently checks that same version, so it cannot verify an independently supplied 2.4.9 Codex ZIP. Add an optional `version` field to schema-v2 **Codex `verify_existing`** targets only. Require a nonempty version different from the application version when present. The target's manifest check and generated validation-registry target version must use it. Keep the application's source and OpenClaw contract at 2.4.7, and retain all other target-mode semantics. This field does not grant any rights or installed-runtime status.

Copy the eight changed skill files from the ZIP into Workbench's application source. Keep the source plugin manifest and OpenClaw contract at 2.4.7 to avoid implying an OpenClaw release. Set the catalog's Codex target to `verify_existing`, `version: 2.4.9` and keep OpenClaw `verify_existing` at 2.4.7. Document the supplied ZIP hash and exact member comparison in release evidence.

Five earlier Codex metadata patch releases are already present in the published marketplace. Their Workbench catalog entries must be pinned to `verify_existing` at those published Codex versions before the current catalog can prepare a new stage from marketplace main. This pin changes only generated validation metadata; it does not change those five plugin trees.

## Local publication sequence

1. Validate ZIP integrity, member paths, plugin identity, version, rights-file preservation, and exact difference from 2.4.8.
2. Copy the existing Obvious One baseline to an isolated root and overlay only the Codex plugin tree with the exact ZIP members. Confirm every staged member has the ZIP's hash and no extra members exist.
3. Run `prepare-marketplace` to regenerate catalogs and registry from this baseline without mutating the public repository. The stage must differ from published main only in the nine plugin files and necessary generated controls.
4. Run filesystem, index, commit, and fresh-checkout gates; run product/framework tests, distribution audit, exact Scripture retrieval, and `git diff --check`. Classify the ZIP's historical 2.4.7 test fixtures and local socket restrictions separately from release behavior.
5. Review the exact staged delta and obtain the required final Git/marketplace authorization before push and merge. Merge Workbench first, then the Obvious One PR only if both CI and exact-byte gates pass. Verify both main branches afterward.

## Acceptance criteria

- The published 2.4.9 Codex tree is byte-for-byte equal to the supplied ZIP's members.
- The existing OpenClaw tree, runtime assets, rights files, and all unrelated plugins are byte-identical.
- The generated registry independently records Codex 2.4.9 and existing OpenClaw 2.4.7.
- A tampered or wrong-version Codex tree fails verification; OpenClaw version mismatch remains fail-closed.
- No installed-runtime or behavioral claim is inferred from static or CI verification.
