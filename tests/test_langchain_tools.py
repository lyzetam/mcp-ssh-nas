"""Tests for LangChain tool interfaces."""

from langchain_core.tools import BaseTool

from mcp_ssh_nas.langchain_tools import TOOLS


def test_tools_count():
    assert len(TOOLS) == 13


def test_all_tools_are_base_tool():
    for t in TOOLS:
        assert isinstance(t, BaseTool), f"{t} is not a BaseTool"


def test_tool_names_follow_convention():
    for t in TOOLS:
        assert t.name.startswith("ssh_"), f"Tool {t.name} does not follow ssh_ naming convention"


def test_tool_names_are_unique():
    names = [t.name for t in TOOLS]
    assert len(names) == len(set(names)), f"Duplicate tool names: {names}"


def test_expected_tools_present():
    names = {t.name for t in TOOLS}
    expected = {
        "ssh_execute",
        "ssh_status",
        "ssh_list_files",
        "ssh_read_file",
        "ssh_write_file",
        "ssh_file_exists",
        "ssh_system_info",
        "ssh_disk_usage",
        "ssh_memory_usage",
        "ssh_process_list",
        "ssh_docker_ps",
        "ssh_docker_logs",
        "ssh_service_status",
    }
    assert expected == names


def test_all_tools_have_descriptions():
    for t in TOOLS:
        assert t.description, f"Tool {t.name} has no description"
