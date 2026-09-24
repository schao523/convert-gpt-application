# User-interaction protocols

A user-interaction protocol is a named behavioral contract for communication
within a workflow stage or Instruction Module. It is not Skill routing, folder
structure, runtime UI wiring, or technical Reference Material loading.

Define for each protocol:

- mode: `direct`, `guided`, `Socratic`, `co-creative`, or `evaluative`;
- what information is required and what may be assumed provisionally;
- what to ask and a numeric per-turn question limit (default to one focused
  consequential question when no stronger need is established);
- the exact condition that requires a wait;
- when two or three materially different alternatives should be offered;
- which decision requires explicit confirmation;
- how incomplete, ambiguous, or conflicting answers are labeled and resolved;
- how the user may revise, skip, pause, resume, or stop;
- what state is summarized before progression or resume;
- transition guards and the state preserved across each transition; and
- when a draft may be generated, revised, finalized, or marked approved.

## Protocol rules

Do not combine unrelated consequential questions merely to appear compliant
with the numeric limit. Wait after the question or checkpoint. A skip may leave
an optional item unresolved but cannot bypass a safety boundary, required input,
or approval gate. On pause, preserve current stage, confirmed decisions,
artifacts, assumptions, and the next unresolved decision. On resume, restate
that state before continuing. On stop, name the terminal state and do not
silently progress.

When answers conflict, show the conflict, identify the affected transition or
output, and ask which statement governs. Keep provisional output in `draft`.
Finalization requires the protocol's stated completion evidence and every
applicable explicit confirmation.
