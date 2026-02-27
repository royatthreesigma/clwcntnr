"""Skill discovery endpoints – list and read skill definitions from /skills."""

import os
import logging
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from models import ShpblResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/skills", tags=["skills"])

# Skills root – mounted read-only from the host
SKILLS_ROOT = Path("/skills")


def _parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter delimited by ``---`` from a Markdown file."""
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}
    # Find closing ---
    end = stripped.find("---", 3)
    if end == -1:
        return {}
    yaml_block = stripped[3:end]
    try:
        return yaml.safe_load(yaml_block) or {}
    except yaml.YAMLError as exc:
        logger.warning("Failed to parse SKILL.md frontmatter: %s", exc)
        return {}


def _skill_summary(skill_dir: Path) -> dict | None:
    """Return a compact summary dict for a single skill directory."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return None

    content = skill_md.read_text(encoding="utf-8", errors="replace")
    fm = _parse_frontmatter(content)

    return {
        "name": fm.get("name", skill_dir.name),
        "description": fm.get("description", "").strip(),
        "compatibility": fm.get("compatibility", ""),
        "allowed_tools": fm.get("allowed-tools", ""),
        "metadata": fm.get("metadata", {}),
    }


@router.get("/list", response_model=ShpblResponse)
async def list_skills():
    """Return a list of all available skills with name and description."""
    if not SKILLS_ROOT.is_dir():
        return ShpblResponse(
            success=True,
            message="No skills directory found.",
            data={"skills": []},
        )

    skills: list[dict] = []
    for entry in sorted(SKILLS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        summary = _skill_summary(entry)
        if summary is not None:
            skills.append(summary)

    return ShpblResponse(
        success=True,
        message=f"Found {len(skills)} skill(s).",
        data={"skills": skills},
    )


@router.get("/read/{skill_name}", response_model=ShpblResponse)
async def read_skill(skill_name: str):
    """Return the full SKILL.md content for a given skill."""
    skill_dir = SKILLS_ROOT / skill_name
    if not skill_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found.")

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' has no SKILL.md.",
        )

    content = skill_md.read_text(encoding="utf-8", errors="replace")

    # Directories to skip when listing companion files
    _SKIP_DIRS = {
        # Python
        "__pycache__", ".venv", "venv", "env", ".env", ".eggs", "*.egg-info",
        ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".nox",
        # Node / JS
        "node_modules", ".next", ".nuxt", "dist", "build",
        # Version control
        ".git", ".hg", ".svn",
        # IDE / editor
        ".vscode", ".idea", ".vs",
        # Project-specific
        "__scratchpad",
        # Misc caches & output
        ".cache", ".coverage", "htmlcov", ".hypothesis",
    }

    # File extensions to skip
    _SKIP_EXTS = (
        ".pyc", ".pyo", ".pyd",       # Python bytecode
        ".so", ".dylib", ".dll",       # native extensions
        ".egg", ".whl",                # packaged distributions
        ".DS_Store",                   # macOS
    )

    # Also list companion files (scripts, etc.)
    files: list[str] = []
    for root, dirs, filenames in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for fname in filenames:
            if fname.endswith(_SKIP_EXTS) or fname.startswith("."):
                continue
            rel = os.path.relpath(os.path.join(root, fname), skill_dir)
            if rel != "SKILL.md":
                files.append(rel)

    return ShpblResponse(
        success=True,
        message=f"Skill '{skill_name}' loaded.",
        data={
            "name": skill_name,
            "content": content,
            "files": sorted(files),
        },
    )
