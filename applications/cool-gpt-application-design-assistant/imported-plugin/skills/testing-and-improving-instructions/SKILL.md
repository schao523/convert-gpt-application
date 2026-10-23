---
name: testing-and-improving-instructions
description: Design tests, assess supplied results and propose reviewable patches.
---

# testing-and-improving-instructions

Read the applicable [module contracts](references/module-contracts.json) in full. Follow the plugin-root tools/contracts/application-policy.md, tools/contracts/workflows.json, tools/contracts/interaction-protocols.json and tools/contracts/artifact-contracts.md; these are shared application rules. Approved R02 lifecycle supersedes historical draft labels in source artifacts.

Before test cards or rubric obtain current instructions, blueprint, goal and context; missing prerequisites mean request missing items only. Read RM11/RM13 for IM09. Cards include scenario, input, steps, expected observable, version, requirement IDs, evidence state and actual result NOT RUN until executed. Rubric covers accuracy, relevance, clarity, interactivity and consistency with observable full/partial/fail criteria; add depth/structure/resource use where needed. Actual assessment requires target-specific replies. For IM10 read RM05/RM10/RM11/RM13; patches identify baseline/version, exact location, before/after, reason, evidence, affected requirements, preserved functions, rollback and retests. No invented before text. User confirms the patch version before application.

Before substantive methodology, invoke the sibling consulting-design-references Skill and read the applicable resource bodies it owns. Record actual consultation. This delegation is source retrieval, not a claim that an index or hash check read a body.

For deterministic checks, invoke the owning sibling: consulting-design-references for D01, adapting-platforms-and-delivering-packages for D02/D04, or guiding-application-design-sessions for D03. Only those bound Skills invoke the tool; return their actual structured result here. The owner uses bundled design-integrity via direct argv {python} -B tools/design_integrity.py from the installed plugin root, except D04 uses the approved export workspace as cwd and the resolved bundled script path. Read plugin-root tools/design-integrity-contract.json and tools/operation-guide.md before calling. Send {"operation":"D01|D02|D03|D04","input":{...}} as JSON stdin and return parsed JSON stdout to this Skill before interpreting it. Errors/absent execution block the affected path; do not guess a result. No remote MCP service or network permission. Python 3.10+ and host access to installed files/execution must be available; never assume a local test proves installed execution. DEFERRED_ALLOWED installed evidence stays NOT VERIFIED until observed.

Preserve user pause/resume/stop and version-specific confirmation; follow the shared safety/input/source gates. End with the artifact version/state, confirmed scope, unresolved limits and appropriate next step. Do not claim target-platform configuration or runtime success from design text.
