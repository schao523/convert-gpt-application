# Knowledge Reference Policies Design

## 1. Executive Summary

The Conversion Workbench needs to preserve two distinct uses of packaged
knowledge without introducing a large knowledge-policy subsystem:

- professional knowledge must govern the skill or workflow that owns it; and
- general knowledge must be discoverable through a topic guide and consulted
  when it materially improves a response.

This design uses skill-local conventions rather than a new plugin-root
`knowledge/` directory or application-configuration schema. Professional
knowledge remains under the owning skill's `references/` directory. General
knowledge is owned by one application-specific consultation or router skill,
also under its `references/` directory, and is indexed by
`knowledge-index.json`.

One user request may use multiple skills. A domain or orchestration skill owns
the final response; a general-knowledge skill supplies relevant reference
material and does not issue a separate competing response. Mandatory
application-owned behavioral tests distinguish knowledge that is merely
packaged from knowledge that is actually used.

## 2. Goals and Non-goals

### Goals

- **KRP-001:** Ensure that professional reference files are linked, consulted,
  and behaviorally exercised by the skill that owns them.
- **KRP-002:** Ensure that every general knowledge file is discoverable through
  a topic guide containing purpose, topics, chapters, sections, keywords, and
  page ranges.
- **KRP-003:** Keep all model-readable knowledge inside standard skill-local
  `references/` directories for Codex and OpenClaw portability.
- **KRP-004:** Support composition of multiple skills while producing one
  coherent response with one explicit response owner.
- **KRP-005:** Keep validation non-interactive, application-aware, and
  machine-readable.
- **KRP-006:** Distinguish structural presence, deterministic discovery, runtime
  consultation, and behavioral application as separate evidence layers.
- **KRP-007:** Reuse the existing application coverage matrix, product test
  suite, runtime verification, packaging, and readiness mechanisms.
- **KRP-008:** Preserve exact structured retrieval and optional semantic RAG as
  separate application capabilities rather than making either mandatory.

### Non-goals

- Creating a plugin-root `knowledge/` directory.
- Adding a general knowledge section to distribution-contract schema v3.
- Creating application-configuration schema v3 solely for knowledge policy.
- Defining per-file trigger objects, authority graphs, fallback graphs, or
  retrieval-mode declarations.
- Requiring RAG for static reference material.
- Treating static link validation as proof of runtime use.
- Loading all general knowledge for every request.
- Replacing application-owned behavioral judgment with generic keyword tests.
- Changing the behavior or knowledge classification of an existing converted
  application without decision-owner approval.

## 3. Terminology

### Professional knowledge

Professional knowledge is authoritative material associated with a particular
skill. It supplies methods, policies, schemas, constraints, or domain guidance
that must govern the skill when relevant.

### General knowledge

General knowledge supplies broader background, context, explanations, and
examples. It is not bound to one domain workflow step, but it must remain
discoverable and must be consulted when it materially improves the answer.

### Response owner

The response owner is the skill responsible for the requested user outcome and
the final response. Supporting skills may provide knowledge, tools, validation,
or subordinate workflow steps, but they do not produce separate user-facing
answers.

### Consultation skill

The consultation skill is an application-specific skill that owns the general
knowledge topic guide and files. It selects and reads relevant general
knowledge for another skill or for a direct general-knowledge request.

## 4. Convention-based Architecture

### Professional knowledge layout

Professional knowledge lives with its owning skill:

```text
skills/
  <domain-skill>/
    SKILL.md
    references/
      <professional-reference>.md
```

Every file below this `references/` directory is professional knowledge unless
the same directory contains the plugin's `knowledge-index.json`, in which case
Section 4.2 applies to that skill.

The owning `SKILL.md` must directly link every professional reference and state
the condition under which it is read. The condition remains natural-language
workflow guidance in `SKILL.md`; it is not duplicated in another manifest.

### General knowledge layout

General knowledge lives under one application-specific consultation or router
skill:

