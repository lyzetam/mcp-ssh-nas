"""Tests for SSH NAS operations using mock paramiko."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_ssh_nas.client import SSHClient, format_result
from mcp_ssh_nas.operations import docker, exec, files, services, system


def _make_exec_result(stdout_text: str, stderr_text: str = "", exit_code: int = 0):
    """Helper to build a mock exec_command return value."""
    stdin = MagicMock()
    stdout = MagicMock()
    stderr = MagicMock()
    stdout.read.return_value = stdout_text.encode()
    stderr.read.return_value = stderr_text.encode()
    stdout.channel.recv_exit_status.return_value = exit_code
    return stdin, stdout, stderr


@pytest.fixture
def client():
    """Create an SSHClient with test credentials and a mocked paramiko connection."""
    c = SSHClient(host="10.0.0.1", port=22, user="testuser", password="testpass")
    mock_ssh = MagicMock()
    c._client = mock_ssh
    return c


# =============================================================================
# Client tests
# =============================================================================


def test_client_configured():
    c = SSHClient(host="h", user="u", password="p")
    assert c.configured is True


def test_client_not_configured():
    c = SSHClient()
    assert c.configured is False


def test_client_execute_not_configured():
    c = SSHClient()
    result = c.execute("ls")
    assert result["success"] is False
    assert "not configured" in result["error"]


def test_format_result_success():
    result = {"success": True, "stdout": "hello\n", "stderr": ""}
    assert format_result(result) == "hello"


def test_format_result_error():
    result = {"success": False, "error": "Connection refused"}
    assert "Connection refused" in format_result(result)


# =============================================================================
# Exec operations
# =============================================================================


def test_execute(client):
    client._client.exec_command.return_value = _make_exec_result("output line\n")
    result = exec.execute(client, "echo hello")
    assert "output line" in result


def test_execute_empty_command(client):
    result = exec.execute(client, "")
    assert "Error" in result


def test_check_status(client):
    client._client.exec_command.return_value = _make_exec_result("mynas\nLinux mynas 5.15\n")
    result = exec.check_status(client)
    assert result["status"] == "connected"
    assert "10.0.0.1" in result["host"]


def test_check_status_not_configured():
    c = SSHClient()
    result = exec.check_status(c)
    assert result["status"] == "error"


# =============================================================================
# File operations
# =============================================================================


def test_list_files(client):
    client._client.exec_command.return_value = _make_exec_result("file1\nfile2\n")
    result = files.list_files(client, "/tmp")
    assert "file1" in result


def test_read_file(client):
    client._client.exec_command.return_value = _make_exec_result("line1\nline2\n")
    result = files.read_file(client, "/etc/hostname")
    assert "line1" in result


def test_file_exists_true(client):
    # Health check + test -e + file command = 3 calls through exec_command
    # The health check (echo) fires each time execute() calls _get_client()
    client._client.exec_command.side_effect = [
        _make_exec_result(""),           # health check for test -e
        _make_exec_result("exists\n"),   # test -e returns "exists"
        _make_exec_result(""),           # health check for file command
        _make_exec_result("/tmp/test: ASCII text\n"),  # file type info
    ]
    result = files.file_exists(client, "/tmp/test")
    assert result["exists"] is True
    assert "ASCII" in result["info"]


def test_file_exists_false(client):
    client._client.exec_command.return_value = _make_exec_result("not found\n")
    result = files.file_exists(client, "/nonexistent")
    assert result["exists"] is False


# =============================================================================
# Docker operations
# =============================================================================


def test_docker_ps(client):
    client._client.exec_command.return_value = _make_exec_result(
        "CONTAINER ID   IMAGE   STATUS\nabc123   nginx   Up 2 hours\n"
    )
    result = docker.docker_ps(client)
    assert "nginx" in result


# =============================================================================
# Service operations
# =============================================================================


def test_service_status(client):
    client._client.exec_command.return_value = _make_exec_result(
        "docker.service - Docker\n   Active: active (running)\n"
    )
    result = services.service_status(client, "docker")
    assert "active" in result
