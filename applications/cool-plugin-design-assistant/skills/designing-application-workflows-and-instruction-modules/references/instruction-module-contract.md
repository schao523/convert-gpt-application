# Instruction Module contract

An Instruction Module is a behavior-level responsibility that supports an
application outcome. It may participate in an ordered workflow, respond to a
recognizable intent, or apply across multiple workflows. It is not a deployable
unit and does not imply one-to-one implementation.

Classify each module as:

- `primary-workflow` — participates in the ordered or stateful mission path;
- `intent-triggered` — activates for a recognizable user goal inside or outside
  the primary workflow; or
- `cross-cutting` — applies across stages, such as safety, HITL, language,
  evidence, uncertainty, or confirmation policy.

## Required fields

- stable `module_id` and human-readable `name`;
- `classification` using one category above;
- `purpose` and supported `mission_outcome`;
- triggering intent or workflow condition;
- required and optional inputs;
- preconditions;
- behavioral procedure;
- outputs;
- named user-interaction protocol;
- transitions to other logical modules;
- stop, wait, and completion conditions;
- error and recovery behavior;
- safety boundaries;
- Reference Material requirements at behavior level; and
- acceptance criteria.

No field assigns the module to a Skill, folder, prompt, tool, runtime adapter,
data store, or packaged reference path. The Application Workbench may combine
several modules in one Skill, split a module across Skills and tools, or choose
another conforming architecture.
