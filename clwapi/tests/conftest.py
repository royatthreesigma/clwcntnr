"""Shared fixtures for the skill testing framework."""

import sys
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from tests.helpers import SKILLS_ROOT, discover_skill_dirs, parse_frontmatter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def skills_root():
    """Path to the project's skills/ directory."""
    return SKILLS_ROOT


@pytest.fixture
def fake_skill(tmp_path):
    """Factory fixture — create a temporary skill directory for testing.

    Usage:
        skill_dir = fake_skill("my-skill", frontmatter={"name": "my-skill", ...}, body="# Docs")
    """
    def _factory(name: str, *, frontmatter: dict | None = None, body: str = ""):
        skill_dir = tmp_path / name
        skill_dir.mkdir()
        fm = frontmatter or {"name": name, "description": f"Test skill {name}"}
        content = "---\n" + yaml.dump(fm, default_flow_style=False) + "---\n" + body
        (skill_dir / "SKILL.md").write_text(content)
        return skill_dir

    return _factory


# ---------------------------------------------------------------------------
# Mock DB helpers  (used by execution tests for db-operations & similar)
# ---------------------------------------------------------------------------


class MockCursor:
    """A configurable mock cursor that behaves like psycopg2 RealDictCursor.

    Set ``results`` to a list-of-lists.  Each ``execute()`` call pops from
    the front so sequential queries get different return values.
    """

    def __init__(self, results: list[list[dict]] | None = None, description=True):
        self._results_queue: list[list[dict]] = list(results or [])
        self._current: list[dict] = []
        self.description = description  # None => write statement
        self.rowcount = 0

    def execute(self, sql, params=None):
        if self._results_queue:
            self._current = self._results_queue.pop(0)
        else:
            self._current = []
        self.rowcount = len(self._current)

    def fetchall(self):
        return self._current

    def fetchone(self):
        return self._current[0] if self._current else None

    def fetchmany(self, size=None):
        if size is None:
            return self._current
        return self._current[:size]

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


class MockConnection:
    """A mock psycopg2 connection that returns a pre-configured MockCursor."""

    def __init__(self, cursor: MockCursor):
        self._cursor = cursor
        self.autocommit = False

    def cursor(self, **kwargs):
        return self._cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


@pytest.fixture
def mock_db():
    """Factory fixture: create a mock psycopg2.connect that returns
    a MockConnection with pre-loaded query results.

    Usage:
        conn, cur = mock_db([
            [{"schema_name": "public"}],       # result for 1st execute()
            [{"table_name": "users"}],          # result for 2nd execute()
        ])
    Returns (MockConnection, MockCursor) so tests can inspect state.
    """
    def _factory(results: list[list[dict]], description=True):
        cur = MockCursor(results=results, description=description)
        conn = MockConnection(cursor=cur)
        return conn, cur

    return _factory


def import_script(script_path: Path):
    """Import a script's module by file path so we can call main().

    Adds the script's parent directory to sys.path temporarily.
    Returns the imported module.
    """
    parent = str(script_path.parent)
    module_name = script_path.stem

    # Avoid import conflicts by making the module name unique
    unique_name = f"_skill_script_{script_path.parent.parent.name}_{module_name}"

    if parent not in sys.path:
        sys.path.insert(0, parent)

    spec = importlib.util.spec_from_file_location(unique_name, script_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = mod
    spec.loader.exec_module(mod)
    return mod
