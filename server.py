#!/usr/bin/env python3
"""
SSH NAS MCP Server - Execute commands and manage files on a NAS via SSH.
Provides tools for system administration, file management, and monitoring.
"""
import json
import os
from typing import Optional

import paramiko
from fastmcp import FastMCP

# Configuration from environment variables (strip to handle trailing newlines from Docker secrets)
NAS_HOST = os.environ.get("NAS_HOST", "").strip()
NAS_PORT = int(os.environ.get("NAS_PORT", "22").strip())
NAS_USER = os.environ.get("NAS_USER", "").strip()
NAS_PASSWORD = os.environ.get("NAS_PASSWORD", "").strip()

mcp = FastMCP("ssh-nas")

# Connection pool for reuse
_ssh_client = None


def get_ssh_client() -> paramiko.SSHClient:
    """Get or create an SSH client connection."""
    global _ssh_client

    if _ssh_client is not None:
        try:
            # Test if connection is still alive
            _ssh_client.exec_command("echo", timeout=5)
            return _ssh_client
        except Exception:
            try:
                _ssh_client.close()
            except Exception:
                pass
            _ssh_client = None

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=NAS_HOST,
        port=NAS_PORT,
        username=NAS_USER,
        password=NAS_PASSWORD,
        timeout=30,
    )
    _ssh_client = client
    return client


