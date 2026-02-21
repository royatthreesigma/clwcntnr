from fastapi import FastAPI
import logging
import docker  # type: ignore
import time
from container import exec_in_container
from routers import db_service  # type: ignore
from models import ContainerLogsRequest, RunCommandRequest, ShpblResponse  # type: ignore

# Docker client for logs
docker_client = docker.from_env()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service metadata
SERVICE_VERSION = "0.1.0"
SERVICE_START_TIME = time.time()

# Initialize FastAPI app
app = FastAPI(
    title="Shpbl Manager Service",
    description="Manages file edits and shell execution across backend, app, and db containers",
    version=SERVICE_VERSION,
)

# Include service routers
app.include_router(db_service.router)


@app.get("/")
async def root():
    return {"message": "Shpbl Manager Service", "version": SERVICE_VERSION}


@router.post("/run-command", response_model=ShpblResponse)
async def run_command_in_container(request: RunCommandRequest):
    """
    Execute a raw shell command in the specified container.

    Args:
        request: RunCommandRequest with container_name, command, and optional workdir

    Returns:
        ShpblResponse with success status, stdout, stderr, and exit_code
    """
    try:
        result = exec_in_container(
            container_name=request.container_name, command=request.command
        )
        return result
    except Exception as e:
        return ShpblResponse(
            success=False,
            message=f"Failed to execute command: {str(e)}",
            data={"error": str(e)},
            stderr=str(e),
        )


@router.post("/terminal-logs", response_model=ShpblResponse)
async def get_terminal_logs(request: ContainerLogsRequest):
    """
    Retrieve logs from a specified container, pruned to last 1K characters.

    Args:
        request: ContainerLogsRequest with container_name and num_lines

    Returns:
        ShpblResponse with logs content (pruned to last 1000 characters)
    """
    try:
        # Get container by name
        container = docker_client.containers.get(request.container_name)

        # Get logs (tail by num_lines, decode to string)
        logs = container.logs(tail=request.num_lines).decode("utf-8")

        # Prune to last 1K characters
        if len(logs) > 1000:
            logs = logs[-1000:]
            pruned = True
        else:
            pruned = False

        return ShpblResponse(
            success=True,
            message=f"Container logs retrieved{' (pruned to 1K chars)' if pruned else ''}",
            data={"logs": logs, "pruned": pruned, "character_count": len(logs)},
            internal_do_not_parse__=True,
            unparsed_str_response__=logs,
        )
    except docker.errors.NotFound:
        return ShpblResponse(
            success=False,
            message=f"Container '{request.container_name}' not found",
            data={"error": "Container not found"},
        )
    except Exception as e:
        return ShpblResponse(
            success=False,
            message=f"Failed to retrieve container logs: {str(e)}",
            data={"error": str(e)},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
