---
name: adapting-platforms-and-delivering-packages
description: Adapt portable instructions to selected platforms and deliver setup packages.
---

# adapting-platforms-and-delivering-packages

Read the applicable [module contracts](references/module-contracts.json) in full. Follow the plugin-root tools/contracts/application-policy.md, tools/contracts/workflows.json, tools/contracts/interaction-protocols.json and tools/contracts/artifact-contracts.md; these are shared application rules. Approved R02 lifecycle supersedes historical draft labels in source artifacts.

Read RM10/RM13 through consultation; RM10 is general historical guidance, never current Builder UI evidence. Identify target and use context before adaptation; unknown target permits only pending-target portable draft. Profile includes instruction field/scope/length and measurement, source availability, tools, memory, sharing and account/interface constraints, dated evidence and unknown values. Do not infer source files grant system authority. Deliver CustomInstructionDesignPackage with portable_core, selected_platform_variants, target_capability_profiles, role/goal, modules, interaction blueprint, resources and conditional usage map, launch examples usable as first-chat prompts, setup/validation guide, differences/limitations, tests, versions and explicit confirmation scopes. Separate core and platform variant approval/testing. WF06 switches platform without invalidating unaffected core. Run D02 against the actual typed requirements/modules/resources/workflows/tests and links; unresolved findings block claiming complete coverage. Run D04 on the exact rights-approved export files for reproducible manifest hashes. It does not verify behavior. Human user sets up/tests/shares on the target platform.

Before substantive methodology, invoke the sibling consulting-design-references Skill and read the applicable resource bodies it owns. Record actual consultation. This delegation is source retrieval, not a claim that an index or hash check read a body.

Required deterministic paths use bundled design-integrity via direct argv {python} -B tools/design_integrity.py from the installed plugin root, except D04 uses the approved export workspace as cwd and the resolved bundled script path. Read plugin-root tools/design-integrity-contract.json and tools/operation-guide.md before calling. Send {"operation":"D01|D02|D03|D04","input":{...}} as JSON stdin and return parsed JSON stdout to this Skill before interpreting it. Errors/absent execution block the affected path; do not guess a result. No remote MCP service or network permission. Python 3.10+ and host access to installed files/execution must be available; never assume a local test proves installed execution. DEFERRED_ALLOWED installed evidence stays NOT VERIFIED until observed.

Preserve user pause/resume/stop and version-specific confirmation; follow the shared safety/input/source gates. End with the artifact version/state, confirmed scope, unresolved limits and appropriate next step. Do not claim target-platform configuration or runtime success from design text.
