# Software Design Specification

## 1. Executive Summary
Local command-line log analyzer.
## 2. Goals and Non-goals
Analyze logs; no graphical interface.
## 3. Users and Actors
Operator.
## 4. Use Cases
Analyze one file.
## 5. Software Form and Boundaries
CLI with local filesystem input.
## 6. Interfaces
`analyze PATH`; JSON output; exit codes 0 and 2.
## 7. Architecture
Parser and reporter components.
## 8. Data and Persistence
No persistence.
## 9. Services and Integrations
None.
## 10. Workflows
Read, parse, summarize, return.
## 11. Quality Attributes
Deterministic output and bounded memory.
## 12. Security and Privacy
Never transmit log content.
## 13. Validation and Acceptance
Golden-file and malformed-input tests.
## 14. Assumptions and Open Questions
UTF-8 input unless overridden.
