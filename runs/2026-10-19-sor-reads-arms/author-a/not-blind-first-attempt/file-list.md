# Author A: files and URLs read

## The `tools.yaml` format used (MCP Toolbox for Databases v1.14.0)

Every page below carries the footer "Last modified October 8, 2026: chore(main): release 1.14.0
(#4159) (6b743ef)". The v1.14.0 release notes (https://github.com/googleapis/mcp-toolbox/releases/tag/v1.14.0,
2026-10-08) list no change to the `tools.yaml` format.

**SQLite source**, from https://mcp-toolbox.dev/integrations/sqlite/source/:

```yaml
kind: source
name: my-sqlite-db
type: "sqlite"
database: "/path/to/database.db"
```

Fields: `type` (required, must be "sqlite"), `database` (required, path to the SQLite file),
`sqlCommenter` (optional).

**SQLite SQL tool**, from https://mcp-toolbox.dev/integrations/sqlite/tools/sqlite-sql/:

```yaml
kind: tool
name: search-users
type: sqlite-sql
source: my-sqlite-db
description: Search users by name and age
parameters:
  - name: name
    type: string
    description: The name to search for
  - name: min_age
    type: integer
    description: Minimum age
statement: SELECT * FROM users WHERE name LIKE ? AND age >= ?
```

"SQLite uses the `?` placeholder for parameters in SQL statements. Parameters are bound in the
order they are provided." Fields: `type`, `source`, `description`, `statement` (required);
`parameters`, `templateParameters` (optional). The page recommends basic parameters only;
`templateParameters` is not used anywhere in this `tools.yaml`.

**Toolset**, from https://mcp-toolbox.dev/documentation/configuration/toolsets/:

```yaml
kind: toolset
name: my_first_toolset
tools:
  - my_first_tool
  - my_second_tool
```

**General format**, from https://mcp-toolbox.dev/documentation/configuration/: one `kind:` block
per YAML document, separated by `---`; environment variables are written `${ENV_NAME}`.

**Parameters and annotations**, from https://mcp-toolbox.dev/documentation/configuration/tools/:
parameter `type` is one of string, integer, float, boolean, array (and map); parameters are
required by default. The annotation example is:

```yaml
annotations:
  readOnlyHint: true
  idempotentHint: true
```

The v1.14.0 `sqlite-sql` source (internal/tools/sqlite/sqlitesql/sqlitesql.go) embeds
`tools.ConfigBase`, where `annotations` live, and passes parameters to the database as an ordered
list. With no annotations set, the tool defaults to destructive annotations, so every tool here sets
`readOnlyHint: true`.

## Read, in order

1. `runs/2026-10-19-sor-reads-arms/author-a/brief.md`
2. `runs/2026-10-19-sor-reads-arms/author-a/schema.md`
3. `dataset/evidence/documents/sla_schedule_v1.md`
4. `dataset/evidence/documents/sla_schedule_v2.md`
5. `dataset/evidence/documents/acme_support_schedule_c.md`
6. `dataset/evidence/documents/blueriver_support_terms.md`
7. `dataset/evidence/documents/cedar_support_terms.md`
8. `dataset/evidence/documents/support_severity_guide.md`
9. `dataset/evidence/documents/support_escalation_procedure.md`
10. `dataset/evidence/documents/support_org_chart.md`
11. `dataset/evidence/documents/holiday_calendar.md`
12. https://mcp-toolbox.dev/documentation/
13. https://mcp-toolbox.dev/integrations/sqlite/source/
14. https://mcp-toolbox.dev/integrations/sqlite/tools/sqlite-sql/
15. https://mcp-toolbox.dev/documentation/configuration/
16. https://mcp-toolbox.dev/documentation/configuration/toolsets/
17. https://mcp-toolbox.dev/documentation/configuration/tools/ (fetched twice)
18. https://github.com/googleapis/mcp-toolbox/releases/tag/v1.14.0
19. https://raw.githubusercontent.com/googleapis/mcp-toolbox/v1.14.0/docs/en/integrations/sqlite/tools/sqlite-sql.md
20. https://raw.githubusercontent.com/googleapis/mcp-toolbox/v1.14.0/internal/tools/sqlite/sqlitesql/sqlitesql.go

To check my work, I parsed `tools.yaml` and ran each of its statements and each example query in `conventions.md`
against an empty in-memory SQLite database built from the column lists in `schema.md`, using a
script in my session scratchpad outside the repository. All 18 tools and 10 examples parse and
bind.

## Context I did not open but had loaded

The agent harness put the repository's `CLAUDE.md`, the user's global `CLAUDE.md` and the user's
memory index into my context automatically at the start of the session, before I read the brief.
I did not open these files, and I did not use them to write these deliverables. Because the brief
lists `CLAUDE.md` as off-limits, I am recording that it was in my context.
