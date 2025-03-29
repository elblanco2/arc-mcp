# Arc MCP Server Debugging Guide

This guide walks you through the process of debugging issues with the Arc MCP server. It covers common problems and their solutions.

## Prerequisites

- Python 3.10+
- Arc MCP Server installed
- Claude Desktop or another MCP client
- Basic familiarity with terminal/command line

## Debugging Tools

The Arc MCP server comes with several debugging tools:

1. **MCP Inspector** (`mcp_inspector.py`): Interactive tool for testing MCP servers
2. **Credential Validator** (`credential_validator.py`): Tool for validating provider credentials
3. **Deployment Analyzer** (`deployment_analyzer.py`): Tool for analyzing deployment logs

## Step 1: Check Your Environment

Before diving into debugging, verify your environment:

```bash
# Check Python version
python --version

# Check Arc MCP installation
pip show arc-mcp-server

# Check Claude Desktop configuration
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

## Step 2: Enable Debug Logging

Enable debug logging to get more detailed information:

```bash
# Run Arc MCP with debug logging
arc --debug

# Or with Claude Desktop, update configuration:
# "mcpServers": {
#   "arc": {
#     "command": "python",
#     "args": ["-m", "arc_mcp", "--debug"]
#   }
# }
```

## Step 3: Check Server Connectivity

Verify the server is running and connecting properly:

```bash
# View logs in real-time on macOS
tail -n 20 -F ~/Library/Logs/Claude/mcp*.log

# Check if server is responding
python mcp_inspector.py --command "python -m arc_mcp" --transport stdio
```

## Step 4: Validate Provider Credentials

If you're having issues with deployments, check your credentials:

```bash
# Validate Netlify credentials
python credential_validator.py --provider netlify --key YOUR_API_KEY

# Validate Vercel credentials
python credential_validator.py --provider vercel --token YOUR_TOKEN

# Validate shared hosting credentials
python credential_validator.py --provider shared-hosting --host HOST --username USER --password PASS --protocol ftp
```

## Step 5: Test Tools Individually

Test specific tools to isolate issues:

```bash
# Test credentials tool
python mcp_inspector.py --command "python -m arc_mcp" --tool validate_credentials --params '{"provider": "netlify", "credentials": {"api_key": "YOUR_API_KEY"}}'

# Test deployment tool
python mcp_inspector.py --command "python -m arc_mcp" --tool deploy_project --params '{"path": "/path/to/project", "provider": "netlify", "options": {"site_name": "your-site"}}'
```

## Step 6: Analyze Deployment Logs

If a deployment fails, analyze the logs:

```bash
# Save logs to a file first
python mcp_inspector.py --command "python -m arc_mcp" --tool deploy_project --params '{"path": "/path/to/project", "provider": "netlify", "options": {"site_name": "your-site"}}' > deployment.log

# Analyze the logs
python deployment_analyzer.py --provider netlify --log-file deployment.log
```

## Common Issues and Solutions

### Connection Issues

**Problem**: Claude Desktop can't connect to the Arc MCP server

**Solutions**:
- Check if the server is running
- Verify the configuration in `claude_desktop_config.json`
- Ensure the working directory is correct
- Check for error messages in Claude Desktop logs

### Credential Issues

**Problem**: Provider credential validation fails

**Solutions**:
- Verify credentials with provider's website/dashboard
- Use the credential validator to check credentials independently
- Check for expired tokens or API keys
- Ensure you have the necessary permissions

### Deployment Issues

**Problem**: Deployments fail

**Solutions**:
- Check deployment logs for specific errors
- Use the deployment analyzer to identify common issues
- Verify project structure is compatible with the provider
- Test deploying directly with provider tools (e.g., Netlify CLI)
- Check for framework-specific requirements

### Framework Detection Issues

**Problem**: Arc MCP fails to detect the framework type

**Solutions**:
- Verify the project has the expected structure
- Specify the framework type explicitly in deployment options
- Check if the framework is supported by Arc MCP
- Ensure the framework's configuration files are present

### Missing Dependencies

**Problem**: Deployment fails due to missing dependencies

**Solutions**:
- Check that all required CLI tools are installed (netlify-cli, vercel, etc.)
- Verify project dependencies are installed and up-to-date
- Check environment variables in the MCP server's environment
- Install any missing npm/pip packages