```text
skills/
  consulting-<application-domain>-knowledge/
    SKILL.md
    references/
      knowledge-index.json
      <general-reference-1>.pdf
      <general-reference-2>.md
```

The exact skill name is application-owned and goal-oriented. The framework
does not require the literal prefix `consulting-`. A plugin has zero or one
general knowledge index. Multiple general knowledge files and domains may be
listed in that single index.

The consultation skill's `SKILL.md` must link `knowledge-index.json`, explain
when general knowledge is worth consulting, require selective reading, and
prohibit silent contradiction of consulted material.

### Classification by location

The Workbench applies these rules:

1. A reference beneath a normal skill is professional knowledge.
2. `knowledge-index.json` identifies its owning skill as the general knowledge
   consultation skill.
3. Other reference files beside that index are general knowledge and must be
   indexed.
4. Scripts remain deterministic operations, and assets remain output
   resources; neither is reclassified as knowledge merely because it is
   packaged with a skill.

This convention removes the need for a second application-owned knowledge
manifest.

## 5. Professional Knowledge Policy

When a professional reference's stated condition applies, the owning skill
must consult and apply it. General model knowledge may explain or connect the
material but may not replace, silently contradict, or override it.

If the required professional reference is missing, unreadable, incomplete, or
insufficient for the requested conclusion, the response owner must:

1. state the material limitation;
2. avoid presenting unsupported content as governed by that reference; and
3. request the missing input or offer a narrower supported result when useful.

The package and hosted verifiers must reject missing or broken reference links.
Behavioral evidence remains necessary because file presence and links do not
prove consultation or application.

## 6. General Knowledge Topic Guide

### File location and root shape

The topic guide is `references/knowledge-index.json` inside the consultation
skill. It uses this minimal schema:

```json
{
  "schema_version": 1,
  "files": [
    {
      "path": "software-architecture-guide.pdf",
      "purpose": "Background guidance for selecting and comparing software architectures.",
      "topics": [
        {
          "name": "Event-driven architecture",
          "chapters": ["Asynchronous System Design"],
          "sections": ["Events and message delivery", "Failure handling"],
          "keywords": [
            "event-driven",
            "message broker",
            "idempotency",
            "eventual consistency"
          ],
          "page_ranges": [
            {"start": 42, "end": 67}
          ]
        }
      ]
    }
  ]
}
```

Paths are POSIX-style paths relative to the consultation skill's
`references/` directory. They must remain confined to that directory.

### Required fields

Each file entry requires:

- `path`: a unique relative path to a packaged general knowledge file;
- `purpose`: a concise explanation of how the file can improve responses; and
- `topics`: one or more topic entries.

Each topic entry requires:

- `name`: the topic a user request may express;
- `chapters`: relevant chapter names, or an empty array when unavailable;
- `sections`: relevant section names, or an empty array when unavailable;
- `keywords`: one or more search or matching terms; and
- `page_ranges`: relevant physical page ranges, or an empty array for
  unpaginated or sufficiently short material.

Each page range contains positive integer `start` and `end` values with
`start <= end`. Page numbers mean physical document pages. If printed page
labels differ materially, the topic's section or chapter text supplies the
additional locator; the first schema does not add a second page-label system.

At least one of `chapters`, `sections`, or `page_ranges` should be populated
when the source has that structure. The validator does not invent missing
metadata.

### Consultation behavior

For a substantive request that may benefit from broader application knowledge,
the consultation skill must:

1. match the request against topic names and keywords;
2. select only relevant file entries;
3. use chapters, sections, and page ranges to narrow reading;
4. consult the selected portions before supplying knowledge to the response
   owner; and
5. report uncertainty or unavailable material when it materially affects the
   answer.

General model knowledge may complement missing context, but it may not silently
contradict consulted general references. When no indexed topic is relevant, the
model may proceed without loading general knowledge.

## 7. Multi-skill Composition

