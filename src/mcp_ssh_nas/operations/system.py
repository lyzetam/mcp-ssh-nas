"""System information operations."""

from __future__ import annotations

from typing import Optional

from ..client import SSHClient, format_result


def system_info(client: SSHClient) -> str:
    """Get system information (hostname, OS, uptime, load).

    Returns:
        System information output.
    """
    cmd = (
        "echo '=== Hostname ===' && hostname && "
        "echo '=== OS ===' && cat /etc/os-release 2>/dev/null | head -5 || uname -a && "
        "echo '=== Uptime ===' && uptime && "
        "echo '=== Load ===' && cat /proc/loadavg 2>/dev/null || uptime"
    )
    result = client.execute(cmd)
    return format_result(result)


def disk_usage(client: SSHClient, path: Optional[str] = None) -> str:
    """Get disk usage information.

    Args:
        path: Specific path to check (default: all filesystems).

    Returns:
        Disk usage output.
    """
    cmd = f"df -h {path}" if path else "df -h"
    result = client.execute(cmd)
    return format_result(result)


def memory_usage(client: SSHClient) -> str:
    """Get memory usage information.

    Returns:
        Memory usage output.
    """
    cmd = "free -h 2>/dev/null || vm_stat"
    result = client.execute(cmd)
    return format_result(result)


def process_list(
    client: SSHClient,
    filter: Optional[str] = None,
    top: int = 20,
) -> str:
    """List running processes.

    Args:
        filter: Filter processes by name (grep pattern).
        top: Limit to top N processes by CPU/memory.

    Returns:
        Process list output.
    """
    if filter:
        cmd = f"ps aux | grep -i '{filter}' | grep -v grep | head -n {top}"
    else:
        cmd = f"ps aux --sort=-%cpu | head -n {top + 1}"

    result = client.execute(cmd)
    return format_result(result)
