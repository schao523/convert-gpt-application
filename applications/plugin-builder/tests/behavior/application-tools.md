# Application-tool behavior scenarios

Status: `RUNTIME VERIFIED` for repository-local bundled-tool execution and structural adapter evidence. Target-service execution remains `NOT VERIFIED` unless actually authorized and observed.

- A bundled local tool is classified during planning, approved at W1, materialized with exact files and skill bindings, executed with a direct argument vector, and reported with digest-only process evidence.
- A required failing tool blocks W2 and emits no final ZIP.
- An optional unavailable runtime-native tool remains individually `NOT VERIFIED` through W2 without erasing other passing requirement evidence.
- An MCP adapter is built without credentials and receives structural and binding evidence only when the external service is unavailable.
- Update mode preserves unchanged tool implementations and requires renewed planning and W1 approval for contract or binding changes.
