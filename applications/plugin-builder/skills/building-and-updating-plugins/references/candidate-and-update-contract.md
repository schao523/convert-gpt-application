# Candidate and update contract

## Candidate contract

| Key | Outcome |
| --- | --- |
| PRECONDITION | W1_APPROVED |
| MODES | CREATE_OR_UPDATE_EXPLICIT |
| UNEXPLAINED_UPDATE_CONTENT | PRESERVE_AND_WAIT |
| OUTPUT | CANDIDATE_NOT_FINAL_ZIP |
| PREFLIGHT_IDENTITY | MATCH_APPROVED_W1_EVIDENCE |

Use `resolve-update` to record an explicit keep, replace, or remove decision for every unexplained baseline member, then use `build`. Application-tool files and bindings follow the same preservation rules as skills and references; an unchanged tool is byte-preserved, while a changed contract requires a newly approved W1 identity.

Create a new isolated workspace and record its relative session identity. Never use the Workbench checkout as a runtime dependency.

For ZIP input, normalize separators and reject absolute paths, `..`, device paths, symlinks, duplicate normalized names, and case-fold collisions before extraction. Refuse an existing nonempty output unless it carries the expected session marker and the operation explicitly permits replacement.

For update mode, build a baseline member inventory before changes. Classify each member as changed by approved requirement, preserved unaffected content, or unexplained. Preserve the latter two byte-for-byte until the user explicitly decides otherwise; unexplained executable or policy content must remain a blocking wait.

Generate only files required by the approved plan. Record additions, modifications, preserved members, and unresolved members. The candidate is passed to verification without a final distribution ZIP.

Re-materialize and preflight the exact create tree or projected update overlay before mutation. Its canonical evidence must match the W1-approved preflight digest; drift blocks the build rather than silently producing a different candidate.
