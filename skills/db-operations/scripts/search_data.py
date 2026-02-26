#!/usr/bin/env python3
"""
Search for a value across all text columns in all tables of a schema.

Usage:
    python3 scripts/search_data.py <search_term> [schema]

    search_term — text to search for (case-insensitive ILIKE %%term%%)
    schema      — default 'public'
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor


TEXT_TYPES = {"text", "character varying", "character", "varchar", "char", "name"}


def main():
    if len(sys.argv) < 2:
        print("Usage: search_data.py <search_term> [schema]")
        sys.exit(1)

    term = sys.argv[1]
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
            # Get all tables + text columns
            cur.execute("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND data_type IN ('text', 'character varying', 'character', 'varchar', 'char', 'name')
                ORDER BY table_name, ordinal_position
            """, (schema,))
            col_rows = cur.fetchall()

        if not col_rows:
            print(f"No text columns found in schema '{schema}'.")
            return

        # Group by table
        table_cols = {}
        for r in col_rows:
            table_cols.setdefault(r["table_name"], []).append(r["column_name"])

        print(f"Searching for '{term}' in {schema}...\n")
        found_any = False

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for table, cols in table_cols.items():
                conditions = " OR ".join(
                    f'"{c}" ILIKE %s' for c in cols
                )
                params = [f"%{term}%"] * len(cols)

                cur.execute(
                    f'SELECT * FROM "{schema}"."{table}" WHERE {conditions} LIMIT 5',
                    params,
                )
                matches = cur.fetchall()
                if matches:
                    found_any = True
                    print(f"  {schema}.{table}  ({len(matches)} match{'es' if len(matches) != 1 else ''} shown, max 5)")
                    for row in matches:
                        # Show only columns that matched
                        for c in cols:
                            val = str(row.get(c, ""))
                            if term.lower() in val.lower():
                                print(f"    {c}: {val[:120]}")
                    print()

        if not found_any:
            print("  No matches found.")
        print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
