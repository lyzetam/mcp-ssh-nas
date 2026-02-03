"""SSH client with paramiko for NAS operations."""

from __future__ import annotations

import os

import paramiko

from mcp_ssh_nas.config import get_settings


class SSHClient:
    """Manages a paramiko SSH connection to the NAS.

    Reads configuration from environment variables (NAS_* prefix),
    .env file, or explicit constructor parameters.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        settings = get_settings()
        self.host = (host or settings.host).strip()
        self.port = port or settings.port
        self.user = (user or settings.user).strip()
        self.password = (password or settings.password).strip()
        self._client: paramiko.SSHClient | None = None

    @property
    def configured(self) -> bool:
        """Check if NAS credentials are set."""
        return bool(self.host and self.user and self.password)

    def _connect(self) -> paramiko.SSHClient:
        """Create a new SSH connection."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            timeout=30,
        )
        return client

    def _get_client(self) -> paramiko.SSHClient:
        """Get or create an SSH client connection with reconnect on failure."""
        if self._client is not None:
            try:
                self._client.exec_command("echo", timeout=5)
                return self._client
            except Exception:
                try:
                    self._client.close()
                except Exception:
                    pass
                self._client = None

        self._client = self._connect()
        return self._client

    def execute(self, command: str, timeout: int = 30) -> dict:
        """Execute a command on the NAS via SSH.

        Returns:
            dict with keys: success, exit_code, stdout, stderr (or error).
        """
        if not self.configured:
            return {
                "success": False,
                "error": "NAS credentials not configured. Set NAS_HOST, NAS_USER, and NAS_PASSWORD.",
            }

        try:
            client = self._get_client()
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

    def close(self) -> None:
        """Close the SSH connection."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None


def format_result(result: dict) -> str:
    """Format command result for human-readable output."""
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
