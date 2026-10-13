# Implementation Architecture Decision

REQ-019 is implemented as a Workbench-owned architectural decision, not an application Skill responsibility.

The approved behavioral specification does not prescribe Skill count, Skill names, folder layout, collaboration, reference-to-Skill binding, runtime adapters, storage architecture, RAG, MCP implementation, API clients, programming language, or physical schema. The candidate therefore derives a six-Skill architecture from implementation responsibilities and verification needs. This document records that the six-Skill decomposition is an implementation decision and must not be interpreted as canonical application behavior.

REQ-028 remains behaviorally implemented through capability-oriented target adaptation: provider-specific target behavior is derived from capability evidence rather than hard-coded as canonical creative behavior.
