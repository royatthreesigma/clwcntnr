"""
Shared database helpers for sandbox skills.

Provides three entry points:
  - execute_query(sql, params)  — SELECT → list[dict]  (max 500 rows)
  - execute_write(sql, params)  — INSERT/UPDATE/DELETE/DDL → int (affected rows)
  - get_connection()            — context manager → raw psycopg2 connection
"""

import os
import json
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

MAX_ROWS = 500


def _connect():
    """Create a new psycopg2 connection using environment variables."""
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "clwdb"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )


class _Encoder(json.JSONEncoder):
    """Handle date/datetime/Decimal/memoryview when converting rows."""

    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, memoryview):
            return o.tobytes().decode("utf-8", errors="replace")
        return super().default(o)


def _normalise_row(row):
    """Convert a RealDictRow to a plain dict with JSON-safe values."""
    out = {}
    for k, v in row.items():
        if isinstance(v, (date, datetime)):
            out[k] = v.isoformat()
        elif isinstance(v, Decimal):
            out[k] = float(v)
        elif isinstance(v, memoryview):
            out[k] = v.tobytes().decode("utf-8", errors="replace")
        else:
            out[k] = v
    return out


# ── public API ──────────────────────────────────────────────


def execute_query(sql, params=None):
    """Run a SELECT and return up to MAX_ROWS rows as a list of dicts.

    Args:
        sql:    SQL string (should be a SELECT or other row-returning query).
        params: Optional tuple/list/dict of bind parameters for %s / %(name)s.

    Returns:
        list[dict] – each dict is one row, keyed by column name.

    Raises:
        psycopg2.Error on any database-level failure.
    """
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchmany(MAX_ROWS)
        conn.rollback()  # read-only — release any held locks
        return [_normalise_row(r) for r in rows]
    finally:
        conn.close()


def execute_write(sql, params=None):
    """Run an INSERT / UPDATE / DELETE / DDL statement and commit.

    Args:
        sql:    SQL string.
        params: Optional bind parameters.

    Returns:
        int – number of affected rows (``cursor.rowcount``).
             For DDL (CREATE TABLE, etc.) this is typically -1.

    Raises:
        psycopg2.Error on any database-level failure (transaction is rolled back).
    """
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            affected = cur.rowcount
        conn.commit()
        return affected
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_connection():
    """Context manager yielding a raw psycopg2 connection.

    Use this when you need multi-statement transactions or other
    advanced features (COPY, LISTEN/NOTIFY, server-side cursors, etc.).

    The connection is **not** auto-committed — call ``conn.commit()``
    explicitly.  The connection is closed when the block exits.

    Example::

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("BEGIN")
                cur.execute("INSERT INTO t (x) VALUES (%s)", (1,))
                cur.execute("INSERT INTO t (x) VALUES (%s)", (2,))
                conn.commit()
    """
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()
