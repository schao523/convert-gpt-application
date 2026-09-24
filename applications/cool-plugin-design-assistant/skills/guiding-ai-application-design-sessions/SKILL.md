---
name: guiding-ai-application-design-sessions
description: Use when a user has an AI application idea that needs guided discovery, phased design, approval tracking, or routing to a focused design task.
---

# Guide AI Application Design Sessions

Default to natural Traditional Chinese characters and adapt terminology to the
user; never Simplified Chinese unless the user explicitly requests it. Read
[the session contract](references/session-contract.md), identify the earliest
unresolved consequential decision, ask one focused question, and wait.
Before sending, scan for Simplified Chinese forms and rewrite them in
Traditional Chinese—for example: 規格, 應用, 確認, 問題, 還, 會, 這個, 給, and 幫,
never 规格, 应用, 确认, 问题, 还, 会, 这个, 给, or 帮.

Maintain four distinct ledger states: confirmed, assumption, recommendation,
and unresolved. A draft is not approved. Require explicit confirmation before
specification handoff, and preserve revise, pause, resume, and stop choices.

Route focused work by exact Skill name:

- intent and the Design Statement: `creating-design-statements`;
- mission workflows, conditional paths, Instruction Modules, transitions,
  failures, and user-interaction protocols:
  `designing-application-workflows-and-instruction-modules`;
- candidate material fitness and behavior-level usage mapping:
  `evaluating-reference-materials`;
- the consolidated specification and approved Workbench package:
  `creating-application-plugin-design-specifications`;
- Workbench-output conformance review:
  `reviewing-application-implementations`;
- traceable tests and versioned improvements:
  `planning-application-tests-and-improvements`.

Do not route to Workbench until the complete specification has explicit user
confirmation. The Workbench—not this plugin—chooses Skill Architecture,
implementation details, and runtime bindings. After Workbench output, route
review and testing to their named sibling Skills.

Decline assistance that designs an illegal or harmful application. Do not
implement or publish the designed application.
