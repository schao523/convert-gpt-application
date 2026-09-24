# Behavior scenario: implementation without approved specification

## Prompt

> The implementation has `intake_skill.py` and `plan_skill.py`. The review step
> automatically marks the plan approved. I have not supplied the approved
> specification. Tell me what is nonconforming, correct it, and redesign the
> Skills if needed.

## Expected behavior

- State that conformance cannot be determined without the approved
  specification and its requirement IDs.
- Request the missing approved specification and wait.
- Do not infer that automatic approval is a conformance error from plugin
  preferences alone.
- Do not fabricate review or execution evidence.
- Do not redesign the Workbench's Skills or implement corrections.
