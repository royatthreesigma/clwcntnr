#!/usr/bin/env python3
"""
Show database-level stats: size, table sizes, active connections.

Usage:
    python3 scripts/db_stats.py
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
            # Database size
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database())) AS db_size")
            db_size = cur.fetchone()["db_size"]

            # Table sizes
            cur.execute("""
                SELECT
                    schemaname || '.' || relname AS table_name,
                    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
                    pg_size_pretty(pg_relation_size(relid)) AS data_size,
                    n_live_tup AS estimated_rows
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
                LIMIT 20
            """)
            tables = cur.fetchall()

            # Active connections
            cur.execute("""
                SELECT
                    pid, usename, application_name, state,
                    query_start::text,
                    LEFT(query, 80) AS query_preview
                FROM pg_stat_activity
                WHERE datname = current_database()
                  AND pid != pg_backend_pid()
                ORDER BY query_start DESC NULLS LAST
            """)
            connections = cur.fetchall()

        print("=" * 60)
        print("DATABASE STATS")
        print("=" * 60)

        print(f"\n  Database size: {db_size}")

        print(f"\n  Top tables by size:")
        print(f"  {'Table':40s} {'Total':>10s} {'Data':>10s} {'~Rows':>10s}")
        print(f"  {'-'*72}")
        for t in tables:
            print(f"  {t['table_name']:40s} {t['total_size']:>10s} {t['data_size']:>10s} {t['estimated_rows']:>10,d}")

        print(f"\n  Active connections: {len(connections)}")
        if connections:
            for c in connections:
                state = c["state"] or "unknown"
                app = c["application_name"] or ""
                print(f"    PID {c['pid']}  user={c['usename']}  state={state}  app={app}")
                if c["query_preview"]:
                    print(f"      {c['query_preview']}")

        print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
