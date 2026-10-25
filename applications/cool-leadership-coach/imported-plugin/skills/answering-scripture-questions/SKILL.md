---
name: answering-scripture-questions
description: Verify Scripture passages and distinguish text from interpretation.
---

# Answering Scripture Questions

IM-05 / WF-S and Scripture support for other workflows. Inputs: requested passage, edition and quote/explanation intent. Do not force a ten-step study. Read the Bible inventory through the `explaining-source-evidence` Skill (invoke it and read its actual resources), then locate the actual passage and enough surrounding text in the retained New Testament through the `explaining-source-evidence` Skill (invoke it and read its actual resources) or Old Testament through the `explaining-source-evidence` Skill (invoke it and read its actual resources).

Use available host PDF/resource reading and page search. Verify book/chapter/verse against the actual page and ensure contiguous requested verses. Record PDF identity, physical page and passage; a remembered wording or search hit alone does not verify exact quotation. For unreadable extraction consult the original page view if available. Never guess OCR characters, verse boundaries or missing passages. No specific PDF tool or installed Python dependency is promised by this Skill.

Return the verified requested verses with translation/passage and concise context when helpful. For interpretation read appropriate IBS card bodies through index through the `explaining-source-evidence` Skill (invoke it and read its actual resources) and cards through the `explaining-source-evidence` Skill (invoke it and read its actual resources); separate biblical text, textual observations, interpretation and application. Maintain baseline orthodox Christian commitments (Trinity, Christ's saving work, Scripture interpreting Scripture), respectfully explaining differences without coercion or assuming denomination.

If exact text cannot be accessed, disclose that quotation is unverified and offer a clearly marked paraphrase or ask for the source passage; never fabricate a quotation or read success. Do not silently switch edition/provider. Outcomes ANSWERED/LIMITED/BLOCKED; optional study only if requested. Both PDFs carry PUBLIC_DOMAIN—OWNER DECLARATION, not independent edition clearance.

Before substantive use, read source governance through the `explaining-source-evidence` Skill (invoke it and read its actual resources) and conversation safeguards in APPLICATION-INVARIANTS.md in the plugin root. Follow the session router through the `guiding-leadership-sessions` Skill (invoke it and read its actual resources). Use the host's available file/resource reading capability; these Skills do not register a callable tool, create a server, or grant network access. If the host cannot expose the packaged file, report the gap and apply the bounded fallback. Do not infer tool availability from a local build test.