One user request may activate or explicitly invoke multiple skills. The
workflow must still produce one response.

### Ownership rules

- The skill matching the user's requested deliverable is the response owner.
- An orchestration skill may remain the response owner while routing domain
  work to focused sibling skills.
- The consultation skill supplies knowledge to the response owner.
- A supporting skill does not repeat the full request, issue a separate final
  answer, or redefine approved decisions.
- If two skills prescribe incompatible output contracts, the response owner
  stops and resolves or exposes the conflict rather than silently combining
  them.

### Required versus optional composition

Model-directed implicit activation is useful but is not sufficient for a
required dependency. When a domain workflow requires professional knowledge,
another skill, exact retrieval, or general knowledge consultation, its
`SKILL.md` must route explicitly to the required reference or supporting skill.

For general knowledge, the response owner should invoke the consultation skill
when the topic guide is likely to materially improve completeness, accuracy,
context, or examples. It should not invoke it merely because the plugin contains
general knowledge.

## 8. Static Validation

Static validation reports structure, not behavior. It must check:

### Professional knowledge

- every professional reference is a confined regular file;
- every professional reference is directly linked from its owning `SKILL.md`;
- every local Markdown link resolves inside the packaged skill;
- no professional reference exists only as an unlinked packaged file; and
- the generated Codex and OpenClaw artifacts contain the expected reference
  bytes.

### General knowledge

- zero or one `knowledge-index.json` exists in the plugin;
- the index is valid UTF-8 JSON with `schema_version: 1`;
- every index path is safe, unique, confined, and present;
- every non-index file in the consultation skill's `references/` directory is
  indexed exactly once;
- every file has a nonempty purpose and at least one topic;
- every topic has a name, the four required locator arrays, and at least one
  keyword;
- every page range is valid;
- the consultation skill directly links the index; and
- no plugin-root `knowledge/` directory is introduced by the conversion.

Static success is `STATICALLY VERIFIED`. It must not be reported as runtime
consultation or behavioral equivalence.

## 9. Behavioral Evidence

Behavioral testing is mandatory and application-owned. The existing coverage
matrix records each knowledge file, its owning skill or consultation route,
its scenario evidence, and its status. No second evidence manifest is added.

### Professional knowledge scenarios

Every professional reference must have at least one scenario whose observable
pass criteria depend on a distinctive rule, method, constraint, or conclusion
from that reference. A link check or assertion that the filename appears in
`SKILL.md` is insufficient.

The scenario set must also cover required knowledge being unavailable or
insufficient and verify that the response exposes the limitation rather than
substituting an unsupported answer.

### General knowledge scenarios

Every general knowledge file must have at least one scenario that:

1. matches a topic or keyword from the index;
2. locates the intended file and relevant chapter, section, or page range;
3. demonstrates an observable contribution from the consulted content; and
4. produces one coherent response through the response owner.

At least one negative-control scenario must verify that an unrelated request
does not cause irrelevant general knowledge to be loaded or echoed.

### Cross-runtime evidence

Representative professional, general, combined-skill, unavailable-knowledge,
and negative-control scenarios must run against generated or installed Codex
and OpenClaw artifacts. Results remain separate per runtime. Passing source
tests does not establish installed-artifact behavior.

## 10. Evidence Model and Readiness

Knowledge evidence is reported in layers:

| Layer | Evidence | Maximum state |
| --- | --- | --- |
| Package structure | Files, index, links, paths, schema, manifest bytes | `STATICALLY VERIFIED` |
| Deterministic discovery | Topic and keyword lookup locates intended entries | `STATICALLY VERIFIED` |
| Codex consultation | Installed Codex scenario uses expected knowledge | `RUNTIME VERIFIED` |
| OpenClaw consultation | Installed OpenClaw scenario uses expected knowledge | `RUNTIME VERIFIED` |
| Cross-runtime behavior | Observable outcomes satisfy the same application invariant | `RUNTIME VERIFIED` |

