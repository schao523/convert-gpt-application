---
name: guiding-application-design-sessions
description: Route design work, manage approvals, pause and resume.
---

# guiding-application-design-sessions

Read the applicable [module contracts](references/module-contracts.json) in full. Follow the plugin-root tools/contracts/application-policy.md, tools/contracts/workflows.json, tools/contracts/interaction-protocols.json and tools/contracts/artifact-contracts.md; these are shared application rules. Approved R02 lifecycle supersedes historical draft labels in source artifacts.

Coordinate WF01-WF06 using tools/contracts/workflows.json. Preserve six outcomes and all applicable HITL checkpoints. D03 is mandatory before marking an artifact approved or reusing an approval. Do not infer confirmation from permission to continue a discussion. Record exact artifact/version/hash/scope and explicit owner evidence. On resume, report retained state and missing context rather than inventing it.

Before substantive methodology, invoke the sibling consulting-design-references Skill and read the applicable resource bodies it owns. Record actual consultation. This delegation is source retrieval, not a claim that an index or hash check read a body.

Required deterministic paths use bundled design-integrity via direct argv {python} -B tools/design_integrity.py from the installed plugin root, except D04 uses the approved export workspace as cwd and the resolved bundled script path. Read plugin-root tools/design-integrity-contract.json and tools/operation-guide.md before calling. Send {"operation":"D01|D02|D03|D04","input":{...}} as JSON stdin and return parsed JSON stdout to this Skill before interpreting it. Errors/absent execution block the affected path; do not guess a result. No remote MCP service or network permission. Python 3.10+ and host access to installed files/execution must be available; never assume a local test proves installed execution. DEFERRED_ALLOWED installed evidence stays NOT VERIFIED until observed.

Preserve user pause/resume/stop and version-specific confirmation; follow the shared safety/input/source gates. End with the artifact version/state, confirmed scope, unresolved limits and appropriate next step. Do not claim target-platform configuration or runtime success from design text.
