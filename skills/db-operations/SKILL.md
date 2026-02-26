---
name: db-operations
description: >
    Query, explore, and manage the workspace PostgreSQL database. Use this skill when you
    needs to inspect schemas, list tables, browse data, run SQL queries, create or alter tables,
    insert/update/delete rows, or perform any database operation.
compatibility: Requires the workspace to be running.
allowed-tools: Bash(python3:*) Read
metadata:
    author: wclw
    version: "1.0"
---

# Database Operations

## Overview

The workspace has a PostgreSQL 17 database (`clwdb`). Interact with it using the bundled Python scripts in `scripts/`.

All scripts are self-contained (only need `psycopg2`, pre-installed in sandbox). Connection env vars (`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`) are injected automatically.

---

## Bundled scripts

All scripts connect directly via `psycopg2` — no external library dependencies. Run them in the sandbox with `python3`.

| Script              | Purpose                                             | Usage                                                       |
| ------------------- | --------------------------------------------------- | ----------------------------------------------------------- |
| `db_introspect.py`  | Full database report (all schemas, tables, columns) | `python3 scripts/db_introspect.py`                          |
| `list_schemas.py`   | List schemas                                        | `python3 scripts/list_schemas.py`                           |
| `list_tables.py`    | List tables + row counts                            | `python3 scripts/list_tables.py [schema]`                   |
| `describe_table.py` | Columns, types, indexes, foreign keys               | `python3 scripts/describe_table.py <table> [schema]`        |
| `preview_table.py`  | Quick data peek                                     | `python3 scripts/preview_table.py <table> [limit] [schema]` |
| `run_query.py`      | Run any SQL, formatted output                       | `python3 scripts/run_query.py "<sql>"`                      |
| `db_stats.py`       | DB size, table sizes, connections                   | `python3 scripts/db_stats.py`                               |
| `search_data.py`    | Search text across all tables                       | `python3 scripts/search_data.py <term> [schema]`            |
| `export_csv.py`     | Export table or query to CSV                        | `python3 scripts/export_csv.py <table> [file] [schema]`     |
| `import_csv.py`     | Import CSV into table (auto-creates)                | `python3 scripts/import_csv.py <csv> <table> [schema]`      |

Default schema is always `public` unless specified.

---

## Common workflows

### Explore an unfamiliar database

1. `python3 scripts/db_introspect.py` — get the full picture
2. `python3 scripts/describe_table.py <table>` — drill into a table
3. `python3 scripts/preview_table.py <table>` — see sample data

### Run a one-off query

```bash
python3 scripts/run_query.py "SELECT id, name FROM public.users WHERE active = true LIMIT 20"
```

### Create a table

```bash
python3 scripts/run_query.py "CREATE TABLE IF NOT EXISTS public.events (id SERIAL PRIMARY KEY, name TEXT NOT NULL, payload JSONB, created_at TIMESTAMPTZ DEFAULT NOW())"
```

### Import a CSV

```bash
python3 scripts/import_csv.py /workspace/data.csv events
```

Auto-creates the table if it doesn't exist. Appends rows if it does.

### Export data to CSV

```bash
python3 scripts/export_csv.py users /workspace/users_backup.csv
python3 scripts/export_csv.py --sql "SELECT * FROM public.orders WHERE total > 100" /workspace/big_orders.csv
```

### Search for a value

```bash
python3 scripts/search_data.py "alice@example.com"
```

Searches all text columns across all tables in the schema.

### Check database health

```bash
python3 scripts/db_stats.py
```

---

## Important notes

- **SQL injection prevention**: Always use parameterised queries (`%s` placeholders + `params`). Never interpolate user input directly into SQL strings.
- **Row limits**: `run_query.py` caps output at 500 rows. For larger exports use `scripts/export_csv.py` or paginate with `OFFSET`.
- **Transactions**: Scripts auto-commit writes. For multi-statement transactions, write a custom script using `psycopg2` directly with explicit `conn.commit()` / `conn.rollback()`.
- **Schema convention**: Use `public` as the default schema unless the strictly neccessary.
- **Optional `lib.db`**: The sandbox also ships a `/workspace/lib/db.py` helper module (`get_connection`, `execute_query`, `execute_write`). You can use it in custom scripts if convenient, but it is not required — the bundled scripts are fully self-contained.

## See also

- [Example queries](scripts/example_queries.sql) — common SQL patterns for copy-paste
- [lib.db reference](references/PYTHON_LIB.md) — optional Python helper module docs
