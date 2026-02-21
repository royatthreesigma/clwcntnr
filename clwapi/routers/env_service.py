"""Environment variable management for the sandbox container.

The sandbox .env file lives at /sandbox-env/.env — a volume shared
between clwapi and the sandbox container.  clwapi writes to it;
every command executed in the sandbox auto-sources it.
"""

import os
import logging
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException

from models import ShpblResponse, UpdateEnvVariableRequest, BulkEnvUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/env", tags=["environment"])

# Both clwapi and sandbox mount this volume
ENV_FILE = Path("/sandbox-env/.env")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_env() -> Dict[str, str]:
    """Parse the .env file into a dict.  Ignores comments and blank lines."""
    env: Dict[str, str] = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def _write_env(env: Dict[str, str]) -> None:
    """Atomically write the env dict back to the file."""
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(f"{k}={v}" for k, v in sorted(env.items())) + "\n"
    ENV_FILE.write_text(content)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ShpblResponse)
async def get_env():
    """Return all environment variables currently in the sandbox .env file."""
    env = _read_env()
    return ShpblResponse(
        success=True,
        message=f"{len(env)} variable(s)",
        data={"variables": env},
    )


@router.put("", response_model=ShpblResponse)
async def set_env_variable(request: UpdateEnvVariableRequest):
    """Create or update a single environment variable."""
    env = _read_env()
    env[request.variable_name] = request.value
    _write_env(env)
    logger.info(f"Set env var: {request.variable_name}")
    return ShpblResponse(
        success=True,
        message=f"Set {request.variable_name}",
        data={"variables": env},
    )


@router.delete("/{variable_name}", response_model=ShpblResponse)
async def delete_env_variable(variable_name: str):
    """Delete a single environment variable."""
    env = _read_env()
    if variable_name not in env:
        raise HTTPException(
            status_code=404, detail=f"Variable '{variable_name}' not found"
        )
    del env[variable_name]
    _write_env(env)
    logger.info(f"Deleted env var: {variable_name}")
    return ShpblResponse(
        success=True,
        message=f"Deleted {variable_name}",
        data={"variables": env},
    )


@router.post("/bulk", response_model=ShpblResponse)
async def bulk_set_env(request: BulkEnvUpdateRequest):
    """Create or update multiple environment variables at once."""
    env = _read_env()
    env.update(request.variables)
    _write_env(env)
    logger.info(f"Bulk set {len(request.variables)} env var(s)")
    return ShpblResponse(
        success=True,
        message=f"Set {len(request.variables)} variable(s)",
        data={"variables": env},
    )
