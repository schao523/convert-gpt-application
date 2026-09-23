# Developing and Publishing Plugins of Skills

## Technical reference for Custom GPT conversion, packaging, testing, and marketplace publication

This technical reference explains how Codex or a plugin developer converts the system instructions and reference documents of a Custom GPT into a reusable plugin of skills, validates the result, packages it safely, and prepares it for a GitHub-hosted marketplace. It uses examples from `cool-bible-tutor` and `vibe-coding-designer`, but neither product is a generic template.

If you are the GPT owner and want a guided, nontechnical workflow, begin with the [Custom GPT to Plugin User Guide](GPT_TO_PLUGIN_USER_GUIDE.md). That guide focuses on what you need to prepare, the decisions Codex will ask you to make, example prompts and replies, and the approvals required before building or publishing. Return here only for implementation details, schemas, commands, audits, or troubleshooting.

This file is the specialized reference for designing, authoring, and reviewing
skills and plugin structure. The
[Plugin and Framework Command Reference](PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md)
is authoritative for the current framework CLI, packaging, verification, and
marketplace operations. The generic framework requires Python 3.11 or newer.
It uses distribution-contract schema v3 for new builds and the separate
application-configuration schema v2 for provenance and verification.

This reference assumes a source folder containing some combination of:

- a Custom GPT system-instructions document;
- uploaded knowledge or reference documents;
- starter prompts, descriptions, and branding notes;
- scripts, data files, or other supporting assets;
- no existing skill or plugin architecture.

The process is not a mechanical file conversion. A Custom GPT is usually one large prompt plus a flat collection of knowledge files. A good plugin turns that material into a tested set of recognizable workflows, with each instruction and resource loaded only when it is relevant.

## 1. Know what you are publishing

OpenAI currently distinguishes three related concepts:

1. A **skill** is a reusable workflow. It contains instructions and may include references, scripts, assets, and user-interface metadata.
2. A **plugin** is an installable package containing one or more skills, an MCP server, or both. Every plugin has `.codex-plugin/plugin.json`.
3. A **marketplace** is a source from which Codex can discover and install plugins during authoring, testing, or team distribution.

A skills-only plugin is valid. You do not need an MCP server when the original GPT needs only packaged instructions, local references, templates, and deterministic scripts. Use an MCP server when the workflow requires live remote data, authentication, authorization, or controlled actions against an external service.

OpenAI's current documentation makes an important publishing distinction:

- A local or GitHub repository marketplace is an authoring, testing, or team-distribution source.
- A public listing in the universal plugin directory shared by ChatGPT and Codex is submitted through the OpenAI Platform review process.

Pushing a marketplace repository to GitHub does **not** automatically submit the plugin to the universal directory. This guide covers the GitHub marketplace path first and the optional universal-directory path separately.

Official references:

