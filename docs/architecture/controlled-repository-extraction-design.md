# Controlled GPT Conversion Repository Extraction Design

**Date:** 2026-09-13

**Status:** Approved architecture, specification review pending

**Target repository:** `D:\GitHub\convert-gpt-application`

## 1. Purpose

Separate original GPT application materials from reusable conversion tooling and from public marketplace artifacts. The existing `酷聖經教師 4.0` folder becomes a source archive for GPT instructions and reference files. A new Git repository, `convert-gpt-application`, becomes the development home for generic conversion tooling and active plugin conversion projects. `obvious-one-plugins` remains the generated public marketplace repository.

The migration is a controlled extraction. It is not a filesystem move and does not delete source material during the initial extraction.

## 2. Repository boundaries

### Original GPT application archive

The existing folder retains:

- original GPT instructions and exports;
- reference documents, PDFs, presentations, and design material;
- application-specific source indexes;
- an inventory containing stable hashes and redistribution classifications.

It does not remain the long-term home of generic framework code, generated distributions, GitHub Actions, or public marketplace artifacts.

### Conversion development repository

`D:\GitHub\convert-gpt-application` owns:

- the generic Obvious One plugin distribution framework;
- plugin and skill templates;
- package-local runtime bootstrap templates;
- generic RAG adapter and index-reuse contracts;
- framework tests and synthetic fixtures;
- conversion and publication documentation;
- active application conversion workspaces, including Cool Bible Tutor;
- future generic marketplace generation and release orchestration.

The repository starts with a curated new Git history. This prevents unrelated source documents or previously tracked private binaries from being inherited through old Git history. A provenance record identifies the source repository commit and incorporated feature branches.

### Public marketplace repository

`D:\GitHub\obvious-one-plugins` contains only audited public output:

- Codex marketplace metadata and full plugin artifacts;
- OpenClaw-compatible marketplace metadata and lightweight artifacts;
- public licenses, notices, and documentation;
- release manifests and GitHub Actions workflows.

The marketplace is a build destination, never the canonical development source.

### RAG subsystem repository

`D:\GitHub\Codex-RAGenius-System\rag_subsystem` remains an independently installable Python package. The conversion framework consumes its public Python interface. The framework does not copy its implementation into each application.

## 3. Target layout

