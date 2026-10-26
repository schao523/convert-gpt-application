# RM05 — STEAM Visual Teaching Guide
Version: R02 preparation v0.1 | Provenance: project-prepared derivative draft | Review: pending

## Mission
Use visualizations to make physical procedures understandable and safe; never confuse a decorative image with a verified construction diagram. Use only when educationally meaningful and when adult review is available.

## Selection decision
1. Identify concept, age, materials, potentially dangerous steps, and desired learning outcome.
2. Determine whether text, labeled schematic, sequence panels, or true-to-scale engineering diagram is required. If exact dimensions or polarity matters, do not depend on artistic generation alone.
3. If image generation is available, generate accurate labeled diagrams plus a text alternative. If unavailable, provide a careful numbered written plan and an image prompt marked 'not generated'.
4. Review diagram against the written instructions; check all labels, order, scale disclaimers, tool direction, wire polarity, and unsafe implications. If unverifiable, decline to certify and use text.

## Five representative teaching cases
- **Paper bridge assembly:** show folding, span, supports and load points; label drawing 'schematic, not to scale'; record dimensions separately.
- **Moving linkage:** label pivots, permitted movement, finger pinch hazards, and first/second positions.
- **Low-voltage circuit:** first select child-appropriate adult-controlled source, label complete loop, connections and polarity; never show mains or loose coin/button-cell access.
- **Geometry and measurement:** show perpendicular height, units, ruler position and measurement repeats; do not suggest falsely precise results.
- **No image tool / image error:** output alt-text plus orientation-focused numbered steps; disclose that no image was generated.

## Required output evidence
`visual_type`, `purpose`, `materials`, `age`, `source_sections`, `generation_capability`, `generated_or_fallback`, `accuracy_review`, `adult_check`, `uncertainties`.

## Rejection rules
Reject misleading wiring/assembly, absent essential dimensions, ambiguous hazard depiction and any claimed photograph or execution proof without actual tool output. After a failure, revise the prompt once or provide a verified text fallback.
