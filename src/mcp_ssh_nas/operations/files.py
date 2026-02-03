"""File operations on the NAS."""

from __future__ import annotations

import json
from typing import Optional

from ..client import SSHClient, format_result


def list_files(
    client: SSHClient,
    path: str = "~",
    all: bool = False,
    long: bool = True,
) -> str:
    """List files and directories at a given path.

    Returns:
        Directory listing output.
    """
    flags = "-lh" if long else ""
    if all:
        flags += "a"

    cmd = f"ls {flags} {path}" if flags else f"ls {path}"
    result = client.execute(cmd)
    return format_result(result)


def read_file(
    client: SSHClient,
    path: str,
    lines: Optional[int] = None,
) -> str:
    """Read the contents of a file.

    Args:
        lines: Number of lines to read. Positive for head, negative for tail.

    Returns:
        File contents.
    """
    if lines:
        if lines > 0:
            cmd = f"head -n {lines} {path}"
        else:
            cmd = f"tail -n {abs(lines)} {path}"
    else:
        cmd = f"cat {path}"

    result = client.execute(cmd)
    return format_result(result)


def write_file(
    client: SSHClient,
    path: str,
    content: str,
    append: bool = False,
) -> str:
    """Write content to a file (creates or overwrites).

    Returns:
        Success or error message.
    """
    escaped = content.replace("'", "'\\''")
    operator = ">>" if append else ">"
    cmd = f"echo '{escaped}' {operator} {path}"

    result = client.execute(cmd)
    if result.get("success"):
        return f"Successfully wrote to {path}"
    return format_result(result)


def file_exists(client: SSHClient, path: str) -> dict:
    """Check if a file or directory exists.

    Returns:
        dict with exists (bool) and optional info.
    """
    result = client.execute(f"test -e {path} && echo 'exists' || echo 'not found'")
    output = result.get("stdout", "").strip()
    exists = output == "exists"

    if exists:
        type_result = client.execute(f"file {path}")
        file_info = type_result.get("stdout", "").strip()
        return {"exists": True, "info": file_info}
    return {"exists": False}
