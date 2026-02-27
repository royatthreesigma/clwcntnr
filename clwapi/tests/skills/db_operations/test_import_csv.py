"""Tests for skills/db-operations/scripts/import_csv.py"""

import os

import pytest

pytestmark = pytest.mark.execution


class TestImportCsv:
    def test_imports_into_existing_table(self, run_script, tmp_path):
        """Imports CSV rows into an existing table."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,email\nAlice,alice@test.com\nBob,bob@test.com\n")

        conn, _, out = run_script("import_csv",
            argv=["import_csv.py", str(csv_file), "users"],
            results=[
                # table exists check
                [{"count": 1}],
                # insert row 1 (execute returns empty)
                [],
                # insert row 2
                [],
            ])
        assert "Imported 2 rows" in out
        assert conn.committed

    def test_creates_table_if_not_exists(self, run_script, tmp_path):
        csv_file = tmp_path / "new.csv"
        csv_file.write_text("col_a,col_b\nfoo,bar\n")

        _, cur, out = run_script("import_csv",
            argv=["import_csv.py", str(csv_file), "new_table"],
            results=[
                # table exists check — fetchone returns (0,)
                [{"count": 0}],
                # CREATE TABLE
                [],
                # INSERT
                [],
            ])
        assert "Created table" in out
        assert "Imported 1 rows" in out

    def test_file_not_found_exits(self, run_script):
        with pytest.raises(SystemExit) as exc_info:
            run_script("import_csv",
                argv=["import_csv.py", "/nonexistent/file.csv", "t"],
                results=[])
        assert exc_info.value.code == 1

    def test_no_args_exits(self, run_script):
        with pytest.raises(SystemExit) as exc_info:
            run_script("import_csv", argv=["import_csv.py"], results=[])
        assert exc_info.value.code == 1
