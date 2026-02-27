"""Tests for skills/db-operations/scripts/describe_table.py"""

import pytest

pytestmark = pytest.mark.execution


class TestDescribeTable:
    def test_describes_columns(self, run_script):
        """Columns, types, and nullability are printed."""
        _, _, out = run_script("describe_table", argv=["describe_table.py", "users"], results=[
            # columns query
            [
                {"column_name": "id", "data_type": "integer",
                 "character_maximum_length": None, "is_nullable": "NO",
                 "column_default": "nextval('users_id_seq')"},
                {"column_name": "email", "data_type": "character varying",
                 "character_maximum_length": 255, "is_nullable": "YES",
                 "column_default": None},
            ],
            # row count
            [{"cnt": 100}],
            # indexes
            [{"indexname": "users_pkey", "indexdef": "CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id)"}],
            # foreign keys
            [],
        ])
        assert "id" in out
        assert "integer" in out
        assert "email" in out
        assert "character varying(255)" in out
        assert "100" in out
        assert "users_pkey" in out

    def test_table_not_found(self, run_script):
        """When no columns are returned, prints not-found message."""
        _, _, out = run_script("describe_table", argv=["describe_table.py", "nonexistent"], results=[
            [],  # no columns
        ])
        assert "not found" in out or "no columns" in out.lower()

    def test_custom_schema(self, run_script):
        _, cur, out = run_script("describe_table",
            argv=["describe_table.py", "events", "analytics"],
            results=[
                [{"column_name": "id", "data_type": "integer",
                  "character_maximum_length": None, "is_nullable": "NO",
                  "column_default": None}],
                [{"cnt": 5}],
                [],
                [],
            ])
        sql, params = cur._calls[0]
        assert params == ("analytics", "events")

    def test_foreign_keys_shown(self, run_script):
        _, _, out = run_script("describe_table", argv=["describe_table.py", "orders"], results=[
            [{"column_name": "user_id", "data_type": "integer",
              "character_maximum_length": None, "is_nullable": "NO",
              "column_default": None}],
            [{"cnt": 10}],
            [],
            [{"constraint_name": "fk_user", "column_name": "user_id",
              "ref_schema": "public", "ref_table": "users", "ref_column": "id"}],
        ])
        assert "fk_user" in out
        assert "users" in out

    def test_no_args_exits(self, run_script):
        with pytest.raises(SystemExit) as exc_info:
            run_script("describe_table", argv=["describe_table.py"], results=[])
        assert exc_info.value.code == 1
