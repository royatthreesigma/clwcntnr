#!/usr/bin/env python3
"""
Describe a table — columns, types, nullability, defaults.

Usage:
    python3 scripts/describe_table.py <table> [schema]

    table   — table name (required)
    schema  — defaults to 'public'
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    if len(sys.argv) < 2:
        print("Usage: describe_table.py <table> [schema]")
        sys.exit(1)

    table = sys.argv[1]
    schema = sys.argv[2] if len(sys.argv) > 2 else "public"

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "clwdb"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Columns
            cur.execute("""
                SELECT column_name, data_type, character_maximum_length,
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table))
            columns = cur.fetchall()

            if not columns:
                print(f"Table '{schema}.{table}' not found or has no columns.")
                return

            # Row count
            cur.execute(f'SELECT COUNT(*) AS cnt FROM "{schema}"."{table}"')
            row_count = cur.fetchone()["cnt"]

            # Indexes
            cur.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = %s AND tablename = %s
                ORDER BY indexname
            """, (schema, table))
            indexes = cur.fetchall()

            # Foreign keys
            cur.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_schema AS ref_schema,
                    ccu.table_name   AS ref_table,
                    ccu.column_name  AS ref_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = %s
                  AND tc.table_name = %s
            """, (schema, table))
            fkeys = cur.fetchall()

        # Print
        print(f"\n  {schema}.{table}  ({row_count:,d} rows)")
        print(f"  {'='*56}")

        print(f"\n  {'Column':30s} {'Type':20s} {'Nullable':8s} Default")
        print(f"  {'-'*80}")
        for c in columns:
            dtype = c["data_type"]
            if c["character_maximum_length"]:
                dtype += f"({c['character_maximum_length']})"
            nullable = "YES" if c["is_nullable"] == "YES" else "NO"
            default = c["column_default"] or ""
            print(f"  {c['column_name']:30s} {dtype:20s} {nullable:8s} {default}")

        if indexes:
            print(f"\n  Indexes:")
            for idx in indexes:
                print(f"    {idx['indexname']}")
                print(f"      {idx['indexdef']}")

        if fkeys:
            print(f"\n  Foreign keys:")
            for fk in fkeys:
                print(f"    {fk['constraint_name']}: {fk['column_name']} -> {fk['ref_schema']}.{fk['ref_table']}({fk['ref_column']})")

        print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