def execute_ssh_command(command: str, timeout: int = 30) -> dict:
    """Execute a command on the NAS via SSH."""
    if not all([NAS_HOST, NAS_USER, NAS_PASSWORD]):
        return {
            "success": False,
            "error": "NAS credentials not configured. Set NAS_HOST, NAS_USER, and NAS_PASSWORD.",
        }

    try:
        client = get_ssh_client()
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)

        exit_status = stdout.channel.recv_exit_status()
        stdout_text = stdout.read().decode("utf-8", errors="replace")
        stderr_text = stderr.read().decode("utf-8", errors="replace")

        return {
            "success": exit_status == 0,
            "exit_code": exit_status,
            "stdout": stdout_text,
            "stderr": stderr_text,
        }

    except paramiko.AuthenticationException:
        return {"success": False, "error": "Authentication failed. Check username and password."}
    except paramiko.SSHException as e:
        return {"success": False, "error": f"SSH error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}


def format_result(result: dict) -> str:
    """Format command result for output."""
    if result.get("success"):
        output = ""
        if result.get("stdout"):
            output += result["stdout"]
        if result.get("stderr"):
            if output:
                output += "\n"
            output += f"STDERR: {result['stderr']}"
        return output.strip() or "Command completed successfully (no output)"
    else:
        error = result.get("error", "Unknown error")
        stderr = result.get("stderr", "")
        return f"Error: {error}" + (f"\n{stderr}" if stderr else "")


# =============================================================================
# Core Execution Tools
# =============================================================================

@mcp.tool
def ssh_execute(command: str, timeout: int = 30) -> str:
    """Execute a command on the NAS via SSH. Use this to run shell commands, check system status, manage files, etc.

    Args:
        command: The shell command to execute on the NAS
        timeout: Command timeout in seconds (default: 30)

    Returns:
        Command output or error message
    """
    if not command:
        return "Error: No command provided"

    result = execute_ssh_command(command, timeout)
    return format_result(result)


@mcp.tool
def ssh_status() -> str:
    """Check the SSH connection status to the NAS.

    Returns:
        JSON with connection status, host info, and system details
    """
    if not all([NAS_HOST, NAS_USER, NAS_PASSWORD]):
        return "NAS not configured. Set NAS_HOST, NAS_USER, NAS_PASSWORD"

    result = execute_ssh_command("hostname && uname -a", 10)

    if result.get("success"):
        return json.dumps({
            "status": "connected",
            "host": f"{NAS_HOST}:{NAS_PORT}",
            "user": NAS_USER,
            "system": result.get("stdout", "").strip()
        }, indent=2)
    else:
        return json.dumps({
            "status": "error",
            "host": f"{NAS_HOST}:{NAS_PORT}",
            "error": result.get("error", "Unknown error")
        }, indent=2)


# =============================================================================
# File Operations
# =============================================================================

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
    flags = "-lh" if long else ""
    if all:
        flags += "a"

    cmd = f"ls {flags} {path}" if flags else f"ls {path}"
    result = execute_ssh_command(cmd)
    return format_result(result)


@mcp.tool
def ssh_read_file(path: str, lines: Optional[int] = None) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read
        lines: Number of lines to read (default: all). Use negative for tail.

    Returns:
        File contents
    """
    if lines:
        if lines > 0:
            cmd = f"head -n {lines} {path}"
        else:
            cmd = f"tail -n {abs(lines)} {path}"
    else:
        cmd = f"cat {path}"

    result = execute_ssh_command(cmd)
    return format_result(result)


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
    # Escape content for shell
    escaped = content.replace("'", "'\\''")
    operator = ">>" if append else ">"
    cmd = f"echo '{escaped}' {operator} {path}"

    result = execute_ssh_command(cmd)
    if result.get("success"):
        return f"Successfully wrote to {path}"
    return format_result(result)


@mcp.tool
def ssh_file_exists(path: str) -> str:
    """Check if a file or directory exists.

    Args:
        path: Path to check

    Returns:
        JSON with existence status and file info
    """
    result = execute_ssh_command(f"test -e {path} && echo 'exists' || echo 'not found'")
    output = result.get("stdout", "").strip()
    exists = output == "exists"

    if exists:
        # Get file type
        type_result = execute_ssh_command(f"file {path}")
        file_info = type_result.get("stdout", "").strip()
        return json.dumps({"exists": True, "info": file_info}, indent=2)
    return json.dumps({"exists": False}, indent=2)


# =============================================================================
# System Information
# =============================================================================

@mcp.tool
def ssh_system_info() -> str:
    """Get system information (hostname, OS, uptime, load).

    Returns:
        System information output
    """
    cmd = """echo '=== Hostname ===' && hostname && \
             echo '=== OS ===' && cat /etc/os-release 2>/dev/null | head -5 || uname -a && \
             echo '=== Uptime ===' && uptime && \
             echo '=== Load ===' && cat /proc/loadavg 2>/dev/null || uptime"""
    result = execute_ssh_command(cmd)
    return format_result(result)


@mcp.tool
def ssh_disk_usage(path: Optional[str] = None) -> str:
    """Get disk usage information.

    Args:
        path: Specific path to check (default: all filesystems)

    Returns:
        Disk usage output
    """
    cmd = f"df -h {path}" if path else "df -h"
    result = execute_ssh_command(cmd)
    return format_result(result)


@mcp.tool
def ssh_memory_usage() -> str:
    """Get memory usage information.

    Returns:
        Memory usage output
    """
    cmd = "free -h 2>/dev/null || vm_stat"
    result = execute_ssh_command(cmd)
    return format_result(result)


@mcp.tool
def ssh_process_list(filter: Optional[str] = None, top: int = 20) -> str:
    """List running processes.

    Args:
        filter: Filter processes by name (grep pattern)
        top: Limit to top N processes by CPU/memory

    Returns:
        Process list output
    """
    if filter:
        cmd = f"ps aux | grep -i '{filter}' | grep -v grep | head -n {top}"
    else:
        cmd = f"ps aux --sort=-%cpu | head -n {top + 1}"

    result = execute_ssh_command(cmd)
    return format_result(result)


# =============================================================================
# Docker Operations
# =============================================================================

@mcp.tool
def ssh_docker_ps(all: bool = False) -> str:
    """List Docker containers on the NAS.

    Args:
        all: Show all containers (including stopped)

    Returns:
        Docker container list
    """
    cmd = "docker ps -a" if all else "docker ps"
    result = execute_ssh_command(cmd)
    return format_result(result)


@mcp.tool
def ssh_docker_logs(container: str, lines: int = 100) -> str:
    """Get logs from a Docker container.

    Args:
        container: Container name or ID
        lines: Number of lines to show (default: 100)

    Returns:
        Container logs
    """
    cmd = f"docker logs --tail {lines} {container}"
    result = execute_ssh_command(cmd, timeout=60)
    return format_result(result)


# =============================================================================
# Service Management
# =============================================================================

@mcp.tool
def ssh_service_status(service: str) -> str:
    """Check status of a service (systemctl/service).

    Args:
        service: Service name to check

    Returns:
        Service status output
    """
    cmd = f"systemctl status {service} 2>/dev/null || service {service} status"
    result = execute_ssh_command(cmd)
    return format_result(result)


if __name__ == "__main__":
    mcp.run()
