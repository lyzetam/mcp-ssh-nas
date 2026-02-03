"""Docker operations on the NAS."""

from __future__ import annotations

from ..client import SSHClient, format_result


def docker_ps(client: SSHClient, all: bool = False) -> str:
    """List Docker containers on the NAS.

    Args:
        all: Show all containers (including stopped).

    Returns:
        Docker container list.
    """
    cmd = "docker ps -a" if all else "docker ps"
    result = client.execute(cmd)
    return format_result(result)


def docker_logs(client: SSHClient, container: str, lines: int = 100) -> str:
    """Get logs from a Docker container.

    Args:
        container: Container name or ID.
        lines: Number of lines to show (default: 100).

    Returns:
        Container logs.
    """
    cmd = f"docker logs --tail {lines} {container}"
    result = client.execute(cmd, timeout=60)
    return format_result(result)
