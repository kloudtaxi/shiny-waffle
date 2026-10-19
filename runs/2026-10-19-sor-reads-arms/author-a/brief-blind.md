# Brief for Author A (blind workspace): declared read tools and a conventions page

You are a data engineer at Northstar Industrial Systems. An AI agent will answer service-level
questions about support tickets, given a ticket number: severity, whether a service level was
breached, what Northstar owes, who must be engaged or notified and by when, and what the customer
must do. The agent reaches the company's systems of record only through what you build here. You
build two things.

## Your inputs (read these and nothing else)

- `inputs/schema.md`: the database's tables, columns, types and sample rows.
- These documents, which are the company's own:
  - `inputs/documents/sla_schedule_v1.md`
  - `inputs/documents/sla_schedule_v2.md`
  - `inputs/documents/acme_support_schedule_c.md`
  - `inputs/documents/blueriver_support_terms.md`
  - `inputs/documents/cedar_support_terms.md`
  - `inputs/documents/support_severity_guide.md`
  - `inputs/documents/support_escalation_procedure.md`
  - `inputs/documents/support_org_chart.md`
  - `inputs/documents/holiday_calendar.md`
- MCP Toolbox for Databases' own public documentation at https://mcp-toolbox.dev/documentation/
  (and its GitHub repo), for the `tools.yaml` format and the SQLite source and tool types.

**Read only the files in this directory's `inputs/` folder** (and the Toolbox documentation above).
Don't look for other files on this machine.

## Deliverable 1: `out/tools.yaml`

A `tools.yaml` for MCP Toolbox v1.14.0:
- **One SQLite source.** Its database path is `${SOR_DB}` (an environment variable).
- **Declared tools**, all in one toolset named `declared`, covering what the agent needs to read
  for a ticket: the ticket, its event history, the customer and account it belongs to, any service
  credits already issued, maintenance notices, the support staff, and anything else the schema
  holds that bears on these questions.

Rules:
- **Stored values only.** Select columns as stored. No computed or derived columns, no time-zone
  conversion, no CASE logic, no aggregation. Joins are fine if they return stored columns.
- **Bound parameters only.** Every value the agent supplies is a typed parameter bound to the
  statement. Never use `templateParameters`, and never build SQL from text.
- Give each tool a clear name and a description that says what it returns and how to call it.
- Read-only: SELECT statements only.

## Deliverable 2: `out/conventions.md`

The context an agent writing its own SQL against this database would be given (schema notes,
conventions, example queries), as a data team would document it:
- what each table and column means, and how the tables relate (keys, identifiers);
- conventions, **only as the documents and the data themselves state them**, such as formats,
  units, time zones and identifiers. Don't invent rules, and don't interpret the service-level
  terms beyond what the documents say;
- 6–10 example questions, each with the SQL that answers it. They must be generic, not about
  specific tickets you saw in the samples.

## Also write `out/file-list.md`

Every file and URL you read, in order.

Write only these three files, in `out/`.
