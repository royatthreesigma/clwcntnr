from fastapi import FastAPI
import logging
import docker
import time

from container import exec_in_container, exec_python_in_container
from routers import db_service, env_service, file_service, skill_service
from models import (
    ContainerLogsRequest,
    RunCommandRequest,
    RunPythonRequest,
    ShpblResponse,
    SANDBOX_CONTAINER,
)

# Docker client for logs
docker_client = docker.from_env()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service metadata
SERVICE_VERSION = "1.0.0"
SERVICE_START_TIME = time.time()

# Initialize FastAPI app
app = FastAPI(
    title="LLM Sandbox Gateway",
    description=(
        "HTTP gateway for executing commands, managing environment variables, "
        "and querying the database inside a sandboxed container. "
        "Designed as a reliable interface for LLM agents."
    ),
    version=SERVICE_VERSION,
)

# Include routers
app.include_router(db_service.router)
app.include_router(env_service.router)
app.include_router(file_service.router)
app.include_router(skill_service.router)


@app.get("/")
async def root():
    uptime = int(time.time() - SERVICE_START_TIME)
    return {
        "service": "LLM Sandbox Gateway",
        "version": SERVICE_VERSION,
        "uptime_seconds": uptime,
    }


@app.get("/health")
async def health():
    """Quick health check — also verifies the sandbox container is reachable."""
    try:
        container = docker_client.containers.get(SANDBOX_CONTAINER)
        status = container.status
    except docker.errors.NotFound:
        status = "not found"
    except Exception:
        status = "error"

    return {
        "gateway": "ok",
        "sandbox_container": status,
    }


@app.post("/run-command", response_model=ShpblResponse)
async def run_command(request: RunCommandRequest):
    """
    Execute a shell command inside the sandbox container.

    The managed .env variables are automatically available to the command.
    """
    try:
        return exec_in_container(command=request.command, workdir=request.workdir)
    except Exception as e:
        return ShpblResponse(
            success=False,
            message=f"Failed to execute command: {str(e)}",
            stderr=str(e),
        )


@app.post("/run-python", response_model=ShpblResponse)
async def run_python(request: RunPythonRequest):
    """
    Execute a Python code string in the sandbox.

    The code is written to a temp file inside the container and run with
    python3.  This avoids all shell-escaping issues with inline code.
    The managed .env variables are available to the script.
    """
    try:
        return exec_python_in_container(
            code=request.code, workdir=request.workdir
        )
    except Exception as e:
        return ShpblResponse(
            success=False,
            message=f"Failed to execute Python code: {str(e)}",
            stderr=str(e),
        )


@app.post("/terminal-logs", response_model=ShpblResponse)
async def get_terminal_logs(request: ContainerLogsRequest):
    """
    Retrieve recent logs from the sandbox container.
    """
    try:
        container = docker_client.containers.get(request.container_name)
        logs = container.logs(tail=request.num_lines).decode("utf-8")

        # Prune to last 5K characters
        max_chars = 5000
        pruned = len(logs) > max_chars
        if pruned:
            logs = logs[-max_chars:]

        return ShpblResponse(
            success=True,
            message=f"Logs retrieved{' (pruned)' if pruned else ''}",
            data={
                "logs": logs,
                "pruned": pruned,
                "character_count": len(logs),
            },
        )
    except docker.errors.NotFound:
        return ShpblResponse(
            success=False,
            message=f"Container '{request.container_name}' not found",
        )
    except Exception as e:
        return ShpblResponse(
            success=False,
            message=f"Failed to retrieve container logs: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
