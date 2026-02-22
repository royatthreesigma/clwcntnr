import docker
import logging
import uuid
from fastapi import HTTPException
from typing import Optional

from models import ShpblResponse, SANDBOX_CONTAINER

logger = logging.getLogger(__name__)

# Docker client
docker_client = docker.from_env()

# Sandbox configuration
SANDBOX_WORKDIR = "/workspace"
ENV_FILE_PATH = "/sandbox-env/.env"

# Maximum output size (characters)
MAX_OUTPUT_LENGTH = 10_000


def exec_in_container(command: str, workdir: Optional[str] = None) -> ShpblResponse:
    """
    Execute command in the sandbox container.

    Every command automatically sources /sandbox-env/.env so that
    environment variables managed via the API are available to the
    executed process without restarting the container.

    Args:
        command: Shell command to execute
        workdir: Working directory (defaults to /workspace)

    Returns:
        ShpblResponse with success status, exit code, stdout, stderr

    Raises:
        HTTPException: If container not found or execution fails
    """
    try:
        container = docker_client.containers.get(SANDBOX_CONTAINER)
        workdir = workdir or SANDBOX_WORKDIR

        # Source the managed .env file before running the user command.
        # set -a exports every variable.  We must guard with -f because
        # dash (Debian's /bin/sh) treats `. <missing-file>` as a fatal
        # error that kills the shell — even with 2>/dev/null.
        full_command = (
            f"set -a; [ -f {ENV_FILE_PATH} ] && . {ENV_FILE_PATH}; set +a; "
            f"cd {workdir} && {command}"
        )

        logger.info(f"Executing in sandbox ({workdir}): {command}")
        result = container.exec_run(
            cmd=["sh", "-c", full_command], workdir=workdir, demux=True
        )

        stdout = result.output[0].decode() if result.output[0] else ""
        stderr = result.output[1].decode() if result.output[1] else ""

        # Truncate output to prevent huge payloads
        if len(stdout) > MAX_OUTPUT_LENGTH:
            stdout = stdout[:MAX_OUTPUT_LENGTH] + "\n... [output truncated]"
        if len(stderr) > MAX_OUTPUT_LENGTH:
            stderr = stderr[:MAX_OUTPUT_LENGTH] + "\n... [output truncated]"

        return ShpblResponse(
            success=result.exit_code == 0,
            exit_code=result.exit_code,
            stdout=stdout,
            stderr=stderr,
        )
    except docker.errors.NotFound:
        raise HTTPException(
            status_code=404,
            detail=f"Container '{SANDBOX_CONTAINER}' not found. Is the sandbox running?",
        )
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def exec_python_in_container(
    code: str, workdir: Optional[str] = None
) -> ShpblResponse:
    """
    Execute a Python code string in the sandbox container.

    Writes the code to a temp file inside the container (via the Docker API's
    put_archive), runs it with python3, then cleans up.  This avoids all
    shell-quoting / escaping issues with inline code strings.

    The managed .env is sourced before execution, just like exec_in_container.
    """
    try:
        container = docker_client.containers.get(SANDBOX_CONTAINER)
        workdir = workdir or SANDBOX_WORKDIR

        # Unique filename so concurrent calls never collide
        script_name = f"_llm_run_{uuid.uuid4().hex[:12]}.py"
        script_path = f"/tmp/{script_name}"

        # Write the code to the temp file via a safe heredoc-style approach
        # We use `cat` with stdin through docker exec to avoid any shell escaping
        import tarfile
        import io

        # Create an in-memory tar archive containing the script
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            script_bytes = code.encode("utf-8")
            info = tarfile.TarInfo(name=script_name)
            info.size = len(script_bytes)
            tar.addfile(info, io.BytesIO(script_bytes))
        tar_stream.seek(0)

        # Put the script into /tmp in the container
        container.put_archive("/tmp", tar_stream)

        # Run it — source .env first, cd to workdir, then python3
        full_command = (
            f"set -a; . {ENV_FILE_PATH} 2>/dev/null; set +a; "
            f"cd {workdir} && python3 {script_path}; "
            f"_exit=$?; rm -f {script_path}; exit $_exit"
        )

        logger.info(f"Executing Python script in sandbox ({workdir}): {len(code)} chars")
        result = container.exec_run(
            cmd=["sh", "-c", full_command], workdir=workdir, demux=True
        )

        stdout = result.output[0].decode() if result.output[0] else ""
        stderr = result.output[1].decode() if result.output[1] else ""

        if len(stdout) > MAX_OUTPUT_LENGTH:
            stdout = stdout[:MAX_OUTPUT_LENGTH] + "\n... [output truncated]"
        if len(stderr) > MAX_OUTPUT_LENGTH:
            stderr = stderr[:MAX_OUTPUT_LENGTH] + "\n... [output truncated]"

        return ShpblResponse(
            success=result.exit_code == 0,
            exit_code=result.exit_code,
            stdout=stdout,
            stderr=stderr,
        )
    except docker.errors.NotFound:
        raise HTTPException(
            status_code=404,
            detail=f"Container '{SANDBOX_CONTAINER}' not found. Is the sandbox running?",
        )
    except Exception as e:
        logger.error(f"Error executing Python code: {e}")
        raise HTTPException(status_code=500, detail=str(e))
