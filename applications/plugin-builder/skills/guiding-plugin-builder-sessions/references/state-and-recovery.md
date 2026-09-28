# State and recovery

Persist only the minimum local state required to resume:

- application identity and approved specification digest;
- explicit create/update mode and relative baseline identity when applicable;
- current workflow state and recorded W1/W2 decisions;
- requirement coverage, candidate identity, and evidence rows;
- unresolved decisions and relative artifact locations.

Do not persist private absolute source paths, credentials, conversation history, or source document contents when a digest and relative identifier suffice.

On pause, stop all mutation and record `H1_PAUSED`. On resume, validate the state schema and referenced identities, summarize completed work and unresolved decisions, then return to the recorded state. If an identity changed or state is corrupt, do not guess; return to intake or the last independently verified checkpoint. On cancel, mark `E2_CANCELLED` and create no artifact.
