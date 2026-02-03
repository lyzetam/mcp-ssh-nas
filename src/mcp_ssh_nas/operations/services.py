"""Service management operations."""

from __future__ import annotations

from ..client import SSHClient, format_result


def service_status(client: SSHClient, service: str) -> str:
    """Check status of a service (systemctl/service).

    Args:
        service: Service name to check.

    Returns:
        Service status output.
    """
    cmd = f"systemctl status {service} 2>/dev/null || service {service} status"
    result = client.execute(cmd)
    return format_result(result)
