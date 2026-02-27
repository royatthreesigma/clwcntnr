#!/usr/bin/env python3
"""
Run an arbitrary SQL query and print results as a formatted table.

Usage:
    python3 scripts/run_query.py "SELECT * FROM public.users LIMIT 10"
    python3 scripts/run_query.py "INSERT INTO public.logs (msg) VALUES ('test')"
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
        if isinstance(o, memoryview):
            return o.tobytes().decode("utf-8", errors="replace")
        return super().default(o)


def main():
    if len(sys.argv) < 2:
        print("Usage: run_query.py <sql>")
        sys.exit(1)

    sql = sys.argv[1]

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

            if cur.description is not None:
                rows = [dict(r) for r in cur.fetchmany(500)]
                conn.rollback()

                if not rows:
                    print("Query returned 0 rows.")
                    return

                cols = list(rows[0].keys())
                # Calculate column widths
                widths = {c: len(c) for c in cols}
                str_rows = []
                for row in rows:
                    sr = {}
                    for c in cols:
                        val = row[c]
                        s = json.dumps(val, cls=_Encoder) if isinstance(val, (dict, list)) else str(val) if val is not None else "NULL"
                        sr[c] = s
                        widths[c] = max(widths[c], min(len(s), 60))
                    str_rows.append(sr)

                # Header
                header = "  ".join(c.ljust(widths[c]) for c in cols)
                print(header)
                print("  ".join("-" * widths[c] for c in cols))

                for sr in str_rows:
                    print("  ".join(sr[c][:60].ljust(widths[c]) for c in cols))

                print(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")
            else:
                conn.commit()
                print(f"OK. Rows affected: {cur.rowcount}")
    except psycopg2.Error as e:
        print(f"SQL Error: {e.pgerror or e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
