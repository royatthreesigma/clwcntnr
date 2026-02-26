#!/usr/bin/env python3
"""
List all schemas in the database.

Usage:
    python3 scripts/list_schemas.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "clwdb"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT LIKE 'pg_%%'
                  AND schema_name != 'information_schema'
                ORDER BY schema_name
            """
            )
            schemas = cur.fetchall()

        print(f"{'Schema':30s}")
        print("-" * 30)
        for row in schemas:
            print(f"{row['schema_name']:30s}")
        print(f"\nTotal: {len(schemas)} schema(s)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
