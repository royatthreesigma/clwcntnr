#!/usr/bin/env python3
"""
Introspect the workspace database and print a summary.

Self-contained — no dependencies beyond psycopg2 (pre-installed in sandbox).

Run from sandbox:
    python3 scripts/db_introspect.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager


# ---------------------------------------------------------------------------
# Connection helper (self-contained, no lib.db dependency)
# ---------------------------------------------------------------------------


@contextmanager
def _connect():
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "clwdb"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )
    try:
        yield conn
    finally:
        conn.close()


def query(sql, params=None):
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    schemas = query(
        """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT LIKE 'pg_%%'
          AND schema_name != 'information_schema'
        ORDER BY schema_name
        """
    )

    print("=" * 60)
    print("DATABASE INTROSPECTION REPORT")
    print("=" * 60)

    for schema in schemas:
        schema_name = schema["schema_name"]
        print(f"\n--- Schema: {schema_name} ---")

        tables = query(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            (schema_name,),
        )

        if not tables:
            print("  (no tables)")
            continue

        for tbl in tables:
            table_name = tbl["table_name"]

            rows = query(f'SELECT COUNT(*) AS cnt FROM "{schema_name}"."{table_name}"')
            row_count = rows[0]["cnt"] if rows else "?"

            columns = query(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (schema_name, table_name),
            )

            print(f"\n  Table: {table_name}  ({row_count} rows)")
            for col in columns:
                nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                print(
                    f"    - {col['column_name']:30s} {col['data_type']:20s} {nullable}"
                )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
