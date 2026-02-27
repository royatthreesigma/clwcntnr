"""Tests for skills/db-operations/scripts/preview_table.py"""

import pytest

pytestmark = pytest.mark.execution


class TestPreviewTable:
    def test_preview_rows(self, run_script):
        """Shows a formatted preview of table rows."""
        _, _, out = run_script("preview_table", argv=["preview_table.py", "users"], results=[
            # COUNT(*)
            [{"cnt": 50}],
            # SELECT * LIMIT 10
            [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
        ])
        assert "Alice" in out
        assert "Bob" in out
        assert "showing 2 of 50" in out
        assert "48 more row(s)" in out

    def test_empty_table(self, run_script):
        _, _, out = run_script("preview_table", argv=["preview_table.py", "empty_tbl"], results=[
            [{"cnt": 0}],
            [],
        ])
        assert "empty" in out.lower()

    def test_custom_limit(self, run_script):
        """A custom limit argument is passed to the query."""
        _, cur, out = run_script("preview_table",
            argv=["preview_table.py", "users", "5"],
            results=[
                [{"cnt": 100}],
                [{"id": i, "name": f"user{i}"} for i in range(5)],
            ])
        # The LIMIT query should use 5
        sql, params = cur._calls[1]
        assert params == (5,)

    def test_no_args_exits(self, run_script):
        with pytest.raises(SystemExit) as exc_info:
            run_script("preview_table", argv=["preview_table.py"], results=[])
        assert exc_info.value.code == 1
