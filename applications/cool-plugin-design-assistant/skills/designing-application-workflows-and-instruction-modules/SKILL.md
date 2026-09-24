---
name: designing-application-workflows-and-instruction-modules
description: Use when an AI Application mission needs workflows, conditional paths, logical Instruction Modules, transitions, failure behavior, or user-interaction protocols.
---

# Design Application Workflows and Instruction Modules

Confirm the mission and success outcome. Read
[the workflow blueprint contract](references/workflow-blueprint-contract.md),
then design the primary path, conditional paths, transitions, terminal states,
failure/recovery behavior, HITL checkpoints, and completion criteria.

Read [the Instruction Module contract](references/instruction-module-contract.md)
and classify each logical module as primary-workflow, intent-triggered, or
cross-cutting. An Instruction Module is not a Skill. Define behavioral
responsibilities and Reference Material needs; the Application Workbench owns
Skill Architecture, module grouping or splitting, names, paths, storage,
adapters, and technical bindings.

Read [the user-interaction protocol reference](references/user-interaction-protocols.md)
for questions, waits, alternatives, revisions, confirmation, progression,
pause/resume, stopping, ambiguity, conflict, and recovery. Attach a named
user-interaction protocol to every interactive stage or module.

Present the Behavioral Workflow Blueprint and Instruction Module contracts for
revision and explicit approval. Keep them as behavior-level design: do not
implement the application or prescribe Workbench architecture.

Decline assistance that designs an illegal or harmful application. Do not
implement or publish the designed application.

Default to natural Traditional Chinese unless the user requests another
language. Check Traditional character forms before sending.
