# Improvement patch contract

Propose an improvement only when an approved requirement, observed gap, or
explicit owner request establishes the need. Keep proposed corrections separate
from accepted specification and implementation state.

Each patch contains:

- stable `patch_id`;
- `source_requirement_ids` and specification version;
- `observed_gap` with finding, test, or supplied evidence reference;
- `proposed_change` scoped to behavior, specification, test, or implementation;
- impact on workflows, modules, users, safety, privacy, rights, tools, data,
  runtimes, distribution, and existing acceptance criteria;
- compatibility and migration considerations;
- `version` for the proposed target artifact;
- `approval_state`: `draft`, `approved`, `rejected`, or `superseded`;
- owner and required confirmation; and
- verification scenarios for the changed requirement.

If the evidence is `NOT VERIFIED`, propose evidence collection rather than a
corrective patch unless the owner explicitly requests a speculative option.
Label such an option as a recommendation, not a verified defect.

Approval of an improvement patch creates a new versioned baseline. It does not
rewrite prior approval history, prove implementation, or authorize publication.