```text
convert-gpt-application/
├── src/
│   └── obvious_one_plugin_framework/
│       └── templates/
│           └── runtime/
├── templates/
│   ├── plugin/
│   ├── skill/
│   ├── github-workflows/
│   └── marketplace/
├── applications/
│   └── cool-bible-tutor/
│       ├── conversion.json
│       ├── .codex-plugin/
│       ├── skills/
│       ├── scripts/
│       ├── assets/
│       ├── openclaw/
│       └── tests/
├── tests/
│   ├── framework/
│   └── fixtures/
├── docs/
├── scripts/
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

The package uses a `src` layout. Runtime bootstrap templates remain package data under `src/obvious_one_plugin_framework/templates/runtime` so installed package builds do not depend on repository-relative paths. The root `templates` directory contains developer-facing plugin, skill, workflow, and marketplace templates. Framework commands are invoked as `python -m obvious_one_plugin_framework.cli` after an editable development installation.

## 4. Source linkage

Raw GPT material is not copied automatically into the development repository. Each application has a tracked `conversion.json` containing:

- stable application and plugin IDs;
- expected source-inventory hash;
- relative logical names for required inputs;
- redistribution classification for each input class;
- conversion outputs and coverage-matrix locations.

Developer-specific absolute source paths live in an ignored `conversion.local.json`. Environment variables or explicit CLI arguments may override that local configuration. Generated manifests record hashes, not private absolute paths.

## 5. Git and worktree safety

The source repository currently has linked worktrees for `feature/generic-openclaw-framework` and `codex/openclaw-compat-evaluation`. The latter contains compatibility work not present on `main`.

Before extraction:

1. commit the approved documentation on `main`;
2. integrate the completed OpenClaw compatibility branch into the source snapshot;
3. confirm all retained branches and worktrees are clean;
4. record branch names and commit IDs in the provenance document;
5. create the new repository independently rather than moving `.git` or linked worktree directories.

Worktrees are removed only after the new repository passes verification and their commits are reachable from a retained branch. The original repository remains recoverable throughout the migration.

## 6. Extraction stages

### Stage A: documentation and provenance

Track these reusable guides:

- `docs/GPT_TO_PLUGIN_USER_GUIDE.md`;
- `docs/PLUGIN_SKILLS_TECHNICAL_REFERENCE.md`;
- `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`.

Create a provenance manifest with source commits and a file-classification map.

### Stage B: framework extraction

Copy the generic framework and its synthetic tests into the new `src` layout. Update imports, packaging metadata, and tests without changing external behavior. Product-specific audits remain with their products.

### Stage C: product workspace extraction

Copy the canonical Cool Bible Tutor plugin implementation into `applications/cool-bible-tutor`. Do not copy root-level original GPT documents into the Git repository. Replace developer-specific paths with the source-linkage configuration.

### Stage D: publication templates

Extract marketplace catalogs and GitHub workflows into parameterized templates. Cool Bible Tutor supplies values through its application configuration rather than hard-coded generic-framework constants.

### Stage E: equivalence verification

Verify:

- generic framework tests;
- all Cool Bible Tutor tests and distribution audits;
- deterministic Codex and OpenClaw artifacts;
- exact retrieval and optional semantic-RAG behavior;
- public artifact file and digest equivalence, except for explicitly approved structural changes;
- clean installation from a temporary local marketplace.

No public marketplace update occurs until equivalence verification succeeds.

### Stage F: archive cleanup

After the new repository is accepted, present an exact cleanup list for the original folder. Removing extracted development directories, Git metadata, or worktrees requires separate explicit confirmation. Original instructions and reference files remain.

## 7. Command interfaces

The tracked `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md` defines:

- product launcher commands;
- generic framework packaging commands;
- tests and validation commands;
- local and GitHub marketplace installation;
- GitHub release and ClawHub retry operations;
- commands that require explicit approval.

PowerShell is the initial stable interface. Product-specific browser tools may provide GUI workflows. A generic conversion GUI is outside this migration and can be designed after the command contracts stabilize.

## 8. Security and publication guarantees

- Extraction is allowlist-based.
- No secrets, private review history, caches, virtual environments, or developer-specific paths enter public artifacts.
- Large downloads require explicit user consent and cryptographic verification.
- Plugin corpora and vector indexes remain plugin-owned.
- Shared caches contain only compatible runtimes and embedding models.
- The marketplace builder refuses unsafe destinations and performs atomic replacement.
- Immutable releases cannot be overwritten by a same-version publication.

## 9. Testing and acceptance criteria

The migration is complete when:

1. `convert-gpt-application` is an independent Git repository with the target layout.
2. The three conversion and command guides are tracked.
3. The generic framework installs in editable mode and its synthetic tests pass on Windows.
4. Cool Bible Tutor tests and audits pass from its new application workspace.
5. The Codex and OpenClaw artifacts rebuild deterministically.
6. A temporary marketplace install works in a new Codex task.
7. No raw GPT source file is accidentally tracked in the new repository.
8. The public marketplace remains unchanged until a separately reviewed publication step.
9. The original repository remains intact until a separately approved cleanup operation.

## 10. Deferred work

The following are intentionally outside the initial extraction:

- a graphical conversion application;
- automatic semantic decomposition of arbitrary GPT instructions without human review;
- public marketplace publication of a new plugin version;
- deletion of the current source repository or its source materials;
- merging `rag_subsystem` into the conversion repository;
- universal-directory or ClawHub admission decisions.
