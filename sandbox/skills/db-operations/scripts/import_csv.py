#!/usr/bin/env python3
"""
Import a CSV file into a table (creates the table if it doesn't exist).

Usage:
    python3 scripts/import_csv.py <csv_file> <table> [schema]

    csv_file — path to CSV with a header row
    table    — target table name
    schema   — default 'public'

If the table already exists, rows are appended. Column names must match.
If the table doesn't exist, it's created with all TEXT columns — you can
ALTER types afterwards.
"""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    if len(sys.argv) < 3:
        print("Usage: import_csv.py <csv_file> <table> [schema]")
        sys.exit(1)

    csv_path = sys.argv[1]
    table = sys.argv[2]
    schema = sys.argv[3] if len(sys.argv) > 3 else "public"

    if not os.path.isfile(csv_path):
        print(f"File not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        if not columns:
            print("CSV has no header row.", file=sys.stderr)
            sys.exit(1)
        rows = list(reader)

    if not rows:
        print("CSV has no data rows.")
        return

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "clwdb"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if table exists
            cur.execute(
                """
                SELECT COUNT(*) AS count FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            """,
                (schema, table),
            )
            exists = cur.fetchone()["count"] > 0

            if not exists:
                col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
                cur.execute(f'CREATE TABLE "{schema}"."{table}" ({col_defs})')
                print(
                    f"Created table {schema}.{table} with {len(columns)} TEXT columns."
                )

            # Insert rows
            placeholders = ", ".join(["%s"] * len(columns))
            col_names = ", ".join(f'"{c}"' for c in columns)
            insert_sql = f'INSERT INTO "{schema}"."{table}" ({col_names}) VALUES ({placeholders})'

            for row in rows:
                values = [row.get(c) for c in columns]
                cur.execute(insert_sql, values)

            conn.commit()

        print(f"Imported {len(rows)} rows into {schema}.{table}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
