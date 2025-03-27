# Arc MCP Server: Deployment Architecture

## Overview

Arc MCP Server is a specialized backend service designed to simplify and automate the deployment of web applications. It follows the Model Context Protocol (MCP) which enables Large Language Models (LLMs) like Claude to interact with it via structured tool calls. Arc primarily focuses on providing a seamless deployment experience for frameworks like Wasp to traditional hosting environments like Shared Hosting via FTP/SFTP.

## Architecture Components

Arc is composed of several interconnected components that work together to provide a complete deployment solution:

### 1. MCP Server Core (`server.py`)

The core of Arc is an MCP server implementation that:
- Exposes a standardized API for LLMs to discover and use capabilities
- Registers tools, resources, and prompts
- Manages authentication and credentials
- Orchestrates the entire deployment process

### 2. Framework Handlers (`frameworks/`)

Framework-specific modules that understand how to:
- Analyze project structure and requirements
- Build applications using framework-specific commands
- Identify environment variables and dependencies
- Troubleshoot common framework-specific issues

Currently implemented:
- **Wasp**: Specializes in Wasp web applications with React frontends and Node.js backends

### 3. Provider Handlers (`providers/`)

Provider-specific modules that manage the connection to different hosting environments:
- Handle authentication and validation
- Implement file transfer protocols (FTP/SFTP)
- Manage server-side operations (backups, synchronization, etc.)
- Handle provider-specific configurations

Currently implemented:
- **Shared Hosting**: Traditional web hosting with FTP/SFTP access

### 4. Credential Manager (`credentials.py`)

Securely manages authentication credentials:
- Encrypts and stores provider credentials
- Retrieves credentials when needed for deployment operations
- Validates credential format and connectivity

## Deployment Workflow

The following diagram illustrates the typical workflow when deploying a web application using Arc:

```
┌────────┐     ┌───────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   LLM  │────►│ Authentication    │────►│ Requirements    │────►│ Build & Deploy   │
│(Claude)│     │ Tool              │     │ Analysis Tool   │     │ Tool             │
└────────┘     └───────────────────┘     └─────────────────┘     └──────────────────┘
                        │                        │                        │
                        ▼                        ▼                        ▼
              ┌───────────────────┐    ┌──────────────────┐     ┌──────────────────┐
              │ Credential        │    │ Framework        │     │ Framework        │
              │ Manager           │    │ Handler          │     │ Handler (Build)  │
              └───────────────────┘    └──────────────────┘     └──────────────────┘
                                                                         │
                                                                         ▼
                                                               ┌──────────────────┐
                                                               │ Provider         │
                                                               │ Handler (Deploy) │
                                                               └──────────────────┘
```

## Detailed Deployment Process

When deploying a Wasp application to Shared Hosting, the following process is executed:

### 1. Authentication

- The LLM calls `authenticate_provider` with hosting credentials
- Arc validates the credentials by attempting a connection
- Credentials are securely stored for future use

### 2. Requirements Analysis

- The LLM calls `analyze_requirements` with the project path
- The Wasp framework handler:
  - Verifies the project is a valid Wasp application
  - Examines the `.wasp` file to extract app information
  - Checks for dependencies in `package.json` files
  - Identifies required environment variables
  - Analyzes compatibility with the target provider

### 3. Build Process

- The LLM calls `deploy_framework` with configuration parameters
- The Wasp framework handler:
  - Executes `wasp build` command in the project directory
  - Passes any required environment variables to the build process
  - Collects the built output from `.wasp/build/web-app`

### 4. Deployment Process

- The shared hosting provider handler:
  - Connects to the hosting server via FTP/SFTP
  - Creates a backup if requested (default: enabled)
  - Determines which files need uploading based on the sync mode
  - Creates necessary directories on the server
  - Uploads the built files to the target location
  - Reports statistics (files uploaded, skipped, etc.)

### 5. Troubleshooting (if needed)

- The LLM can call `troubleshoot_deployment` if errors occur
- Arc analyzes the project and error logs for common issues
- Provider-specific and framework-specific troubleshooting recommendations are provided

## Smart Synchronization

Arc implements an intelligent file synchronization algorithm:

- **Full Sync**: Uploads all files, overwriting existing files
- **Incremental Sync**: Uploads only new files, never overwrites
- **Smart Sync** (default): Uploads only changed or new files, using:
  - File size comparison
  - Modification time comparison
  - Content hash comparison (when available)

## Security Considerations

- Credentials are stored encrypted in the user's home directory
- Connection security depends on the protocol (SFTP is more secure than FTP)
- Backup functionality preserves data before making changes
- Transactional nature ensures deployment is atomic when possible

## Extension Points

The Arc architecture is designed for extensibility:

- New frameworks can be added by implementing the `FrameworkHandler` interface
- New providers can be added by implementing the `ProviderHandler` interface
- New tools can be registered with the MCP server for additional functionality

## Intended Use Pattern

Arc is designed to be used through conversational interfaces with LLMs:

1. User describes their deployment needs to the LLM
2. LLM interprets the request and calls appropriate Arc tools
3. Arc executes technical operations (build, file transfer, etc.)
4. Results are returned to the LLM, which presents them to the user
5. If issues arise, the LLM can call troubleshooting tools and guide the user

This approach abstracts away technical complexity while maintaining full control over the deployment process.
