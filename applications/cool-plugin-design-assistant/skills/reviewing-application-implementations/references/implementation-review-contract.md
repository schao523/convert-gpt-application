# Application Implementation review contract

## Required inputs

1. The complete approved Application Plugin Design Specification, including
   version, approval evidence, requirement IDs, acceptance criteria, and
   approved deviations.
2. Inspectable Application Implementation evidence, such as source files,
   manifests, configuration, generated artifacts, test reports, runtime logs,
   or user-supplied observations whose provenance is stated.

If either input is missing or inaccessible, state `REVIEW BLOCKED`, request the
specific missing input, and wait. Do not infer requirements from this plugin's
own design preferences or infer runtime behavior from file names and snippets.

## Finding record

Each finding contains:

- stable `finding_id`;
- cited `requirement_id` and specification version;
- `observed_evidence` with source path, artifact, log, or supplied observation;
- evidence state: `STATICALLY VERIFIED`, `RUNTIME VERIFIED`, or `NOT VERIFIED`;
- one classification;
- severity: `critical`, `high`, `medium`, or `low`;
- rationale linking evidence to the requirement and acceptance criterion; and
- recommended next action with the responsible owner.

Classifications:

- **error** — observed behavior contradicts an applicable requirement;
- **omission** — required behavior or evidence is absent from the inspected
  implementation;
- **optional improvement** — nonrequired enhancement that does not imply
  nonconformance; or
- **approved deviation** — difference from the baseline backed by explicit,
  traceable owner approval.

Do not classify lack of runtime evidence as a runtime failure. Use `NOT
VERIFIED` and identify the missing test or observation. Do not convert an
architectural preference into an error or omission.

## Output

Report the reviewed specification version, inspected evidence boundary,
findings ordered by severity, conforming requirements observed, unverified
requirements, approved deviations, and recommended next actions. Distinguish
an implementation correction from a proposed specification revision.

The review describes conformance; it does not edit implementation artifacts,
replace Skill Architecture, select new tools or adapters, or claim tests were
run when only static evidence was inspected.
