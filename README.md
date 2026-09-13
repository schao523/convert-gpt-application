# Obvious One GPT Application Conversion Framework

This repository converts existing GPT application instructions and reference files into tested, redistributable plugins of skills.

It is the development layer in a three-repository boundary:

- Original GPT application folders retain instructions and reference files.
- This repository owns reusable conversion tooling and active application workspaces.
- `schao523/obvious-one-plugins` contains audited public marketplace artifacts.

The `rag_subsystem` project remains an independently installable dependency. Runtime and embedding models may be cached compatibly, while each plugin owns its corpora, PDFs, structured databases, vector indexes, application identity, and namespace.

See `docs/GPT_TO_PLUGIN_USER_GUIDE.md`, `docs/PLUGIN_SKILLS_TECHNICAL_REFERENCE.md`, and `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md` after documentation extraction.
