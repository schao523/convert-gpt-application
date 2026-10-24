# Knowledge Conversion & New Guide Quality Acceptance — DRAFT R02

## Scope & identity
- Source ZIP contains one Instructions DOCX plus five knowledge files, of which Game Framework `.md` and `.docx` duplicate one conceptual source. Preserve source inventory with SHA-256 and provenance.
- Normalize **all operational professional knowledge artifacts to `.md`**: RM01–RM04 original substantive knowledge and RM05–RM08 new guides. No `.docx` as authoritative deployed knowledge. System instructions are separately versioned and may be converted to Markdown for specification traceability without being counted as a ninth knowledge guide.
- RM02 must use original Game Design Innovation Framework.md as authority; compare DOCX for divergence but do not automatically merge differences.

## Conversion checks (QC01–QC10)
1. QC01 100% source-member inventory, hash, size, mapping to target and supersession state; no anonymous losses.
2. QC02 preserve every source heading, substantive paragraph, ordered list, table cell, formula, citation marker, footnote and defined label; diff exceptions documented and approved.
3. QC03 count **15** original STEAM template items including #10 Elastic Catapult; validate numbered identifiers and no synthetic gap-fill.
4. QC04 compare Framework DOCX and MD; record every substantive divergence; original `.md` controls; DOCX remains provenance-only.
5. QC05 preserve meaning of embedded media, figures, diagrams in DOCX via extracted usable approved assets or exact caption/alt-text with explicit `asset unresolved` notation; images not silently dropped. For 数字探险竞技场, check its 2 tables and embedded illustration slots.
6. QC06 all final knowledge files valid UTF-8 `.md`, readable headings/tables, stable IDs, version, authority/provenance and usage scope; no `.md.md` operational filename.
7. QC07 compare logical/source sections manually + deterministic counts; machine count equivalence alone insufficient. Report any paraphrase or change of technical meaning.
8. QC08 re-evaluate hazards by age/material in each activity; never silently preserve unsafe directions as recommended instruction. Keep original text in audit reference if amended.
9. QC09 check rights individually: inspect/convert/derivative/quote/distribute distinct states; external references verified when relied on; no rights assumed because contained in ZIP.
10. QC10 produce traceable acceptance report with pass/fail, original-to-target coverage, exceptions, reviewer and dates. Gate canonical handoff on required checks.

## New-guide acceptance (NG01–NG04)
- NG01 Visual Teaching: >=5 representative use cases incl. structural assembly, mechanism, circuit, geometry/measurement, safe fallback; labels, orientation, uncertainty, age and image fidelity checks.
- NG02 Game Creation: complete conversion from educational design to executable behavior with target platform constraints, rules/states/transitions, assets, accessibility, seed/data controls, errors, testable deliverables, printable/web/advanced branches and complete fallback handoff.
- NG03 Playtest & Evaluation: separate functionality, usability, age fit and learning evidence; observable measures, consent/privacy, pre/post or comparative tasks when appropriate, change requests and re-test.
- NG04 Safety & Age: physical and digital hazard matrix (button cells, scissors/pins, heat, projectiles, electricity, privacy, rewards, social features), adult supervision, safer substitutes, age/maturity and accessibility gates, stop/escalation conditions.
- Each new guide: project-authored status only if genuinely created by project; cite/adjudicate incorporated external claims; version and reviewer recorded. Proposed new guides are **not represented as already written or validated**.

## Release gates
- Mandatory-source availability and proper rights decisions are required before packaging; inaccessible sources trigger failure records rather than false provenance.
- Separate conversion validation, content validation, game functional tests, image accuracy check and child-safety review. Each has its own evidence; none implied by creating a ZIP.
