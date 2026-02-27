"""Tests for skills/db-operations/scripts/list_schemas.py"""

import pytest

pytestmark = pytest.mark.execution


class TestListSchemas:
    def test_lists_schemas(self, run_script):
        """Non-system schemas are listed with a count."""
        _, _, out = run_script("list_schemas", argv=["list_schemas.py"], results=[
            [{"schema_name": "public"}, {"schema_name": "analytics"}],
        ])
        assert "public" in out
        assert "analytics" in out
        assert "Total: 2 schema(s)" in out

    def test_single_schema(self, run_script):
        _, _, out = run_script("list_schemas", argv=["list_schemas.py"], results=[
            [{"schema_name": "public"}],
        ])
        assert "public" in out
        assert "Total: 1 schema(s)" in out

    def test_output_has_header(self, run_script):
        _, _, out = run_script("list_schemas", argv=["list_schemas.py"], results=[
            [{"schema_name": "public"}],
        ])
        assert "Schema" in out
        assert "---" in out
