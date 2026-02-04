# mcp-ssh-nas

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP server and LangChain tools for SSH-based NAS management -- execute commands, manage files, monitor Docker containers, and check system health.

## Features

13 tools across 5 categories:

| Category | Tools | Description |
|----------|-------|-------------|
| Core | `ssh_execute`, `ssh_status` | Execute arbitrary commands, check connection status |
| Files | `ssh_list_files`, `ssh_read_file`, `ssh_write_file`, `ssh_file_exists` | Full file operations over SSH |
| System | `ssh_system_info`, `ssh_disk_usage`, `ssh_memory_usage`, `ssh_process_list` | Hostname, OS, uptime, disk, memory, processes |
| Docker | `ssh_docker_ps`, `ssh_docker_logs` | List containers, view container logs |
| Services | `ssh_service_status` | Check systemd/service status |

## Installation

```bash
# Core library
pip install .

# With MCP server support
pip install ".[mcp]"

# With LangChain tools
pip install ".[langchain]"

# Everything
pip install ".[all]"
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NAS_HOST` | Yes | _(empty)_ | NAS hostname or IP address |
| `NAS_PORT` | No | `22` | SSH port |
| `NAS_USER` | Yes | _(empty)_ | SSH username |
| `NAS_PASSWORD` | Yes | _(empty)_ | SSH password |

### `.env` Example

```bash
NAS_HOST=192.168.1.100
NAS_PORT=22
NAS_USER=admin
NAS_PASSWORD=your_password_here
```

## Quick Start

### As MCP Server

```bash
mcp-ssh-nas
```

Add to Claude Code (`~/.claude.json`):

```json
{
  "mcpServers": {
    "ssh-nas": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-ssh-nas", "run", "mcp-ssh-nas"],
      "env": {
        "NAS_HOST": "192.168.1.100",
        "NAS_USER": "admin",
        "NAS_PASSWORD": "your_password"
      }
    }
  }
}
```

### As LangChain Tools

```python
from mcp_ssh_nas.langchain_tools import TOOLS, ssh_execute, ssh_docker_ps

# Use all 13 tools with an agent
agent = create_react_agent(llm, TOOLS)

# Or use individual tools
print(ssh_execute.invoke({"command": "uptime"}))
print(ssh_docker_ps.invoke({"all": False}))
```

### As Python Library

```python
from mcp_ssh_nas.client import SSHClient
from mcp_ssh_nas.operations import system, docker, files

client = SSHClient(host="192.168.1.100", user="admin", password="secret")
result = client.execute("ls -la /volume1/")
info = system.system_info(client)
containers = docker.docker_ps(client)
```

## License

MIT
