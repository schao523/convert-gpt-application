# Candidate and update contract

## Candidate contract

| Key | Outcome |
| --- | --- |
| PRECONDITION | W1_APPROVED |
| MODES | CREATE_OR_UPDATE_EXPLICIT |
| UNEXPLAINED_UPDATE_CONTENT | PRESERVE_AND_WAIT |
| OUTPUT | CANDIDATE_NOT_FINAL_ZIP |

Create a new isolated workspace and record its relative session identity. Never use the Workbench checkout as a runtime dependency.

For ZIP input, normalize separators and reject absolute paths, `..`, device paths, symlinks, duplicate normalized names, and case-fold collisions before extraction. Refuse an existing nonempty output unless it carries the expected session marker and the operation explicitly permits replacement.

For update mode, build a baseline member inventory before changes. Classify each member as changed by approved requirement, preserved unaffected content, or unexplained. Preserve the latter two byte-for-byte until the user explicitly decides otherwise; unexplained executable or policy content must remain a blocking wait.

Generate only files required by the approved plan. Record additions, modifications, preserved members, and unresolved members. The candidate is passed to verification without a final distribution ZIP.
