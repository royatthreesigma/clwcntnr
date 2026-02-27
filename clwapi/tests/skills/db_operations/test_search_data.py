"""Tests for skills/db-operations/scripts/search_data.py"""

import pytest

pytestmark = pytest.mark.execution


class TestSearchData:
    def test_finds_matches(self, run_script):
        """Matching rows are printed with the matched column values."""
        _, _, out = run_script("search_data", argv=["search_data.py", "alice"], results=[
            # text columns query
            [
                {"table_name": "users", "column_name": "email"},
                {"table_name": "users", "column_name": "name"},
            ],
            # search results for users
            [{"id": 1, "email": "alice@example.com", "name": "Alice"}],
        ])
        assert "alice@example.com" in out
        assert "users" in out

    def test_no_matches(self, run_script):
        _, _, out = run_script("search_data", argv=["search_data.py", "zzz_nonexistent"], results=[
            [{"table_name": "users", "column_name": "email"}],
            [],  # no matches
        ])
        assert "No matches found" in out

    def test_no_text_columns(self, run_script):
        _, _, out = run_script("search_data", argv=["search_data.py", "test"], results=[
            [],  # no text columns in schema
        ])
        assert "No text columns" in out

    def test_no_args_exits(self, run_script):
        with pytest.raises(SystemExit) as exc_info:
            run_script("search_data", argv=["search_data.py"], results=[])
        assert exc_info.value.code == 1
