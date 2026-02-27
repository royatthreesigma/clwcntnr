"""Tests for skills/db-operations/scripts/db_introspect.py"""

import pytest

pytestmark = pytest.mark.execution


class TestDbIntrospect:
    def test_full_report(self, run_script):
        """Produces a report with schemas, tables, and columns."""
        _, _, out = run_script("db_introspect", argv=["db_introspect.py"], results=[
            # schemas
            [{"schema_name": "public"}],
            # tables in public
            [{"table_name": "users"}],
            # row count for users
            [{"cnt": 200}],
            # columns for users
            [
                {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
                {"column_name": "email", "data_type": "text", "is_nullable": "YES"},
            ],
        ])
        assert "INTROSPECTION REPORT" in out
        assert "public" in out
        assert "users" in out
        assert "200" in out
        assert "id" in out
        assert "email" in out

    def test_empty_schema(self, run_script):
        """Schema with no tables shows '(no tables)' message."""
        _, _, out = run_script("db_introspect", argv=["db_introspect.py"], results=[
            [{"schema_name": "empty_schema"}],
            [],  # no tables
        ])
        assert "empty_schema" in out
        assert "(no tables)" in out

    def test_multiple_schemas(self, run_script):
        _, _, out = run_script("db_introspect", argv=["db_introspect.py"], results=[
            [{"schema_name": "public"}, {"schema_name": "analytics"}],
            # public tables
            [{"table_name": "users"}],
            [{"cnt": 10}],
            [{"column_name": "id", "data_type": "integer", "is_nullable": "NO"}],
            # analytics tables
            [{"table_name": "events"}],
            [{"cnt": 500}],
            [{"column_name": "event_id", "data_type": "bigint", "is_nullable": "NO"}],
        ])
        assert "public" in out
        assert "analytics" in out
        assert "users" in out
        assert "events" in out
