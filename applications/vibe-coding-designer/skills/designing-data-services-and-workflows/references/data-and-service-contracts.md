# Data and service contracts

## Data

For each entity define stable name, fields and types, required/optional status, validation, uniqueness, relationships, lifecycle, retention, and sensitive-data classification. Choose persistence only from actual requirements. Record indexing and migration needs when applicable.

## Operations

For each command, endpoint, tool, event, or library operation define:

- stable identifier and purpose;
- caller and authorization boundary;
- input and output schema;
- validation and normalized error shape;
- side effects and transaction boundary;
- idempotency, pagination, timeouts, and rate limits when applicable;
- logging, request/correlation identity, and health evidence.

REST, GraphQL, MCP, local functions, queues, and files are alternatives chosen from the system context. Example technologies such as Node.js, Fastify, Express, PostgreSQL, and Prisma are not defaults unless the user selects them.
