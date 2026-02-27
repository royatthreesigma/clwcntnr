"""Shared helpers for skill tests — importable by test modules."""

import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent
SKILLS_ROOT = REPO_ROOT / "sandbox" / "skills"


def discover_skill_dirs() -> list[Path]:
    """Return all skill directories (dirs that contain SKILL.md)."""
    if not SKILLS_ROOT.is_dir():
        return []
    return sorted(
        d for d in SKILLS_ROOT.iterdir()
        if d.is_dir() and (d / "SKILL.md").is_file()
    )


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter delimited by ``---`` from a Markdown file."""
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}
    end = stripped.find("---", 3)
    if end == -1:
        return {}
    yaml_block = stripped[3:end]
    return yaml.safe_load(yaml_block) or {}
