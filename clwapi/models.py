from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any

# The only managed container
ContainerName = Literal["sandbox"]

# Default sandbox container name
SANDBOX_CONTAINER = "sandbox"


class ContainerLogsRequest(BaseModel):
    container_name: ContainerName = Field(
        default="sandbox",
        description="Name of the container to get logs from",
    )
    num_lines: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Number of log lines to retrieve (default: 50, max: 500)",
    )


class ShpblResponse(BaseModel):
    """Unified response model for all sandbox operations"""

    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None


class RunCommandRequest(BaseModel):
    """Request model for running commands in the sandbox container"""

    command: str = Field(..., description="Shell command to execute in sandbox")
    workdir: Optional[str] = Field(
        None, description="Working directory (defaults to /workspace)"
    )


class UpdateEnvVariableRequest(BaseModel):
    """Request model for updating or creating an environment variable"""

    variable_name: str = Field(..., description="Name of the environment variable")
    value: str = Field(..., description="Value of the environment variable")


class BulkEnvUpdateRequest(BaseModel):
    """Request model for setting multiple environment variables at once"""

    variables: Dict[str, str] = Field(
        ..., description="Key-value pairs of environment variables to set"
    )


class RunPythonRequest(BaseModel):
    """Request model for executing a Python code string in the sandbox"""

    code: str = Field(..., description="Python source code to execute")
    workdir: Optional[str] = Field(
        None, description="Working directory (defaults to /workspace)"
    )


class ExecuteSQLRequest(BaseModel):
    """Request model for executing a SQL statement against the workspace PostgreSQL database"""

    sql: str = Field(..., description="SQL statement to execute")
    params: Optional[list[Any]] = Field(
        None,
        description="Optional positional parameters for parameterised queries (use %s placeholders)",
    )
