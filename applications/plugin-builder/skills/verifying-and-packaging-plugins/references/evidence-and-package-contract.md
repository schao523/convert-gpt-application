# Evidence and package contract

## Evidence states

| Key | Outcome |
| --- | --- |
| EXPECTED | DEFINED_NOT_OBSERVED |
| STATICALLY VERIFIED | STRUCTURE_OR_CONTENT_INSPECTED |
| RUNTIME VERIFIED | DIRECT_EXECUTION_OBSERVED |
| NOT VERIFIED | APPLICABLE_CHECK_NOT_RUN |

Record each check independently with requirement IDs, command or observation, environment identity, result, and limitation. Do not infer execution from structure, discovery from installation, or correctness from process exit alone. Runtime exclusions use `NOT APPLICABLE` outside this four-state evidence column.

## Packaging contract

| Key | Outcome |
| --- | --- |
| REQUIRED_FAILURE | BLOCK_ARTIFACT |
| PRECONDITION | W2_APPROVED |
| DELIVERY | RETURN_ZIP_FOR_MANUAL_UPLOAD |

Run `verify` before presenting W2. The summary names every required failure, optional `NOT VERIFIED` limitation, executed tool, and preserved update member. After explicit acceptance, `approve-w2` binds the exact candidate and report hashes; `package` rejects stale or mismatched evidence.

Before requesting W2, present the candidate delta, every required/optional result, all `NOT VERIFIED` items, unresolved rights/dependencies, and the proposed archive boundary. A required `FAIL` cannot be waived into an artifact.

After W2, build with a sorted allowlist, fixed metadata, canonical text rules, and a content manifest. Independently reopen the ZIP, reject unsafe or undeclared members, validate the plugin manifest, and report its SHA-256. Return the file or usable local path to the user; no account installation or public release is part of this operation.
