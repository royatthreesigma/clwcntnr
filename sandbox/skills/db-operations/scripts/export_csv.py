#!/usr/bin/env python3
"""
Export a table (or query result) to CSV.

Usage:
    python3 scripts/export_csv.py <table> [output_file] [schema]
    python3 scripts/export_csv.py --sql "SELECT ..." [output_file]

    table       — table name
    output_file — path to write CSV (default: /workspace/<table>.csv)
    schema      — default 'public'
"""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    if len(sys.argv) < 2:
        print("Usage: export_csv.py <table> [output_file] [schema]")
        print("       export_csv.py --sql \"SELECT ...\" [output_file]")
        sys.exit(1)

    # Parse args
    if sys.argv[1] == "--sql":
        sql = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else "/workspace/export.csv"
        table_label = "query"
    else:
        table = sys.argv[1]
        schema = sys.argv[3] if len(sys.argv) > 3 else "public"
        output = sys.argv[2] if len(sys.argv) > 2 else f"/workspace/{table}.csv"
        sql = f'SELECT * FROM "{schema}"."{table}"'
        table_label = f"{schema}.{table}"

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "clwdb"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()

        if not rows:
            print(f"No data returned from {table_label}.")
            return

        cols = list(rows[0].keys())
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cols)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Exported {len(rows)} rows to {output}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
