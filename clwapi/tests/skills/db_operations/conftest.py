"""Shared fixtures for db-operations skill tests.

Every test file in this directory tests a single script from
``skills/db-operations/scripts/``.  This conftest provides:

* ``script_module(name)`` — imports a script module with psycopg2.connect
  already patched, returning (module, mock_connect) so tests can configure
  the mock cursor's return values before calling ``module.main()``.
"""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "sandbox"
    / "skills"
    / "db-operations"
    / "scripts"
)

# Ensure the scripts directory can be imported from
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class FakeCursor:
    """Cursor that yields pre-loaded results, one per execute() call."""

    def __init__(self):
        self.results: list[list[dict]] = []
        self.description = True  # non-None => SELECT
        self.rowcount = 0
        self._calls: list[tuple] = []

    def add_result(self, rows: list[dict]):
        """Queue a result set for the next execute() call."""
        self.results.append(rows)
        return self  # allow chaining

    def execute(self, sql, params=None):
        self._calls.append((sql, params))
        if self.results:
            self._current = self.results.pop(0)
        else:
            self._current = []
        self.rowcount = len(self._current)

    def fetchall(self):
        return self._current

    def fetchone(self):
        return self._current[0] if self._current else None

    def fetchmany(self, size=None):
        return self._current[:size] if size else self._current

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


class FakeConnection:
    """Mock connection wrapping a FakeCursor."""

    def __init__(self, cursor: FakeCursor):
        self._cursor = cursor
        self.autocommit = False
        self.committed = False

    def cursor(self, **kw):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


@pytest.fixture
def db(monkeypatch):
    """Provide a (FakeConnection, FakeCursor) pair.

    ``psycopg2.connect`` is monkey-patched at the *module level* of the
    script under test.  Tests should call ``cur.add_result(...)`` to queue
    up return values before invoking the script's ``main()``.
    """
    cur = FakeCursor()
    conn = FakeConnection(cur)

    def _fake_connect(**kw):
        return conn

    # Return a triple so the test can also access the connect-function
    return conn, cur, _fake_connect


@pytest.fixture
def run_script(db, monkeypatch, capsys):
    """High-level helper: import a script with DB mocked and return a runner.

    Usage::

        def test_something(run_script):
            conn, cur, out = run_script("list_tables", results=[
                [{"table_name": "users"}],
                [{"cnt": 42}],
            ], argv=["list_tables.py", "public"])

            assert "users" in out
    """
    conn, cur, fake_connect = db

    def _run(
        script_name: str,
        *,
        results: list[list[dict]] | None = None,
        argv: list[str] | None = None,
        description=True,
    ):
        # Queue results
        cur.results.clear()
        cur._calls.clear()
        cur.description = description
        if results:
            for r in results:
                cur.add_result(r)

        # Patch sys.argv
        if argv is not None:
            monkeypatch.setattr(sys, "argv", argv)

        # Import the module fresh each time
        script_path = SCRIPTS_DIR / f"{script_name}.py"
        assert script_path.exists(), f"Script not found: {script_path}"

        unique = f"_test_script_{script_name}"
        spec = importlib.util.spec_from_file_location(unique, script_path)
        mod = importlib.util.module_from_spec(spec)

        # Patch psycopg2.connect before the module executes
        import psycopg2 as _real_psycopg2

        monkeypatch.setattr(_real_psycopg2, "connect", fake_connect)

        # Also ensure the module-level import of psycopg2 uses our patch
        mod.psycopg2 = _real_psycopg2
        sys.modules[unique] = mod
        spec.loader.exec_module(mod)

        # Patch the module's own reference to psycopg2.connect
        if hasattr(mod, "psycopg2"):
            mod.psycopg2.connect = fake_connect

        # Run main
        mod.main()
        captured = capsys.readouterr()
        return conn, cur, captured.out

    return _run
