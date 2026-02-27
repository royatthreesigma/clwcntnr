#!/usr/bin/env python3
"""
Preview the first N rows of a table.

Usage:
    python3 scripts/preview_table.py <table> [limit] [schema]

    table   — table name (required)
    limit   — number of rows, default 10
    schema  — default 'public'
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime
from decimal import Decimal


class _Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def main():
    if len(sys.argv) < 2:
        print("Usage: preview_table.py <table> [limit] [schema]")
        sys.exit(1)

    table = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    schema = sys.argv[3] if len(sys.argv) > 3 else "public"

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "clwdb"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f'SELECT COUNT(*) AS cnt FROM "{schema}"."{table}"')
            total = cur.fetchone()["cnt"]

            cur.execute(f'SELECT * FROM "{schema}"."{table}" LIMIT %s', (limit,))
            rows = [dict(r) for r in cur.fetchall()]

        if not rows:
            print(f"Table '{schema}.{table}' is empty.")
            return

        cols = list(rows[0].keys())
        widths = {c: len(c) for c in cols}
        str_rows = []
        for row in rows:
            sr = {}
            for c in cols:
                val = row[c]
                s = (
                    json.dumps(val, cls=_Encoder)
                    if isinstance(val, (dict, list))
                    else str(val) if val is not None else "NULL"
                )
                sr[c] = s
                widths[c] = max(widths[c], min(len(s), 50))
            str_rows.append(sr)

        print(f"\n  {schema}.{table}  (showing {len(rows)} of {total:,d})\n")

        header = "  ".join(c.ljust(widths[c]) for c in cols)
        print(header)
        print("  ".join("-" * widths[c] for c in cols))
        for sr in str_rows:
            print("  ".join(sr[c][:50].ljust(widths[c]) for c in cols))

        if total > len(rows):
            print(f"\n  ... {total - len(rows):,d} more row(s)")
        print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
