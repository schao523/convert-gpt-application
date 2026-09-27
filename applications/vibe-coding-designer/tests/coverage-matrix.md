# Vibe Coding Designer coverage matrix

| Requirement | Evidence |
| --- | --- |
| General software forms; Web GUI conditional | `test_skill_contracts.py` |
| Eleven-stage guided intake | `test_skill_contracts.py` |
| Fourteen-section specification | `test_skill_contracts.py`, `test_tools.py` |
| Exact workflow-map validation | `test_tools.py` |
| Explicit-only coverage calculation | `test_tools.py` |
| Skills-only no-RAG distribution | `test_distribution.py` |
| Deterministic OpenClaw package | `test_distribution.py` |
| HOD-001 strict create/update identity and version contracts | `test_hosted_deployment.py` |
| HOD-002 complete create or update archive; no merge dependency | `test_hosted_deployment.py` |
| HOD-003 exact mapping, skill closure, explicit-only policy | `test_hosted_deployment.py` |
| HOD-004 deterministic text and binary handling | `test_hosted_deployment.py` |
| HOD-005 redistribution and adapter provenance | `docs/source-decisions.md`, `test_hosted_deployment.py` |
| HOD-006 deterministic archive and report hashes | `test_hosted_deployment.py` |
| HOD-007 complete-archive verification without retention claims | `test_hosted_deployment.py` |
| HOD-008 hostile archive identity-import boundary | generic framework tests |
| HOD-009 approved identity record for update | `tests/fixtures/hosted-identity.json`, `test_hosted_deployment.py` |
| HOD-010 capability declaration closure | `test_hosted_deployment.py` (no non-instruction capability) |
| HOD-011 local and hosted execution evidence remain separate | `test_hosted_deployment.py` |
| HOD-012 independent distribution-channel status | `test_hosted_deployment.py` |
| HOD-013 transactional output replacement | generic framework tests |
| HOD-014 non-interactive machine-readable operation | generic framework CLI tests |
| HOD-015 no private paths, credentials, or generated local data | `test_hosted_deployment.py` |
| HOD-016 application-owned canary and general-software behavior | `test_hosted_deployment.py` |
| HOD-A27 seven native skills plus explicit-only compatibility router | `test_hosted_deployment.py` |
| HOD-A28 update identity, advanced version, no forced Web GUI | `test_hosted_deployment.py` |
| HOD-A29 adapter-only manifests and compatibility routing | `test_hosted_deployment.py` |
