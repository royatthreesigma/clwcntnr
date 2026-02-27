"""Tests for skills/db-operations/scripts/run_query.py"""

import sys

import pytest

pytestmark = pytest.mark.execution


class TestRunQuery:
    def test_select_query_output(self, run_script):
        """SELECT queries print column headers and rows."""
        _, _, out = run_script("run_query", argv=["run_query.py", "SELECT 1"], results=[
            [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        ])
        assert "id" in out
        assert "name" in out
        assert "Alice" in out
        assert "Bob" in out
        assert "(2 rows)" in out

    def test_select_single_row(self, run_script):
        _, _, out = run_script("run_query", argv=["run_query.py", "SELECT 1"], results=[
            [{"val": 42}],
        ])
        assert "42" in out
        assert "(1 row)" in out  # singular

    def test_select_no_rows(self, run_script):
        _, _, out = run_script("run_query", argv=["run_query.py", "SELECT 1"], results=[
            [],
        ])
        assert "0 rows" in out

    def test_write_query(self, run_script):
        """INSERT/UPDATE/DELETE prints affected row count."""
        _, cur, out = run_script(
            "run_query",
            argv=["run_query.py", "INSERT INTO t VALUES (1)"],
            results=[[]],
            description=None,  # no description => write statement
        )
        assert "OK" in out
        assert "Rows affected" in out

    def test_no_args_exits(self, run_script):
        """Calling without SQL argument should exit with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            run_script("run_query", argv=["run_query.py"], results=[])
        assert exc_info.value.code == 1
