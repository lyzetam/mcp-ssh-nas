"""LangChain @tool wrappers for SSH NAS operations.

Usage:
    from mcp_ssh_nas.langchain_tools import TOOLS

    # Or import individual tools:
    from mcp_ssh_nas.langchain_tools import ssh_execute, ssh_status
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from .client import SSHClient
from .operations import docker, exec, files, services, system


@lru_cache
def _get_client() -> SSHClient:
    """Singleton SSHClient configured from environment."""
    return SSHClient()


# =============================================================================
# Core Execution
# =============================================================================


class ExecuteInput(BaseModel):
    command: str = Field(description="The shell command to execute on the NAS")
    timeout: int = Field(default=30, description="Command timeout in seconds")


@tool(args_schema=ExecuteInput)
def ssh_execute(command: str, timeout: int = 30) -> str:
    """Execute a command on the NAS via SSH. Use this to run shell commands, check system status, manage files, etc."""
    return exec.execute(_get_client(), command, timeout)


@tool
def ssh_status() -> str:
    """Check the SSH connection status to the NAS."""
    return json.dumps(exec.check_status(_get_client()), indent=2)


# =============================================================================
# File Operations
# =============================================================================


class ListFilesInput(BaseModel):
    path: str = Field(default="~", description="Directory path to list")
    all: bool = Field(default=False, description="Include hidden files")
    long: bool = Field(default=True, description="Use long listing format with details")


@tool(args_schema=ListFilesInput)
def ssh_list_files(path: str = "~", all: bool = False, long: bool = True) -> str:
    """List files and directories at a given path on the NAS."""
    return files.list_files(_get_client(), path, all=all, long=long)


class ReadFileInput(BaseModel):
    path: str = Field(description="Path to the file to read")
    lines: Optional[int] = Field(
        default=None,
        description="Number of lines to read (default: all). Use negative for tail.",
    )


@tool(args_schema=ReadFileInput)
def ssh_read_file(path: str, lines: Optional[int] = None) -> str:
    """Read the contents of a file on the NAS."""
    return files.read_file(_get_client(), path, lines=lines)


class WriteFileInput(BaseModel):
    path: str = Field(description="Path to the file to write")
    content: str = Field(description="Content to write to the file")
    append: bool = Field(default=False, description="Append to file instead of overwriting")


@tool(args_schema=WriteFileInput)
def ssh_write_file(path: str, content: str, append: bool = False) -> str:
    """Write content to a file on the NAS (creates or overwrites)."""
    return files.write_file(_get_client(), path, content, append=append)


class FileExistsInput(BaseModel):
    path: str = Field(description="Path to check")


@tool(args_schema=FileExistsInput)
def ssh_file_exists(path: str) -> str:
    """Check if a file or directory exists on the NAS."""
    return json.dumps(files.file_exists(_get_client(), path), indent=2)


# =============================================================================
# System Information
# =============================================================================


@tool
def ssh_system_info() -> str:
    """Get NAS system information (hostname, OS, uptime, load)."""
    return system.system_info(_get_client())


class DiskUsageInput(BaseModel):
    path: Optional[str] = Field(
        default=None,
        description="Specific path to check (default: all filesystems)",
    )


@tool(args_schema=DiskUsageInput)
def ssh_disk_usage(path: Optional[str] = None) -> str:
    """Get disk usage information from the NAS."""
    return system.disk_usage(_get_client(), path=path)


@tool
def ssh_memory_usage() -> str:
    """Get memory usage information from the NAS."""
    return system.memory_usage(_get_client())


class ProcessListInput(BaseModel):
    filter: Optional[str] = Field(
        default=None, description="Filter processes by name (grep pattern)"
    )
    top: int = Field(default=20, description="Limit to top N processes by CPU/memory")


@tool(args_schema=ProcessListInput)
def ssh_process_list(filter: Optional[str] = None, top: int = 20) -> str:
    """List running processes on the NAS."""
    return system.process_list(_get_client(), filter=filter, top=top)


# =============================================================================
# Docker Operations
# =============================================================================


class DockerPsInput(BaseModel):
    all: bool = Field(default=False, description="Show all containers (including stopped)")


@tool(args_schema=DockerPsInput)
def ssh_docker_ps(all: bool = False) -> str:
    """List Docker containers on the NAS."""
    return docker.docker_ps(_get_client(), all=all)


class DockerLogsInput(BaseModel):
    container: str = Field(description="Container name or ID")
    lines: int = Field(default=100, description="Number of lines to show")


@tool(args_schema=DockerLogsInput)
def ssh_docker_logs(container: str, lines: int = 100) -> str:
    """Get logs from a Docker container on the NAS."""
    return docker.docker_logs(_get_client(), container, lines=lines)


# =============================================================================
# Service Management
# =============================================================================


class ServiceStatusInput(BaseModel):
    service: str = Field(description="Service name to check")


@tool(args_schema=ServiceStatusInput)
def ssh_service_status(service: str) -> str:
    """Check status of a service on the NAS (systemctl/service)."""
    return services.service_status(_get_client(), service)


# =============================================================================
# Tool exports
# =============================================================================

TOOLS = [
    # Core
    ssh_execute,
    ssh_status,
    # Files
    ssh_list_files,
    ssh_read_file,
    ssh_write_file,
    ssh_file_exists,
    # System
    ssh_system_info,
    ssh_disk_usage,
    ssh_memory_usage,
    ssh_process_list,
    # Docker
    ssh_docker_ps,
    ssh_docker_logs,
    # Services
    ssh_service_status,
]
