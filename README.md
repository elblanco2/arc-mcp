# Arc MCP

> Simplified web application deployment through conversational interfaces

Arc is a Model Context Protocol (MCP) server designed to bridge the gap between Large Language Models (LLMs) and hosting environments. It allows novice developers to deploy web applications through natural language conversations with AI assistants like Claude.

## Features

- **Framework Support**: Deploy Wasp applications with planned support for more frameworks
- **Multi-Provider**: Support for shared hosting via FTP/SFTP with planned support for more providers
- **Guided Deployments**: Conversational interface to guide users through the deployment process
- **Smart Synchronization**: Intelligent file transfer that only uploads changed files
- **Authentication Management**: Secure storage of hosting provider credentials
- **Troubleshooting**: Built-in tools to diagnose and fix common deployment issues

## Documentation

- [User Guide](docs/USER_GUIDE.md) - Comprehensive guide for using Arc MCP
- [Deployment Architecture](docs/DEPLOYMENT_ARCHITECTURE.md) - Technical overview of the Arc MCP system
- [Prompt Templates](docs/prompts/) - Ready-to-use prompts for common deployment scenarios

## Installation

```bash
pip install arc-mcp
```

## Quick Start

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

## Supported Frameworks

Currently, Arc supports:

- **Wasp**: The fastest way to develop full-stack web apps with React & Node.js

## Supported Providers

Currently, Arc supports:

- **Shared Hosting**: Traditional web hosting with FTP/SFTP access

## Available MCP Tools

Arc exposes the following MCP tools to LLMs:

1. `authenticate_provider`: Store authentication credentials for a hosting provider
2. `check_server_status`: Check the status of the configured server
3. `analyze_requirements`: Analyze deployment requirements for a framework/provider combination
4. `deploy_framework`: Deploy a framework to the specified hosting provider
5. `troubleshoot_deployment`: Analyze deployment errors and suggest solutions

## Example Deployment Workflow

1. **Authenticate** with your hosting provider
2. **Analyze** your project's requirements
3. **Configure** deployment parameters
4. **Deploy** your application
5. **Troubleshoot** any issues that arise

For a detailed walkthrough, see the [User Guide](docs/USER_GUIDE.md) or use one of our [Prompt Templates](docs/prompts/deploy_wasp_to_shared_hosting.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
