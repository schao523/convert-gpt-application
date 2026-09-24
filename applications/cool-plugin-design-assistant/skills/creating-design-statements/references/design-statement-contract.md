# Design Statement contract

A Design Statement is a short intent artifact, not a condensed implementation
specification. It carries only these fields:

| Field | Meaning |
| --- | --- |
| `audience` | The people or role the application serves. |
| `context` | The situation in which they use it. |
| `problem` | The difficulty or unmet need to address. |
| `application_role_or_method` | How the application is expected to help, at an intent level. |
| `desired_outcome` | The observable change or result the audience should obtain. |
| `style_and_tone` | Material communication expectations; otherwise `not material`. |
| `version` | A stable revision label such as `v1` or comparison labels `v1-A` and `v1-B`. |
| `state` | Exactly `draft` or `approved`. |

## Missing information

Treat a missing field as consequential when different plausible values would
change the application's mission, audience, scope, or success outcome. Ask one
focused question and wait. If the user insists on a provisional artifact,
state the missing field, label the chosen value as an assumption, keep the
artifact in `draft`, and offer a direct revision point. Never describe an
invented value as user-supplied or confirmed.

A problem statement describes today's difficulty; a desired outcome describes
the observable change or possibility that counts as success. Do not treat a
restatement or the obvious inverse of the problem as a confirmed outcome. If
the user has not supplied that success condition, ask for it or label the
derived value as an assumption inside the Design Statement itself.

## Canonical persisted artifact

A conversational preview may be one compact paragraph. The version that is
saved, validated, approved, or handed off uses this canonical persisted
artifact shape, with every section non-empty:

```markdown
# Design Statement

Version: v1
State: draft

## Audience
...

## Context
...

## Problem
...

## Application role or method
...

## Desired outcome
...

## Style and tone
...
```

Use the English field headings exactly so deterministic validation remains
portable; write each field value in the user's requested language. When
comparison helps, provide two or three materially distinct candidates and
briefly name the tradeoff; do not multiply cosmetic wording variants. After
drafting, offer `confirm`, `revise`, `compare`, or `combine`.

Only explicit user confirmation changes `state` from `draft` to `approved`.
Approval applies to the identified version and does not approve a later
specification, Workbench handoff, implementation, or publication.

## Separation boundary

Do not embed detailed workflows, conditional paths, Instruction Module
contracts, reference-material mappings, tools, data models, test plans, Skill
Architecture, runtime bindings, or distribution choices. Those belong to later
behavioral design, specification, or Workbench phases.
