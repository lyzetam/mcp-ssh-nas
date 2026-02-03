"""Core execution operations."""

from __future__ import annotations

import json

from ..client import SSHClient, format_result


def execute(client: SSHClient, command: str, timeout: int = 30) -> str:
    """Execute a command on the NAS via SSH.

    Returns:
        Formatted command output or error message.
    """
    if not command:
        return "Error: No command provided"

    result = client.execute(command, timeout)
    return format_result(result)


def check_status(client: SSHClient) -> dict:
    """Check the SSH connection status to the NAS.

    Returns:
        dict with connection status, host info, and system details.
    """
    if not client.configured:
        return {
            "status": "error",
            "error": "NAS not configured. Set NAS_HOST, NAS_USER, NAS_PASSWORD",
        }

    result = client.execute("hostname && uname -a", 10)

    if result.get("success"):
        return {
            "status": "connected",
            "host": f"{client.host}:{client.port}",
            "user": client.user,
            "system": result.get("stdout", "").strip(),
        }
    else:
        return {
            "status": "error",
            "host": f"{client.host}:{client.port}",
            "error": result.get("error", "Unknown error"),
        }
