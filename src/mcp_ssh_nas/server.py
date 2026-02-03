"""SSH NAS MCP Server -- backward-compatible @mcp.tool wrappers.

Tool names match the original server.py for drop-in replacement.
"""

from __future__ import annotations

import json
from typing import Optional

from fastmcp import FastMCP

from .client import SSHClient
from .operations import docker, exec, files, services, system

mcp = FastMCP("ssh-nas")

_client: SSHClient | None = None


def _get_client() -> SSHClient:
    global _client
    if _client is None:
        _client = SSHClient()
    return _client


# --- Core Execution ---


@mcp.tool
def ssh_execute(command: str, timeout: int = 30) -> str:
    """Execute a command on the NAS via SSH. Use this to run shell commands, check system status, manage files, etc.

    Args:
        command: The shell command to execute on the NAS
        timeout: Command timeout in seconds (default: 30)

    Returns:
        Command output or error message
    """
    return exec.execute(_get_client(), command, timeout)


@mcp.tool
def ssh_status() -> str:
    """Check the SSH connection status to the NAS.

    Returns:
        JSON with connection status, host info, and system details
    """
    return json.dumps(exec.check_status(_get_client()), indent=2)


# --- File Operations ---


@mcp.tool
def ssh_list_files(path: str = "~", all: bool = False, long: bool = True) -> str:
    """List files and directories at a given path.

    Args:
        path: Directory path to list (default: home directory)
        all: Include hidden files
        long: Use long listing format with details

    Returns:
        Directory listing output
    """
    return files.list_files(_get_client(), path, all=all, long=long)


@mcp.tool
def ssh_read_file(path: str, lines: Optional[int] = None) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read
        lines: Number of lines to read (default: all). Use negative for tail.

    Returns:
        File contents
    """
    return files.read_file(_get_client(), path, lines=lines)


@mcp.tool
def ssh_write_file(path: str, content: str, append: bool = False) -> str:
    """Write content to a file (creates or overwrites).

    Args:
        path: Path to the file to write
        content: Content to write to the file
        append: Append to file instead of overwriting

    Returns:
        Success or error message
    """
    return files.write_file(_get_client(), path, content, append=append)


@mcp.tool
def ssh_file_exists(path: str) -> str:
    """Check if a file or directory exists.

    Args:
        path: Path to check

    Returns:
        JSON with existence status and file info
    """
    return json.dumps(files.file_exists(_get_client(), path), indent=2)


# --- System Information ---


@mcp.tool
def ssh_system_info() -> str:
    """Get system information (hostname, OS, uptime, load).

    Returns:
        System information output
    """
    return system.system_info(_get_client())


@mcp.tool
def ssh_disk_usage(path: Optional[str] = None) -> str:
    """Get disk usage information.

    Args:
        path: Specific path to check (default: all filesystems)

    Returns:
        Disk usage output
    """
    return system.disk_usage(_get_client(), path=path)


@mcp.tool
def ssh_memory_usage() -> str:
    """Get memory usage information.

    Returns:
        Memory usage output
    """
    return system.memory_usage(_get_client())


@mcp.tool
def ssh_process_list(filter: Optional[str] = None, top: int = 20) -> str:
    """List running processes.

    Args:
        filter: Filter processes by name (grep pattern)
        top: Limit to top N processes by CPU/memory

    Returns:
        Process list output
    """
    return system.process_list(_get_client(), filter=filter, top=top)


# --- Docker Operations ---


@mcp.tool
def ssh_docker_ps(all: bool = False) -> str:
    """List Docker containers on the NAS.

    Args:
        all: Show all containers (including stopped)

    Returns:
        Docker container list
    """
    return docker.docker_ps(_get_client(), all=all)


@mcp.tool
def ssh_docker_logs(container: str, lines: int = 100) -> str:
    """Get logs from a Docker container.

    Args:
        container: Container name or ID
        lines: Number of lines to show (default: 100)

    Returns:
        Container logs
    """
    return docker.docker_logs(_get_client(), container, lines=lines)


# --- Service Management ---


@mcp.tool
def ssh_service_status(service: str) -> str:
    """Check status of a service (systemctl/service).

    Args:
        service: Service name to check

    Returns:
        Service status output
    """
    return services.service_status(_get_client(), service)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
