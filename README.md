# Arc MCP

> Simplified web application deployment through conversational interfaces

Arc is a Model Context Protocol (MCP) server designed to bridge the gap between Large Language Models (LLMs) and hosting environments. It allows novice developers to deploy web applications through natural language conversations with AI assistants like Claude.

## Features

- **Framework Support**: Deploy Wasp applications with planned support for more frameworks
- **Multi-Provider**: Support for Netlify, Vercel, traditional shared hosting, and Hostm.com
- **Guided Deployments**: Conversational interface to guide users through the deployment process
- **Authentication Management**: Secure storage of hosting provider credentials
- **Troubleshooting**: Built-in tools to diagnose and fix common deployment issues

## Installation

```bash
pip install arc-mcp
```

## Usage

### Starting the server

```bash
arc --debug
```

### Python API

```python
from arc.server import ArcServer

server = ArcServer(debug=True)
server.start()
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "arc": {
      "command": "python",
      "args": [
        "-m",
        "arc",
        "--debug"
      ]
    }
  }
}
```

## Tools

Arc exposes the following MCP tools:

1. `authenticate_provider`: Store authentication credentials for a hosting provider
2. `check_server_status`: Check the status of the configured server
3. `analyze_requirements`: Analyze deployment requirements for a framework/provider combination
4. `deploy_framework`: Deploy a framework to the specified hosting provider
5. `troubleshoot_deployment`: Analyze deployment errors and suggest solutions

## License

MIT
