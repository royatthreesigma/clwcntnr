#!/usr/bin/env python3
"""
List all tables in a schema with row counts.

Usage:
    python3 scripts/list_tables.py [schema]

    schema  — defaults to 'public'
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    schema = sys.argv[1] if len(sys.argv) > 1 else "public"

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "clwdb"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema,))
            tables = [r["table_name"] for r in cur.fetchall()]

            if not tables:
                print(f"No tables found in schema '{schema}'.")
                return

            print(f"{'Table':40s} {'Rows':>10s}")
            print("-" * 52)
            for table in tables:
                cur.execute(f'SELECT COUNT(*) AS cnt FROM "{schema}"."{table}"')
                cnt = cur.fetchone()["cnt"]
                print(f"{table:40s} {cnt:>10,d}")

            print(f"\nTotal: {len(tables)} table(s) in '{schema}'")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
