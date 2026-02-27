"""Generic skill validation tests.

Auto-discovers all skills under ``skills/`` and validates their structure
against the Agent Skills specification.  Adding a new skill directory with
a valid SKILL.md is all that's needed — these tests pick it up automatically.

Run only validation tests:
    pytest -m validation
"""

import py_compile
import re
from pathlib import Path

import pytest

from tests.helpers import SKILLS_ROOT, discover_skill_dirs, parse_frontmatter

# ---------------------------------------------------------------------------
# Parametrise over every skill directory
# ---------------------------------------------------------------------------

_SKILL_DIRS = discover_skill_dirs()
_SKILL_IDS = [d.name for d in _SKILL_DIRS]

# Guard: at least one skill must exist for CI to be meaningful
pytestmark = pytest.mark.validation


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


class TestSkillDiscovery:
    def test_skills_directory_exists(self, skills_root):
        assert skills_root.is_dir(), "skills/ directory does not exist"

    def test_at_least_one_skill(self):
        assert len(_SKILL_DIRS) > 0, "No skills found under skills/"


# ---------------------------------------------------------------------------
# Structure & frontmatter (parametrised per skill)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("skill_dir", _SKILL_DIRS, ids=_SKILL_IDS)
class TestSkillStructure:
    """Validates each skill against the Agent Skills spec."""

    # -- SKILL.md presence --------------------------------------------------

    def test_has_skill_md(self, skill_dir: Path):
        assert (skill_dir / "SKILL.md").is_file()

    # -- Required fields ----------------------------------------------------

    def test_frontmatter_has_name(self, skill_dir: Path):
        fm = self._fm(skill_dir)
        assert "name" in fm, "Frontmatter missing required field 'name'"

    def test_frontmatter_has_description(self, skill_dir: Path):
        fm = self._fm(skill_dir)
        assert "description" in fm, "Frontmatter missing required field 'description'"

    # -- name rules ---------------------------------------------------------

    def test_name_matches_directory(self, skill_dir: Path):
        fm = self._fm(skill_dir)
        assert fm.get("name") == skill_dir.name, (
            f"Frontmatter name '{fm.get('name')}' must match directory name '{skill_dir.name}'"
        )

    def test_name_max_length(self, skill_dir: Path):
        name = self._fm(skill_dir).get("name", "")
        assert len(name) <= 64, f"name '{name}' exceeds 64 characters"

    def test_name_format(self, skill_dir: Path):
        name = self._fm(skill_dir).get("name", "")
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name), (
            f"name '{name}' must be lowercase alphanumeric + single hyphens, "
            "no leading/trailing/consecutive hyphens"
        )

    # -- description rules --------------------------------------------------

    def test_description_not_empty(self, skill_dir: Path):
        desc = str(self._fm(skill_dir).get("description", "")).strip()
        assert len(desc) >= 1, "description must not be empty"

    def test_description_max_length(self, skill_dir: Path):
        desc = str(self._fm(skill_dir).get("description", "")).strip()
        assert len(desc) <= 1024, f"description exceeds 1024 characters ({len(desc)})"

    # -- optional field constraints -----------------------------------------

    def test_compatibility_max_length(self, skill_dir: Path):
        fm = self._fm(skill_dir)
        compat = fm.get("compatibility")
        if compat is not None:
            assert len(str(compat)) <= 500, "compatibility exceeds 500 characters"

    def test_metadata_is_dict(self, skill_dir: Path):
        fm = self._fm(skill_dir)
        meta = fm.get("metadata")
        if meta is not None:
            assert isinstance(meta, dict), "metadata must be a key-value mapping"

    # -- Scripts compilation ------------------------------------------------

    def test_scripts_compile(self, skill_dir: Path):
        """Every .py file under scripts/ must be syntactically valid."""
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.is_dir():
            pytest.skip("No scripts/ directory")
        for pyfile in sorted(scripts_dir.glob("*.py")):
            try:
                py_compile.compile(str(pyfile), doraise=True)
            except py_compile.PyCompileError as exc:
                pytest.fail(f"{pyfile.name} has a syntax error: {exc}")

    # -- Referenced files exist ---------------------------------------------

    def test_referenced_scripts_exist(self, skill_dir: Path):
        """Script filenames mentioned in SKILL.md should actually exist."""
        content = (skill_dir / "SKILL.md").read_text()
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.is_dir():
            pytest.skip("No scripts/ directory")

        existing = {f.name for f in scripts_dir.iterdir() if f.is_file()}
        # Only match explicit scripts/ path references (e.g. `scripts/foo.py`)
        mentioned = set(re.findall(r"scripts/([\w-]+\.(?:py|sh|sql))", content))
        missing = mentioned - existing
        assert not missing, f"SKILL.md references files not found in scripts/: {missing}"

    # -- helper -------------------------------------------------------------

    @staticmethod
    def _fm(skill_dir: Path) -> dict:
        return parse_frontmatter((skill_dir / "SKILL.md").read_text())
