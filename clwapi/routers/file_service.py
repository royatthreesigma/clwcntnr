"""File browsing endpoints for the sandbox container's /workspace directory"""

import io
import os
import tarfile
import logging
from pathlib import PurePosixPath

import docker
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from models import ShpblResponse, SANDBOX_CONTAINER
from container import exec_in_container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

docker_client = docker.from_env()

# Root directory that users are allowed to browse
ALLOWED_ROOT = "/workspace"


def _validate_path(path: str) -> str:
    """Ensure the requested path is within /workspace (no traversal)."""
    resolved = str(PurePosixPath(path))
    if not resolved.startswith(ALLOWED_ROOT):
        raise HTTPException(
            status_code=400,
            detail=f"Path must be within {ALLOWED_ROOT}",
        )
    return resolved


def _parse_tree(raw_output: str, root: str) -> list[dict]:
    """
    Parse the output of ``find -printf '%y %p\\n'`` into a nested tree.

    Each entry is ``<type_char> <path>`` where type_char is ``f`` (file) or
    ``d`` (directory).
    """
    nodes: dict[str, dict] = {}
    lines = [l for l in raw_output.strip().splitlines() if l.strip()]

    for line in lines:
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        type_char, abs_path = parts
        entry_type = "directory" if type_char == "d" else "file"
        name = os.path.basename(abs_path) or abs_path
        nodes[abs_path] = {
            "name": name,
            "path": abs_path,
            "type": entry_type,
            "children": [] if entry_type == "directory" else None,
        }

    # Build hierarchy
    for abs_path, node in nodes.items():
        parent_path = str(PurePosixPath(abs_path).parent)
        if parent_path in nodes and parent_path != abs_path:
            nodes[parent_path]["children"].append(node)

    # Return children of the requested root (or the root node itself)
    if root in nodes:
        return nodes[root].get("children") or []
    return list(nodes.values())


@router.get("/tree", response_model=ShpblResponse)
async def get_file_tree(
    path: str = Query(ALLOWED_ROOT, description="Directory path to list"),
    depth: int = Query(5, ge=1, le=10, description="Max depth to recurse"),
):
    """
    Return a nested file-tree for the given directory inside the sandbox.

    The tree is restricted to ``/workspace``.
    """
    safe_path = _validate_path(path)

    result = exec_in_container(
        command=f'find "{safe_path}" -maxdepth {depth} -not -path "*/\\.*" -printf "%y %p\n" 2>/dev/null; true',
    )

    tree = _parse_tree(result.stdout or "", safe_path)

    return ShpblResponse(
        success=True,
        message=f"File tree for {safe_path}",
        data={"path": safe_path, "tree": tree},
    )


@router.get("/download")
async def download_file(
    path: str = Query(..., description="Absolute path of the file to download"),
):
    """
    Download a single file from the sandbox container.

    Uses Docker ``get_archive`` to pull the file as a tar stream, then
    extracts and returns the raw bytes with an appropriate Content-Disposition.
    """
    safe_path = _validate_path(path)

    try:
        container = docker_client.containers.get(SANDBOX_CONTAINER)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Sandbox container not found")

    try:
        bits, stat = container.get_archive(safe_path)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"File not found: {safe_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # get_archive returns a tar stream — extract the single file
    tar_bytes = b"".join(bits)
    tar_stream = io.BytesIO(tar_bytes)

    try:
        with tarfile.open(fileobj=tar_stream) as tar:
            members = tar.getmembers()
            if not members:
                raise HTTPException(status_code=404, detail="Archive is empty")
            member = members[0]
            if member.isdir():
                raise HTTPException(
                    status_code=400,
                    detail="Path is a directory. Use /files/tree to browse.",
                )
            extracted = tar.extractfile(member)
            if extracted is None:
                raise HTTPException(
                    status_code=500, detail="Could not extract file from archive"
                )
            file_bytes = extracted.read()
    except tarfile.TarError as e:
        raise HTTPException(status_code=500, detail=f"Tar extraction error: {e}")

    filename = os.path.basename(safe_path)

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
