"""Tests for skills/db-operations/scripts/db_stats.py"""

import pytest

pytestmark = pytest.mark.execution


class TestDbStats:
    def test_stats_report(self, run_script):
        """Prints database size, table sizes, and connection info."""
        _, _, out = run_script("db_stats", argv=["db_stats.py"], results=[
            # database size
            [{"db_size": "25 MB"}],
            # table sizes
            [
                {"table_name": "public.users", "total_size": "8192 bytes",
                 "data_size": "8192 bytes", "estimated_rows": 150},
            ],
            # active connections
            [],
        ])
        assert "DATABASE STATS" in out
        assert "25 MB" in out
        assert "public.users" in out
        assert "150" in out

    def test_with_connections(self, run_script):
        _, _, out = run_script("db_stats", argv=["db_stats.py"], results=[
            [{"db_size": "10 MB"}],
            [],
            [{"pid": 123, "usename": "postgres", "application_name": "psql",
              "state": "idle", "query_start": "2026-01-01 00:00:00",
              "query_preview": "SELECT 1"}],
        ])
        assert "Active connections: 1" in out
        assert "PID 123" in out

    def test_no_tables(self, run_script):
        _, _, out = run_script("db_stats", argv=["db_stats.py"], results=[
            [{"db_size": "7 MB"}],
            [],
            [],
        ])
        assert "7 MB" in out
