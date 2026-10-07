# Evidence and package contract

## Evidence states

| Key | Outcome |
| --- | --- |
| EXPECTED | DEFINED_NOT_OBSERVED |
| STATICALLY VERIFIED | STRUCTURE_OR_CONTENT_INSPECTED |
| RUNTIME VERIFIED | DIRECT_EXECUTION_OBSERVED |
| NOT VERIFIED | APPLICABLE_CHECK_NOT_RUN |

Record each check independently with requirement IDs, command or observation, environment identity, result, and limitation. Do not infer execution from structure, discovery from installation, or correctness from process exit alone. Runtime exclusions use `NOT APPLICABLE` outside this four-state evidence column.

## Evidence layers

| Key | Outcome |
| --- | --- |
| structural_validation | STATIC_ONLY_UNTIL_INSTALLED_TEST |
| installation | INDEPENDENT_UPLOAD_AND_DISCOVERY_EVIDENCE |
| tool_execution | DECLARED_AND_OBSERVED_COMMAND_EVIDENCE |
| reference_consultation | NOT_VERIFIED_WITHOUT_SCENARIO_DIGEST |
| conversation | NOT_VERIFIED_WITHOUT_SCENARIO_DIGEST |

## Packaging contract

| Key | Outcome |
| --- | --- |
| REQUIRED_FAILURE | BLOCK_ARTIFACT |
| PRECONDITION | W2_APPROVED |
| DELIVERY | RETURN_ZIP_FOR_MANUAL_UPLOAD |
| ENVELOPE | PORTABLE_SINGLE_DIRECTORY |
| SIDECAR | DIGEST_BOUND_OUTSIDE_ZIP |

Run `verify` before presenting W2. The summary names every required failure, optional `NOT VERIFIED` limitation, executed tool, and preserved update member. After explicit acceptance, `approve-w2` binds the exact candidate and report hashes; `package` rejects stale or mismatched evidence.

Before requesting W2, present the candidate delta, every required/optional result, all `NOT VERIFIED` items, unresolved rights/dependencies, and the proposed archive boundary. A required `FAIL` cannot be waived into an artifact.

After W2, build with a sorted allowlist, fixed metadata, canonical text rules, and a content manifest. Independently reopen the wrapped ZIP, reject unsafe or undeclared members, validate the plugin manifest, and report its SHA-256. Keep `package-metadata.json` outside the installable ZIP, bind its SHA-256 in the exact session identity, and carry the approved preflight, manifest-profile, command, and evidence-layer records without promotion. Return the file or usable local path to the user; no account installation or public release is part of this operation.
