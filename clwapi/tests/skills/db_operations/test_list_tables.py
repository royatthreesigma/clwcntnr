"""Tests for skills/db-operations/scripts/list_tables.py"""

import pytest

pytestmark = pytest.mark.execution


class TestListTables:
    def test_lists_tables_with_row_counts(self, run_script):
        """Tables and their row counts are printed in a formatted table."""
        _, _, out = run_script("list_tables", argv=["list_tables.py"], results=[
            # 1st query: information_schema.tables
            [{"table_name": "users"}, {"table_name": "orders"}],
            # 2nd query: COUNT(*) for 'users'
            [{"cnt": 150}],
            # 3rd query: COUNT(*) for 'orders'
            [{"cnt": 42}],
        ])
        assert "users" in out
        assert "orders" in out
        assert "150" in out
        assert "42" in out
        assert "Total: 2 table(s)" in out

    def test_empty_schema(self, run_script):
        """When no tables exist, a helpful message is printed."""
        _, _, out = run_script("list_tables", argv=["list_tables.py", "empty"], results=[
            [],  # no tables
        ])
        assert "No tables found" in out

    def test_custom_schema(self, run_script):
        """A schema argument is passed through correctly."""
        _, cur, out = run_script("list_tables", argv=["list_tables.py", "analytics"], results=[
            [{"table_name": "events"}],
            [{"cnt": 99}],
        ])
        # The first execute should have received 'analytics' as the schema param
        sql, params = cur._calls[0]
        assert params == ("analytics",)

    def test_output_header(self, run_script):
        """Output starts with a formatted header line."""
        _, _, out = run_script("list_tables", argv=["list_tables.py"], results=[
            [{"table_name": "t"}],
            [{"cnt": 1}],
        ])
        assert "Table" in out
        assert "Rows" in out