A plugin with applicable knowledge cannot be `READY` when either runtime lacks
the required behavioral evidence. It must retain the repository's established
pending-validation language and portability classification.

## 11. Retrieval and RAG Boundaries

The topic guide is the default discovery mechanism for packaged general
knowledge. RAG is optional and justified only by application scale or retrieval
needs.

- Exact identifiers and quotations continue to use exact structured retrieval.
- Semantic RAG may help discover relevant material but does not establish exact
  wording or authority.
- When RAG is used, the existing application identity, namespace, model,
  ingestion, index, rights, and setup contracts remain in force.
- General knowledge consultation must retain a documented fallback when the
  source application's behavior permits operation without optional RAG.

## 12. Distribution and Rights

Knowledge role does not imply redistribution permission. All professional and
general files remain subject to the existing source inventory, provenance,
rights decision, distribution allowlist, content policy, secret audit, and
deterministic build rules.

The distribution contract continues to classify bytes as text or binary and to
record approved redistribution evidence. Knowledge role is inferred from the
skill-local layout and is not added to distribution schema v3.

## 13. Failure Semantics

The generic validator uses stable machine-readable conditions, including:

- `professional_reference_unlinked`;
- `professional_reference_missing`;
- `general_knowledge_index_invalid`;
- `multiple_general_knowledge_indexes`;
- `general_knowledge_file_unindexed`;
- `general_knowledge_index_path_missing`;
- `general_knowledge_topic_incomplete`;
- `general_knowledge_page_range_invalid`; and
- `plugin_root_knowledge_directory_forbidden`.

Malformed, unsafe, missing, or contradictory declarations are `FAIL`.
Application behavior without required runtime evidence is `NOT VERIFIED`, not
`PASS`. The validator does not repair the topic guide or invent metadata.

## 14. Compatibility and Adoption

Existing plugins without general knowledge do not need a
`knowledge-index.json`. Their existing skill references become professional
knowledge under this convention only after the application owner approves the
classification and the coverage matrix supplies the required behavioral
evidence.

Adoption is therefore explicit per application. The framework must not make an
existing plugin fail merely because it has historical `references/` files
before that application's migration is approved. New conversions use this
design by default. Migrated applications add the new knowledge validation gate
to their application verification profile.

## 15. Test Strategy

Framework tests cover:

- professional reference discovery and direct-link closure;
- valid and invalid general topic guides;
- missing, duplicate, escaping, and unindexed paths;
- required fields and page-range validation;
- zero-index and multiple-index applications;
- absence of a plugin-root `knowledge/` directory;
- canonical behavior on Windows, Linux, and macOS paths; and
- unchanged legacy applications until explicitly migrated.

Application tests cover:

- one behavior scenario per professional reference;
- one discovery-and-use scenario per general file;
- missing or insufficient professional knowledge;
- irrelevant general knowledge negative control;
- multi-skill composition with one response owner;
- Codex installed-artifact execution;
- OpenClaw installed-artifact execution; and
- cross-runtime invariant comparison.

Package and marketplace tests confirm that topic guides and reference files are
present, deterministic, rights-approved, and byte-identical to the verified
application artifacts.

## 16. Acceptance Criteria

The design is implemented when:

1. new conversions can adopt the convention without an application-schema or
   distribution-schema change;
2. professional references cannot pass static validation while orphaned or
   broken;
3. every general file is covered by a valid topic guide with purpose, topics,
   chapters, sections, keywords, and page ranges;
4. the general consultation skill composes with response-owning skills without
   producing multiple answers;
5. application coverage matrices trace every knowledge file to behavioral
   evidence;
6. installed Codex and OpenClaw scenarios distinguish presence from actual use;
7. optional RAG and exact retrieval retain their existing separate contracts;
8. deterministic builds and marketplace verification continue to pass; and
9. no application is declared `READY` from static knowledge validation alone.
