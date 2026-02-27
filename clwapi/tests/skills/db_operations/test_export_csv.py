"""Tests for skills/db-operations/scripts/export_csv.py"""

import os

import pytest

pytestmark = pytest.mark.execution


class TestExportCsv:
    def test_exports_table(self, run_script, tmp_path):
        """Exports rows to a CSV file."""
        out_file = str(tmp_path / "users.csv")
        _, _, out = run_script("export_csv",
            argv=["export_csv.py", "users", out_file],
            results=[
                [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            ])
        assert "Exported 2 rows" in out
        assert os.path.isfile(out_file)
        content = open(out_file).read()
        assert "id,name" in content
        assert "Alice" in content
        assert "Bob" in content

    def test_exports_sql_query(self, run_script, tmp_path):
        out_file = str(tmp_path / "result.csv")
        _, _, out = run_script("export_csv",
            argv=["export_csv.py", "--sql", "SELECT 1 AS val", out_file],
            results=[
                [{"val": 1}],
            ])
        assert "Exported 1 rows" in out

    def test_empty_result(self, run_script, tmp_path):
        out_file = str(tmp_path / "empty.csv")
        _, _, out = run_script("export_csv",
            argv=["export_csv.py", "empty_tbl", out_file],
            results=[
                [],
            ])
        assert "No data" in out
        assert not os.path.isfile(out_file)

    def test_no_args_exits(self, run_script):
        with pytest.raises(SystemExit) as exc_info:
            run_script("export_csv", argv=["export_csv.py"], results=[])
        assert exc_info.value.code == 1