- [Build skills](https://developers.openai.com/plugins/build/skills)
- [Package your plugin](https://developers.openai.com/plugins/build/plugins)
- [Build plugins in Codex](https://learn.chatgpt.com/docs/build-plugins)
- [Submit plugins for public review](https://developers.openai.com/plugins/deploy/submission)

## 2. The complete lifecycle

Use this lifecycle for a serious conversion:

1. Preserve and inventory the GPT source folder.
2. Extract the behavioral contract from the system instructions.
3. Catalog and normalize the reference documents.
4. Define user goals and a requirement coverage matrix.
5. Choose a skills-only or skills-plus-MCP architecture.
6. Design the skill boundaries and routing model.
7. Scaffold the plugin and skills.
8. Author concise `SKILL.md` files and progressively disclosed resources.
9. Add behavioral, structural, and distribution tests.
10. Create and validate the plugin manifest.
11. Validate distribution-contract schema v3 and build deterministic artifacts.
12. Prepare and verify a catalog-driven marketplace delta without mutating the baseline.
13. Install and test the staged marketplace version in new Codex and OpenClaw sessions.
14. After explicit approval, publish the reviewed marketplace change and retest it.
15. Separately authorize any GitHub Release, ClawHub publication, or universal-directory submission.

The order matters. Packaging a monolithic prompt before defining its workflows merely moves the original design problems into a new folder.

## 3. Case study: what the Cool Bible Tutor conversion started with

The source folder contained a Word document with the GPT identity, use case, description, starter questions, system instructions, mode detection, interaction protocol, response-handling rules, ten-stage study workflow, support modules, language policy, and theological safety rules. A separate resource index described the role of every uploaded reference file.

The source also contained:

- ten stage-specific Markdown guides;
- Word and PDF reference documents;
- Chinese Union Version Bible PDFs;
- later, retrieval, review, and semantic-discovery tooling;
- local authoring data that was never intended for public distribution.

The finished plugin did not become one giant `SKILL.md`. It became eight user-goal-oriented skills:

| Skill | Responsibility |
|---|---|
| `guiding-bible-tutor-sessions` | Detect the teaching mode, maintain the learner-paced interaction contract, and route to sibling skills. |
| `observing-biblical-passages` | Handle observation stages 1–4. |
| `interpreting-biblical-passages` | Handle interpretation stages 5–7. |
| `applying-biblical-truth` | Handle application stages 8–10. |
| `discussing-biblical-theology` | Guide Scripture-grounded Socratic theological discussion. |
| `supporting-biblical-exegesis` | Select focused literary, historical, grammatical, thematic, or redemptive context. |
| `comparing-biblical-words-and-translations` | Handle lexical, grammatical, and material translation questions. |
| `retrieving-chinese-union-version-scripture` | Retrieve and verify exact Chinese Union Version passages. |

The checked-in implementation can be examined at [`../applications/cool-bible-tutor/skills/`](../applications/cool-bible-tutor/skills/). Its requirement traceability is recorded in [`../applications/cool-bible-tutor/tests/coverage-matrix.md`](../applications/cool-bible-tutor/tests/coverage-matrix.md).

## 4. Phase 1: preserve and inventory the GPT source folder

### 4.1 Keep the source immutable

Do not edit the only copy of the GPT instructions or reference files while converting them. Keep the original source folder unchanged and perform normalization in a separate working area or Git repository.

Record at least:

- original filename;
- file type;
- purpose;
- owner or source;
- copyright or redistribution status;
- whether it contains instructions, knowledge, executable logic, generated data, or private data;
- checksum for release-sensitive source material;
- intended plugin destination, if any.

A useful inventory table looks like this:

| Source | Type | Role | Redistributable? | Planned destination |
|---|---|---|---|---|
| `GPT Instructions.docx` | Word | Behavioral contract | Usually yes, after owner review | Split among skills and references |
| `Resource Index.docx` | Word | Resource routing map | Usually yes | Development traceability only |
| `topic-guide.md` | Markdown | Detailed domain guidance | Verify | `skills/<skill>/references/` |
| `template.docx` | Word | Output template | Verify | `skills/<skill>/assets/` |
| `build-helper.py` | Python | Deterministic operation | Verify dependencies | `skills/<skill>/scripts/` or plugin `scripts/` |
| `private-index.sqlite3` | Database | Generated user data | Usually no | External runtime data directory |

### 4.2 Extract content without flattening meaning

For Word and PDF files, extract both text and structure. Preserve:

- headings and heading levels;
- numbered procedures;
- tables and labels;
- footnotes and source notes;
- distinctions such as “must,” “should,” “may,” and “example”;
- cross-references among files.

Do not treat OCR output as authoritative when the source can be read directly. For scanned documents, retain the page provenance and establish a human-review process for important extracted text.

### 4.3 Normalize filenames through a mapping, not silent renaming

Custom GPT source folders often contain inconsistent filenames. The Cool Bible Tutor resource index, for example, contained several spelling variants that did not exactly match the files on disk. Build a mapping table before writing skill links:

| Logical resource | Source spelling | Canonical filename |
|---|---|---|
| Identify relationships | `identify_relation_guide.md` / `identify_relationship_guide.md` | `relationships.md` |
| Examine structure | `examine_structre_guide.md` | `structure.md` |
| Answer questions | `answer_quesions_guide.md` | `answering.md` |

Every canonical link should be tested. Never depend on a model to guess a misspelled or renamed path.

### 4.4 Classify each source statement

Mark every meaningful instruction or document section as one of the following:

- **Trigger:** when a workflow should activate.
- **Input:** information the workflow requires.
- **Process:** decisions or ordered actions.
- **Output:** what the user should receive.
- **Boundary:** what the workflow must not infer or do.
- **Stop/approval condition:** when it must ask, wait, or decline.
- **Safety or policy:** domain-specific constraints.
- **Reference knowledge:** details needed only in some cases.
- **Deterministic operation:** logic better implemented as a script.
- **Asset:** a template or file copied or transformed in output.
- **Live integration:** a candidate for an MCP tool rather than static instructions.

This classification is the bridge from “one long system prompt” to a plugin architecture.

## 5. Phase 2: turn instructions into use cases and acceptance criteria

### 5.1 Write a use-case inventory

List the recognizable goals users bring to the GPT. Do not begin with source-document headings; begin with user intent.

For each use case, record:

- representative user requests;
- required inputs;
- successful output;
- required references or tools;
- important decision points;
- questions the workflow may need to ask;
- unsafe or unsupported outcomes;
- whether the workflow shares state with another workflow.

Example:

```text
Use case: Guide inductive observation of a Bible passage
Trigger: The user wants to observe textual facts, relationships, or structure
Input: A passage reference or supplied passage text
Output: One to three text-grounded questions followed by a waiting point
Must not: Jump directly to interpretation or application
References: observation.md, relationships.md, structure.md, questions.md
Next workflow: interpreting-biblical-passages, only with learner consent
```

### 5.2 Build a requirement coverage matrix before implementation

Create one row for every behavioral requirement in the GPT instructions and every important resource module.

| Requirement | Owning skill/reference | Test evidence | Status |
|---|---|---|---|
| Detect four conversation modes | Orchestrator | Mode-routing scenarios | Planned |
| Ask no more than three questions per turn | Interaction reference | Contract test | Planned |
| Preserve ten study stages | Three phase skills | Coverage and behavior tests | Planned |
| Compare translations without inventing source-language claims | Lexical skill | Pressure scenario | Planned |
| Keep generated corpus data outside the plugin | Retrieval/runtime layer | Distribution audit | Planned |

The Cool Bible Tutor matrix exposed both missing coverage and explicit exclusions. This was more reliable than rereading the original prompt at the end and hoping every requirement survived.

### 5.3 Resolve contradictions explicitly

Source GPT instructions frequently contain tensions, such as:

- “Never give the answer” versus “Answer direct questions helpfully.”
- “Always follow all ten steps” versus “Let the learner skip or stop.”
- “Use these exact resources” versus filenames that no longer exist.
- “Quote the source exactly” versus unverified or copyrighted source text.

Choose one testable interpretation and record it in the coverage matrix or design notes. Do not preserve ambiguity inside the skill.

## 6. Phase 3: design the plugin architecture

### 6.1 Decide whether an MCP server is needed

Choose a skills-only plugin when the workflow needs:

- packaged instructions;
- static reference documents;
- templates or other assets;
- local deterministic scripts;
- no remote account or live service.

Add an MCP server when the plugin must:

- read or change live external data;
- authenticate a user;
- enforce authorization centrally;
- expose controlled external actions;
- return current state that cannot be bundled.

Do not build an MCP server merely to store a long reference document. Conversely, do not place credentials, live API mutation logic, or access-control decisions in `SKILL.md`.

### 6.2 Choose skill boundaries by user goal

Create separate skills when workflows have materially different:

- triggers;
- required inputs;
- success criteria;
- safety boundaries;
- tools or references;
- stopping conditions.

Do not create one skill per source file. Several source documents may support one workflow, and one monolithic instruction document may contain several workflows.

Good boundary:

```text
observing-biblical-passages
  Trigger: observation before interpretation
  References: facts, relationships, structure, question formulation
```

Weak boundary:

```text
bible-document-1
  Trigger: whenever anything in source document 1 might matter
```

### 6.3 Use an orchestrator only when coordination is real

An orchestrator skill is justified when several skills participate in a stateful user journey. It should own:

- top-level mode selection;
- workflow state or current phase;
- routing conditions;
- shared interaction rules;
- transitions and stop conditions.

It should not duplicate every sibling skill's detailed procedure. In Cool Bible Tutor, the orchestrator keeps the learner-paced contract and names the next appropriate skill, while observation, interpretation, application, theology, exegesis, lexical comparison, and retrieval keep their own operating rules.

### 6.4 Prefer progressive disclosure

Use three levels of disclosure:

1. **Name and description:** enough for Codex to decide whether the skill applies.
2. **`SKILL.md`:** the essential operating contract and routing instructions.
3. **Supporting files:** detailed guidance loaded only when needed.

This matters for both accuracy and context cost. The finished Cool Bible Tutor skills keep their `SKILL.md` entrypoints short—roughly a few dozen lines—while substantial stage-specific material lives in `references/`.

## 7. Phase 4: scaffold the plugin

### 7.1 Recommended plugin tree

```text
my-gpt-plugin/
├── .codex-plugin/
│   └── plugin.json
├── skills/
│   ├── orchestrating-my-gpt/
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   └── openai.yaml
│   │   └── references/
│   └── performing-one-user-goal/
│       ├── SKILL.md
│       ├── agents/
│       │   └── openai.yaml
│       ├── references/
│       ├── scripts/
│       └── assets/
├── scripts/
├── tests/
├── README.md
├── DISTRIBUTION.md
├── PRIVACY.md
├── SECURITY.md
├── THIRD_PARTY_NOTICES.md
└── LICENSE
```

Only create directories that have a real purpose. A narrow skill may need nothing except `SKILL.md` and `agents/openai.yaml`.

### 7.2 Scaffold with the built-in creators

In Codex, a natural-language starting request can be:

```text
$plugin-creator Create a skills-only plugin named my-gpt-plugin.
Include a skills directory, but do not publish it or modify an existing marketplace yet.
```

For an individual skill:

```text
$skill-creator Create a skill named performing-one-user-goal.
It should activate when [...], require [...], produce [...], and must not [...].
```

The bundled scaffold scripts can also be used directly. Paths vary by installation, so treat `<plugin-creator-root>` and `<skill-creator-root>` as resolved tool locations:

```powershell
python <plugin-creator-root>/scripts/create_basic_plugin.py `
  my-gpt-plugin --path . --with-skills

python <skill-creator-root>/scripts/init_skill.py `
  performing-one-user-goal `
  --path ./my-gpt-plugin/skills `
  --resources references,scripts,assets
```

Do not leave scaffold placeholders in a finished plugin.

## 8. Phase 5: author each skill

### 8.1 Write a discriminating description

Every skill requires a `SKILL.md` with YAML frontmatter:

```markdown
---
name: performing-one-user-goal
description: Use when the user wants [specific goal] and the workflow requires [distinguishing condition].
---
```

The description controls discovery. It should state what the skill does and when it applies. Avoid descriptions such as “helps with documents,” “handles the GPT,” or “use for all questions about this domain.”

### 8.2 Put the operating contract in the body

The body should make these points clear:

- expected input;
- ordered or conditional workflow;
- required output;
- facts the model must not infer;
- when to ask a question;
- when to stop, wait, or decline;
- which reference or script to use and under what condition;
- routing to another skill, when appropriate.

Example:

```markdown
Use the supplied passage text as the observation boundary.

1. Determine whether the learner is examining facts, relationships, structure, or questions.
2. Read only the corresponding reference file.
3. Ask one to three text-grounded questions.
4. Wait for the learner's response.

Do not present interpretation as observation. Do not move to the next stage without the learner's consent.
```

### 8.3 Route supporting resources explicitly

Use:

- `references/` for policies, schemas, detailed procedures, examples, and domain background;
- `scripts/` for repeatable deterministic computation or file processing;
- `assets/` for templates and files meant to be copied, transformed, or included in output;
- `agents/openai.yaml` for user-facing metadata, invocation policy, and MCP dependencies.

Link resources from `SKILL.md` where they become relevant:

```markdown
- For observation of repeated words and visible facts, read [observation](references/observation.md).
- For paragraph and narrative structure, read [structure](references/structure.md).
- Do not load both unless the current request requires both.
```

### 8.4 Add `agents/openai.yaml`

A typical skills-only file is:

```yaml
interface:
  display_name: "Perform One User Goal"
  short_description: "Complete one focused and repeatable workflow"
  default_prompt: "Use $performing-one-user-goal to complete this workflow."

policy:
  allow_implicit_invocation: true
```

Quote string values. The default prompt should explicitly mention `$skill-name`. Keep implicit invocation enabled unless the user explicitly wants an explicit-only skill.

If a skill requires an MCP server, declare the dependency rather than pretending the tool is always available:

```yaml
dependencies:
  tools:
    - type: "mcp"
      value: "service-name"
      description: "Read and update the service"
      transport: "streamable_http"
      url: "https://example.com/mcp"
```

### 8.5 Keep scripts stable and relocatable

Scripts included in an installed plugin must not assume the developer's workspace path. Resolve the plugin root from the script's installed location, use relative packaged paths, and write mutable state outside the plugin.

The Cool Bible Tutor experience established a useful pattern:

- immutable release assets remain under the plugin root;
- generated databases, caches, review history, downloads, and user corrections live in a per-user data directory;
- a stable top-level launcher provides one documented interface;
- the launcher rejects output paths inside the installed plugin;
- optional downloads require explicit consent and are verified before activation.

See [`../applications/cool-bible-tutor/docs/top-level-launcher-pattern.md`](../applications/cool-bible-tutor/docs/top-level-launcher-pattern.md) for the case-study pattern.

## 9. Phase 6: test behavior before trusting the skill

Skill validation proves structure, not behavior. Use several complementary test layers.

### 9.1 Baseline and skill-enabled scenarios

Before authoring a complex skill, record how a capable model behaves without it. Then rerun the same request with the skill enabled.

Use pressure scenarios that reveal likely failures:

- request an unsupported shortcut;
- omit a required input;
- ask the model to invent unavailable evidence;
- combine conflicting constraints;
- push it to skip an approval or waiting point;
- ask for a one-sided conclusion where the workflow requires balance;
- provide ambiguous or malformed source references.

Record observable pass criteria, not preferred wording. A good scenario says “asks no more than three questions and waits,” not “contains the sentence ‘Would you like to continue?’”

The case-study scenarios are in [`../applications/cool-bible-tutor/tests/behavior/`](../applications/cool-bible-tutor/tests/behavior/).

### 9.2 Contract tests

Use simple tests for invariants that must remain visible in packaged files:

- every sibling route uses the exact skill name;
- every referenced Markdown file exists;
- the orchestrator includes all required response states;
- every source-guide category is represented;
- UI metadata names the correct skill;
- known unsafe shortcuts are explicitly prohibited.

See [`../applications/cool-bible-tutor/tests/test_skill_contracts.py`](../applications/cool-bible-tutor/tests/test_skill_contracts.py) for a concrete example.

Do not overfit these tests to prose formatting. Contract tests complement behavior evaluation; they do not replace it.

### 9.3 Coverage tests

Treat the requirement coverage matrix as a release artifact. A requirement is complete only when it has:

1. an owning skill or reference;
2. observable behavior evidence or a structural invariant;
3. an explicit exclusion if it is intentionally out of scope.

### 9.4 Validate each skill

Run the skill validator on every skill directory:

```powershell
python <skill-creator-root>/scripts/quick_validate.py `
  ./my-gpt-plugin/skills/performing-one-user-goal
```

Repeat for all skills. Validation should fail for malformed frontmatter, invalid naming, or unfinished scaffold content.

## 10. Phase 7: create the plugin manifest

Every plugin requires `.codex-plugin/plugin.json`. A marketplace-grade skills-only manifest can look like this:

```json
{
  "name": "my-gpt-plugin",
  "version": "1.0.0",
  "description": "A focused description of the user outcomes this plugin supports.",
  "author": {
    "name": "Publisher Name",
    "url": "https://github.com/publisher"
  },
  "homepage": "https://github.com/publisher/plugins/tree/main/plugins/my-gpt-plugin",
  "repository": "https://github.com/publisher/plugins",
  "license": "MIT",
  "keywords": ["domain", "workflow", "language"],
  "skills": "./skills/",
  "interface": {
    "displayName": "My GPT Plugin",
    "shortDescription": "A short, scannable description.",
    "longDescription": "A fuller explanation of the plugin's purpose, scope, and important operating boundary.",
    "developerName": "Publisher Name",
    "category": "Education",
    "capabilities": ["Interactive", "Read"],
    "defaultPrompt": [
      "Help me begin the primary workflow.",
      "Use the plugin for a second representative goal.",
      "Guide me through an advanced use case."
    ]
  }
}
```

Rules worth enforcing:

- plugin directory name, manifest `name`, and marketplace entry `name` must match;
- use lower-case kebab case for stable identifiers;
- use strict semantic versioning;
- keep paths relative and beginning with `./`;
- include `apps` only when `.app.json` exists;
- include `mcpServers` only when the plugin actually supplies or references MCP configuration;
- use absolute HTTPS URLs for public website, privacy, and terms fields when present;
- make every icon or screenshot path point to a real packaged file;
- keep starter prompts short and representative;
- do not copy secrets, local paths, or private operational details into searchable metadata.

Validate the plugin:

```powershell
python <plugin-creator-root>/scripts/validate_plugin.py ./my-gpt-plugin
```

The current case-study manifest is [`../applications/cool-bible-tutor/.codex-plugin/plugin.json`](../applications/cool-bible-tutor/.codex-plugin/plugin.json).

## 11. Phase 8: define the distribution boundary

The source tree and the public release tree should be treated as different products.

Record that boundary in `applications/<plugin-id>/openclaw/distribution.json`.
New builds require distribution-contract schema v3. Schema v1 and v2 remain
readable only for legacy verification and return `legacy_contract_read_only`
when a caller attempts to rebuild them. Use `migrate-contract` to create a
non-destructive proposal; a decision owner must resolve every classification
and redistribution decision before the proposal becomes a buildable contract.

### 11.1 Use an allowlist

An allowlist is safer than copying the source folder and deleting known private files afterward. Permit only intentional release files and directories, such as:

- `.codex-plugin/`;
- `skills/`;
- approved `scripts/` and `assets/`;
- required runtime manifests;
- tests safe for public distribution;
- README, license, privacy, security, and third-party notices.

Reject or exclude:

- credentials and tokens;
- `.env` files;
- user data and conversation exports;
- review history and audit databases;
- generated caches and temporary files;
- OCR output and rendered source pages;
- machine-specific absolute paths;
- model weights or large dependencies not intentionally licensed and packaged;
- symlinks that could escape the source tree;
- unrelated source documents;
- unfinished placeholders;
- broken local links.

Schema-v3 `content_rules` are deny-by-default. Every selected file must match
exactly one text or binary rule. Text rules declare canonicalization, and every
included rule cites approved redistribution evidence from an application-owned
provenance file. Ambiguous classification, missing classification, unsafe
links, generated-path collisions, or unresolved rights block the build before
the output directory is changed.

### 11.2 Audit rights and provenance

For every redistributed reference or asset, record:

- who owns it;
- the redistribution basis or license;
- required attribution;
- whether modifications are allowed;
- whether the plugin implies endorsement;
- a checksum when exact source identity matters.

If rights are uncertain, leave the file out of the plugin and document how an authorized user supplies it locally. Do not infer permission from the fact that a file was uploaded to a Custom GPT.

### 11.3 Bind immutable data to manifests

When a plugin intentionally includes a database, index, model manifest, or other generated runtime asset, validate more than its filename:

- SHA-256 digest;
- schema and table allowlist;
- expected row or item counts;
- absence of private metadata;
- source identity;
- model or dependency revision;
- integrity check;
- ordinary GitHub object-size limits.

Cool Bible Tutor eventually shipped an explicitly approved read-only corpus and compact search index. Its audit rejects any undeclared database while performing structural and digest checks on the two allowed artifacts. This is an exception backed by release engineering, not permission to publish arbitrary generated data.

The case-study audit is [`../applications/cool-bible-tutor/scripts/distribution_audit.py`](../applications/cool-bible-tutor/scripts/distribution_audit.py).

### 11.4 Validate and build through the generic framework

Run the non-interactive preflight before building:

```powershell
python -B -m obvious_one_plugin_framework.cli validate-contract `
  --contract .\applications\<plugin-id>\openclaw\distribution.json `
  --json
```

If the contract is legacy, create a reviewable proposal rather than editing or
guessing classifications in place:

```powershell
python -B -m obvious_one_plugin_framework.cli migrate-contract `
  --contract .\applications\<plugin-id>\openclaw\distribution.json `
  --output .\.tmp\<plugin-id>-schema-v3-proposal.json `
  --json
```

After approval, build and verify the lightweight OpenClaw artifact:

```powershell
python -B -m obvious_one_plugin_framework.cli build-package `
  --contract .\applications\<plugin-id>\openclaw\distribution.json `
  --output .\dist\openclaw\<plugin-id>

python -B -m obvious_one_plugin_framework.cli verify `
  --contract .\applications\<plugin-id>\openclaw\distribution.json `
  --output .\dist\openclaw\<plugin-id>
```

The builder stages transactionally, validates the post-copy tree, reserves the
framework runtime namespace, and writes a deterministic content manifest. Each
CLI invocation emits exactly one ASCII-safe `result-schema-v1` document.
Clients must parse that result and its status; exit code zero alone is not
artifact evidence.

## 12. Phase 9: prepare a GitHub repository marketplace

### 12.1 Recommended marketplace repository layout

```text
my-plugin-marketplace/
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── plugins/
│   └── my-gpt-plugin/
│       ├── .codex-plugin/
│       │   └── plugin.json
│       ├── skills/
│       └── ...
├── openclaw/
│   └── my-gpt-plugin/
├── .obvious-one-validation.json
├── tools/
│   └── verify_marketplace.py
├── .github/
│   └── workflows/
│       └── validate.yml
├── .release-manifest.json
├── README.md
└── LICENSE
```

The Obvious One preparation catalog owns the Codex and OpenClaw destinations
for every application. The generated registry and verifier make validation
catalog-driven instead of hard-coding one reference product into CI.

### 12.2 Create `marketplace.json`

Example:

```json
{
  "name": "my-marketplace",
  "interface": {
    "displayName": "My Plugin Marketplace"
  },
  "plugins": [
    {
      "name": "my-gpt-plugin",
      "source": {
        "source": "local",
        "path": "./plugins/my-gpt-plugin"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Education"
    }
  ]
}
```

Required consistency rules:

- top-level `name` is the marketplace identifier used by install commands;
- `interface.displayName` is the human-facing marketplace name;
- each plugin entry contains `policy.installation`, `policy.authentication`, and `category`;
- `source.path` remains `./plugins/<plugin-name>` for this repository layout;
- plugin entries are ordered as you want them rendered;
- append new entries unless deliberate reordering is required;
- omit product gating unless it is explicitly needed.

Typical policies are:

- `installation`: `AVAILABLE`, `NOT_AVAILABLE`, or `INSTALLED_BY_DEFAULT`;
- `authentication`: `ON_INSTALL` or `ON_USE`.

### 12.3 Declare the preparation catalog

Keep the catalog in the conversion repository, not in product instructions. An
entry uses `build` for an approved schema-v3 application or `verify_existing`
for a published legacy artifact whose exact bytes must be preserved. Legacy
verification is not trust in an old manifest: paths, sizes, SHA-256 values,
aggregate identity, and complete scoped trees are recalculated.

### 12.4 Prepare and verify a local delta

Treat the marketplace checkout as a read-only baseline. Prepare a separate
staging tree:

```powershell
python -B -m obvious_one_plugin_framework.cli prepare-marketplace `
  --catalog .\marketplaces\obvious-one.json `
  --marketplace <clean-marketplace-checkout> `
  --output .\dist\marketplace-delta\obvious-one `
  --json
```

Preparation updates only declared destinations, preserves unrelated content,
reconstructs both runtime catalogs, and generates the self-contained verifier
and catalog-driven CI workflow. It also writes scoped Git attributes such as
`-text whitespace=cr-at-eol` so exact manifest bytes survive Windows, Linux,
and macOS checkouts.

Verify filesystem evidence first, then Git index, commit, and fresh-checkout
evidence as separate modes:

```powershell
python -B -m obvious_one_plugin_framework.cli verify-marketplace --catalog .\marketplaces\obvious-one.json --marketplace .\dist\marketplace-delta\obvious-one --json
python -B -m obvious_one_plugin_framework.cli verify-marketplace --catalog .\marketplaces\obvious-one.json --marketplace <external-git-stage> --index --json
python -B -m obvious_one_plugin_framework.cli verify-marketplace --catalog .\marketplaces\obvious-one.json --marketplace <external-git-stage> --commit HEAD --json
python -B -m obvious_one_plugin_framework.cli verify-marketplace --catalog .\marketplaces\obvious-one.json --marketplace <external-git-stage> --fresh-checkout --json
```

Do not create a nested Git worktree under the conversion repository, including
under `dist` or `.tmp`; repository-boundary tests intentionally reject nested
`.git` metadata. Use an external temporary Git repository or a platform-managed
worktree. Preparation never applies or publishes the delta. GitHub marketplace
publication requires a separate review and explicit approval.

For repositories containing intentional binary assets, also check object sizes
before publication. Large optional models or platform dependencies are usually
better downloaded after explicit consent and verified against pinned manifests.

### 12.5 Document marketplace installation

Codex can track a Git-backed marketplace directly. Current official examples include GitHub shorthand, Git URLs, refs, sparse checkouts, and local roots:

```powershell
codex plugin marketplace add <owner>/<marketplace-repo>
codex plugin marketplace add <owner>/<marketplace-repo> --ref main
codex plugin marketplace add https://github.com/<owner>/<marketplace-repo>.git
codex plugin marketplace add ./local-marketplace-root
```

Then inspect and install:

```powershell
codex plugin marketplace list
codex plugin add my-gpt-plugin@my-marketplace
codex plugin list
```

Test the installed plugin in a **new task**. A pre-existing task may retain earlier skill context and is not a reliable pickup test.

For a private GitHub repository, use an already authorized Git transport—such as the user's Git credential manager or SSH configuration—rather than embedding a token in the repository URL, plugin manifest, or documentation.

## 13. Phase 10: release and update workflow

### 13.1 Separate product versions from local cache-busting

Use semantic versions for releases:

- patch: fixes without intended workflow change;
- minor: backward-compatible features or new skills;
- major: incompatible behavior, data, or integration changes.

During local development, Codex may need a cache-busting manifest version so a reinstall sees changed files. Preserve the base version and use one suffix:

```text
1.2.3+codex.local-YYYYMMDD-HHMMSS
```

Do not increment the public patch version merely to force a local refresh, and do not accumulate multiple suffixes.

With the bundled helper:

```powershell
python <plugin-creator-root>/scripts/read_marketplace_name.py `
  --marketplace-path <marketplace-root>/.agents/plugins/marketplace.json

python <plugin-creator-root>/scripts/update_plugin_cachebuster.py `
  <plugin-source-path>

codex plugin add <plugin-name>@<validated-marketplace-name>
```

For the default personal marketplace at `~/.agents/plugins/marketplace.json`, Codex discovers it implicitly. For a non-default local or Git-backed marketplace, add or configure the marketplace source first.

### 13.2 Publish a real release

After the locally staged delta and its exact Git evidence pass:

1. restore a clean semantic version without a local cache-buster;
2. run all skill, behavior, plugin, distribution, framework, and product tests;
3. regenerate the marketplace delta from the approved clean baseline;
4. inspect the manifests, machine-readable results, and exact Git diff;
5. obtain explicit approval for the specific marketplace mutation;
6. commit and push a marketplace branch, then let catalog-driven CI validate
   every registered plugin on its configured operating systems;
7. merge only after required checks pass;
8. install from the GitHub marketplace and run smoke scenarios in new Codex and
   OpenClaw sessions.

A GitHub tag or GitHub Release is not implied by marketplace publication.
Likewise, ClawHub publication and universal-directory submission are separate
channels with separate contracts and approvals. When ClawHub is enabled,
schema v3 requires a compatible native manifest and declared extension files;
when disabled, the channel is `NOT APPLICABLE` rather than failed.

After publishing an update, users can refresh configured marketplaces with:

```powershell
codex plugin marketplace upgrade
# or one marketplace:
codex plugin marketplace upgrade <marketplace-name>
```

Then reinstall or update the plugin as required by the current client and retest in a new task.

### 13.3 Preserve marketplace configuration during updates

Do not hand-edit user `config.toml` files. Use `codex plugin marketplace add`, `list`, `upgrade`, and `remove` for configured sources. Do not rewrite an existing marketplace entry during a normal plugin code iteration unless its actual source, policy, category, or identity must change.

## 14. Optional: submit to the universal plugin directory

When the GitHub marketplace version is stable, you may separately submit it for public review through the OpenAI Platform.

OpenAI currently accepts:

- skills-only plugins;
- MCP-only plugins;
- plugins combining skills and an MCP server.

The submission process requires more than a GitHub URL. Prepare:

- verified developer or business identity;
- organization role with plugin-submission write access;
- listing name, descriptions, category, logo, website, support URL, privacy policy, and terms;
- starter prompts and representative test cases;
- country availability and policy attestations;
- for MCP plugins, the public server, authentication details, accurate tool metadata, domain verification, and review credentials when required.

Consult the current [plugin submission documentation](https://developers.openai.com/plugins/deploy/submission) immediately before submitting because review fields and policy requirements can change.

## 15. An end-to-end operator runbook

The following compact runbook assumes the plugin design and rights review are complete.

### Step 1: validate every skill

```powershell
Get-ChildItem ./my-gpt-plugin/skills -Directory | ForEach-Object {
  python <skill-creator-root>/scripts/quick_validate.py $_.FullName
  if ($LASTEXITCODE -ne 0) { throw "Skill validation failed: $($_.Name)" }
}
```

### Step 2: run plugin tests

Use the repository's real test runner. For a Python standard-library suite:

```powershell
python -m unittest discover -s ./my-gpt-plugin/tests -p "test_*.py" -v
```

### Step 3: validate the plugin and distribution contract

```powershell
python <plugin-creator-root>/scripts/validate_plugin.py ./my-gpt-plugin
python -B -m obvious_one_plugin_framework.cli validate-contract `
  --contract .\applications\my-gpt-plugin\openclaw\distribution.json `
  --json
```

Run any application-owned distribution audit declared by the product tests, but
do not substitute it for the generic schema-v3 preflight.

### Step 4: prepare the marketplace delta

```powershell
python -B -m obvious_one_plugin_framework.cli prepare-marketplace `
  --catalog .\marketplaces\obvious-one.json `
  --marketplace <clean-marketplace-checkout> `
  --output .\dist\marketplace-delta\obvious-one `
  --json
```

### Step 5: verify and inspect the staged tree

```powershell
python -B -m obvious_one_plugin_framework.cli verify-marketplace `
  --catalog .\marketplaces\obvious-one.json `
  --marketplace .\dist\marketplace-delta\obvious-one `
  --json

git diff --no-index -- <clean-marketplace-checkout> .\dist\marketplace-delta\obvious-one
```

### Step 6: test the local marketplace root

```powershell
codex plugin marketplace add .\dist\marketplace-delta\obvious-one
codex plugin marketplace list
codex plugin add my-gpt-plugin@my-marketplace
codex plugin list
```

Start a new task and run at least:

- one normal request per skill;
- one ambiguous routing request;
- one missing-input request;
- one pressure or safety-boundary request;
- one packaged script or asset workflow;
- one offline or unavailable-dependency scenario, if applicable;
- the corresponding OpenClaw discovery and representative execution scenario.

### Step 7: publish only after explicit approval

After approval, apply the reviewed delta on a marketplace feature branch, open
a pull request, and require the generated catalog-driven CI matrix to pass.
Merge the marketplace pull request before considering any separately approved
tag, GitHub Release, ClawHub publication, or universal-directory submission.

Then replace the local marketplace source and install the published plugin:

```powershell
codex plugin marketplace remove my-marketplace
codex plugin marketplace add <owner>/<marketplace-repo> --ref main
codex plugin add my-gpt-plugin@my-marketplace
```

Repeat the Codex and OpenClaw smoke scenarios. This verifies the published
repository version rather than the developer's source folder.

## 16. Common failure modes and their corrections

### One giant skill copied from the GPT instructions

**Symptom:** unrelated rules load for every request, routing is vague, and detailed references consume context constantly.

**Correction:** split by recognizable user goal; retain shared routing and state only in an orchestrator; move conditional detail to references.

### One skill per source document

**Symptom:** skill triggers describe filenames rather than user goals.

**Correction:** map documents to use cases first. Several documents may support one skill.

### Missing requirement traceability

**Symptom:** the plugin appears plausible, but a critical interaction, safety, or domain rule disappeared during rewriting.

**Correction:** maintain a requirement coverage matrix with implementation and test evidence.

### Descriptions that activate too broadly

**Symptom:** the plugin's skills appear for unrelated questions.

**Correction:** describe the concrete outcome and distinguishing trigger conditions; keep detailed procedure out of the description.

### References that are never routed

**Symptom:** useful files are packaged but the model has no instruction about when to consult them.

**Correction:** link each reference from `SKILL.md` at the decision point where it matters.

### Deterministic work left to prose

**Symptom:** parsing, file processing, checksums, or release copying varies between runs.

**Correction:** implement repeatable mechanics as tested scripts and keep judgment in the skill.

### Private or generated data copied into the plugin

**Symptom:** local paths, user content, review databases, credentials, or caches appear in Git.

**Correction:** use schema-v3 `content_rules`, external per-user data
directories, an application-owned audit, the generic transactional builders,
and staged-tree inspection.

### Publishing assets without a rights decision

**Symptom:** a source was available to the GPT, so it was assumed redistributable.

**Correction:** record ownership, license or authorization, attribution, permitted modifications, and release scope for every asset.

### Treating a GitHub push as universal publication

**Symptom:** documentation claims the plugin is publicly listed in ChatGPT and Codex after only publishing a repository marketplace.

**Correction:** label the GitHub marketplace as a separate distribution source and use the Platform submission portal for universal-directory review.

### Testing only the source folder

**Symptom:** development tests pass, but packaged files are missing, stale, or undiscoverable.

**Correction:** install the built marketplace version and test it in a new task.

### Editing marketplace or Codex configuration by hand during routine updates

**Symptom:** marketplace identity, cached source, or plugin source diverges across machines.

**Correction:** use the creator helpers and `codex plugin marketplace` commands; validate the marketplace name before reinstalling.

## 17. Lessons from the Cool Bible Tutor development history

The repository history shows an effective incremental sequence:

1. design the plugin and redistribution boundary;
2. scaffold the plugin;
3. implement the orchestrator;
4. add one focused instructional skill at a time;
5. complete a core coverage matrix;
6. add exact reference parsing and retrieval;
7. add provenance and verification gates;
8. add optional semantic discovery without allowing it to replace exact retrieval;
9. add a secured human-review workflow;
10. bundle only explicitly authorized, immutable assets;
11. add managed runtime setup with consent and digest verification;
12. build an auditable marketplace release;
13. add searchable marketplace metadata;
14. fix release reproducibility details such as line-ending preservation.

Several broader lessons follow:

- Architecture and distribution rights should be designed before copying source files.
- Behavior should be migrated in small independently testable slices.
- Retrieval confidence and semantic relevance are different claims and should have different gates.
- Human-reviewed or security-sensitive state should remain external and auditable.
- Release engineering includes seemingly small reproducibility details; line endings, file ordering, hashes, and atomic replacement can affect the published package.
- Marketplace metadata is part of the product. Add it after the behavior and distribution boundaries are stable, then test discovery prompts as well as execution.

## 18. Release-readiness checklist

### Source and design

- [ ] Original GPT source files are preserved unchanged.
- [ ] Every source document has an owner, purpose, and redistribution decision.
- [ ] Filename inconsistencies have an explicit canonical mapping.
- [ ] User-goal use cases are documented.
- [ ] Every system-instruction requirement appears in a coverage matrix.
- [ ] Contradictions and exclusions are resolved explicitly.
- [ ] Skills-only versus MCP architecture has been chosen intentionally.

### Skills

- [ ] Every skill name is lower-case kebab case and matches its folder.
- [ ] Every description states a specific outcome and trigger.
- [ ] `SKILL.md` defines input, process, output, boundaries, and stop conditions.
- [ ] Conditional details are in routed references.
- [ ] Deterministic repeated operations are tested scripts.
- [ ] Assets are used as output resources, not loaded indiscriminately as instructions.
- [ ] `agents/openai.yaml` metadata matches the skill.
- [ ] MCP dependencies are declared when required.
- [ ] Every skill passes `quick_validate.py`.

### Behavior and traceability

- [ ] Baseline and skill-enabled scenarios exist for important workflows.
- [ ] Pressure scenarios cover missing inputs, shortcuts, and unsafe inference.
- [ ] Contract tests protect exact routes and essential invariants.
- [ ] Local reference links are checked.
- [ ] Every coverage-matrix row has implementation and evidence.

### Plugin and distribution

- [ ] `.codex-plugin/plugin.json` passes validation.
- [ ] The distribution contract is schema v3; schema v1/v2 inputs are treated as read-only legacy formats.
- [ ] Every selected file matches exactly one approved `content_rules` entry.
- [ ] Plugin folder name, manifest name, and marketplace entry name match.
- [ ] Version is valid semantic versioning.
- [ ] Search metadata is accurate and non-sensitive.
- [ ] README, license, privacy, security, and third-party notices are complete as applicable.
- [ ] A release allowlist excludes unrelated source and private state.
- [ ] Included binary or generated assets have integrity and provenance checks.
- [ ] No credential, local absolute path, cache, or private database is packaged.
- [ ] The staged release is audited after copying.
- [ ] A per-file release manifest is generated.

### Marketplace and publication

- [ ] `.agents/plugins/marketplace.json` has a stable unique name.
- [ ] The preparation catalog contains every intended Codex and OpenClaw artifact exactly once.
- [ ] `prepare-marketplace` changed only declared destinations in a separate staged tree.
- [ ] Filesystem, index, commit, and fresh-checkout verification pass as applicable.
- [ ] Generated catalog-driven CI validates every registered plugin independently.
- [ ] Every entry contains source, policy, and category.
- [ ] The GitHub repository contains the release tree, not the private authoring tree.
- [ ] The staged Git diff has been manually reviewed.
- [ ] The marketplace is installable from a local root.
- [ ] The plugin is tested from the installed local marketplace in a new task.
- [ ] Any repository push, tag, GitHub Release, ClawHub publication, or universal-directory submission has separate explicit approval.
- [ ] The marketplace is installable from the GitHub source.
- [ ] The GitHub-installed plugin is retested in a new task.
- [ ] Documentation distinguishes repository distribution from universal-directory publication.

## 19. Case-study files to examine

These files capture the development practices discussed in this guide:

- [Plugin design specification](superpowers/specs/2026-08-22-cool-bible-tutor-plugin-design.md)
- [Core plugin implementation plan](superpowers/plans/2026-08-22-cool-bible-tutor-core-plugin.md)
- [Public runtime and marketplace design](superpowers/specs/2026-08-24-cool-bible-tutor-public-runtime-assets-design.md)
- [Cool Bible Tutor plugin manifest](../applications/cool-bible-tutor/.codex-plugin/plugin.json)
- [Skill requirement coverage matrix](../applications/cool-bible-tutor/tests/coverage-matrix.md)
- [Skill contract tests](../applications/cool-bible-tutor/tests/test_skill_contracts.py)
- [Distribution audit](../applications/cool-bible-tutor/scripts/distribution_audit.py)
- [Marketplace release builder](../applications/cool-bible-tutor/scripts/build_marketplace_release.py)
- [Marketplace release tests](../applications/cool-bible-tutor/tests/test_marketplace_release.py)
- [Distribution documentation](../applications/cool-bible-tutor/DISTRIBUTION.md)
- [Plugin README](../applications/cool-bible-tutor/README.md)

## 20. Final principle

The goal is not to preserve the original GPT's files verbatim. The goal is to preserve its intended behavior, knowledge boundaries, safety constraints, and useful resources in a form that is discoverable, testable, relocatable, and safe to distribute.

A successful conversion can answer four questions with evidence:

1. **When does each skill activate?**
2. **What exact outcome and boundary does it own?**
3. **Which source requirement and reference support it?**
4. **How do we know the installed marketplace package still behaves that way?**

When the coverage matrix, skill tests, distribution audit, marketplace install, and new-task smoke tests all agree, the plugin is ready to share.
