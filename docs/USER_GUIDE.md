# Arc MCP Server User Guide

This guide provides detailed instructions for using Arc MCP Server with Claude or other LLMs to deploy web applications to various hosting environments.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Configuration](#configuration)
- [Basic Usage](#basic-usage)
- [Detailed Workflow](#detailed-workflow)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Available Prompts](#available-prompts)

## Introduction

Arc is a Model Context Protocol (MCP) server designed to simplify web application deployment through conversational interfaces. It allows you to deploy applications to hosting providers using natural language conversations with AI assistants like Claude.

Arc specializes in:
- Framework-specific deployments (currently focusing on Wasp)
- Provider-specific deployment strategies (currently focusing on shared hosting via FTP/SFTP)
- Automated build and deployment processes
- Intelligent file synchronization
- Error detection and troubleshooting

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for repository management)
- Node.js (for Wasp applications)

### Install via pip

```bash
pip install arc-mcp
```

### Install from source

```bash
git clone https://github.com/elblanco2/arc-mcp.git
cd arc-mcp
pip install -e .
```

### Claude Configuration

To use Arc with Claude, add the following to your Claude desktop configuration file:

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

## Configuration

Arc doesn't require explicit configuration files. Instead, it stores:

- Credentials in `~/.arc/credentials/` (encrypted)
- Temporary build files in system temp directories
- Logs in `~/.arc/logs/`

## Basic Usage

### Quick Start

1. Start a conversation with Claude
2. Describe your deployment needs, specifying:
   - The framework you're using (e.g., Wasp)
   - The hosting provider (e.g., shared hosting)
   - The source code location
   - The target deployment location
3. Claude will guide you through the process using Arc tools

### Example Conversation

```
User: I need to deploy my Wasp application from my local directory ~/projects/my-app to my shared hosting provider at example.com.

Claude: I can help you deploy your Wasp application to shared hosting using Arc. Let's go through this step by step.

First, I'll need your shared hosting credentials. Can you provide:
- Hostname
- Username
- Password
- Port number
- Protocol (FTP or SFTP)

User: [Provides credentials]

Claude: [Uses Arc to authenticate, analyze requirements, and deploy]
```

## Detailed Workflow

### 1. Authentication

Before deployment, Arc needs to authenticate with your hosting provider:

```
Claude: I'll store your credentials securely using the authenticate_provider tool.

[Claude calls authenticate_provider with your credentials]

Claude: Authentication successful! Your credentials are now securely stored for future deployments.
```

### 2. Project Analysis

Arc analyzes your project to determine requirements:

```
Claude: Now I'll analyze your Wasp project to determine deployment requirements.

[Claude calls analyze_requirements]

Claude: Analysis complete! Your project requires:
- Node.js version >=14.0.0
- Environment variables: DATABASE_URL, JWT_SECRET
- Build command: wasp build
- Output directory: .wasp/build/web-app
```

### 3. Deployment Configuration

Configure the deployment parameters:

```
Claude: Based on the analysis, I recommend the following deployment configuration:
- Enable backup: Yes (recommended)
- Sync mode: "smart" (only uploads changed files)
- Required environment variables:
  * DATABASE_URL: [You need to provide this]
  * JWT_SECRET: [You need to provide this]

Would you like to proceed with this configuration?
```

### 4. Deployment Execution

Execute the deployment process:

```
Claude: Proceeding with deployment...

[Claude calls deploy_framework]

Claude: Deployment completed successfully!
- Files uploaded: 128
- Files skipped (unchanged): 42
- Total files: 170
- Deployment URL: https://example.com/my-app
```

### 5. Troubleshooting (if needed)

If deployment fails, Arc provides troubleshooting assistance:

```
Claude: The deployment encountered an error. Let me troubleshoot it for you.

[Claude calls troubleshoot_deployment]

Claude: I've identified the issue:
- Problem: Missing DATABASE_URL environment variable
- Solution: Add this variable to your deployment configuration
```

## Advanced Configuration

### Sync Modes

Arc supports three synchronization modes:

1. **Smart** (default): Uploads only changed files based on size, modification time, and content hash comparison
2. **Full**: Uploads all files, overwriting existing files
3. **Incremental**: Uploads only new files, never overwrites existing files

Example configuration:

```json
{
  "sync_mode": "smart",
  "backup": true,
  "clean_destination": false,
  "exclusions": [".git", "node_modules", ".env", ".DS_Store"]
}
```

### Environment Variables

Specify environment variables for the build process:

```json
{
  "env": {
    "DATABASE_URL": "postgresql://user:password@localhost:5432/mydb",
    "JWT_SECRET": "your-secret-key",
    "NODE_ENV": "production"
  }
}
```

## Troubleshooting

### Common Issues

#### Authentication Failures

```
Problem: Failed to connect: Connection refused
Solution: Verify hostname, port, and that FTP/SFTP services are running
```

```
Problem: Authentication failed
Solution: Check username and password
```

#### Build Failures

```
Problem: Build failed with exit code 1
Solution: Check error log for details, ensure all dependencies are installed
```

```
Problem: Node.js version incompatible
Solution: Install the required Node.js version (>=14.0.0 for Wasp)
```

#### Deployment Failures

```
Problem: Failed to upload file: Permission denied
Solution: Check file permissions on the server
```

```
Problem: Directory does not exist
Solution: Ensure the destination path exists or allow Arc to create it
```

### Debug Mode

Run Arc in debug mode for more detailed logs:

```bash
python -m arc --debug
```

## Best Practices

1. **Always enable backups** before deployment (default)
2. **Use smart sync mode** to minimize upload time and server load
3. **Check project locally** before deployment to catch errors early
4. **Keep environment variables secure** and never share them in public conversations
5. **Use SFTP instead of FTP** when possible for better security
6. **Clone your repository locally** before deployment for best control
7. **Ensure destination paths exist** on the server or can be created

## Available Prompts

Arc includes predefined prompts to help guide the conversation:

### Deploy Wasp to Shared Hosting

Use this prompt template to deploy a Wasp application to shared hosting:

[Deployment Prompt](/docs/prompts/deploy_wasp_to_shared_hosting.md)

### More Prompt Templates

Check the `/docs/prompts/` directory for additional prompt templates supporting other frameworks and providers as they are added to Arc.
