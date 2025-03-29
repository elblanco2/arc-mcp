# Arc MCP Development Guide

## Project Overview

Arc MCP is a Model Context Protocol (MCP) server that simplifies the deployment of web applications to various hosting environments. It's designed to work with Claude Desktop and other MCP clients to provide a conversational interface for deploying applications.

## Current Status

This is an early development version of Arc MCP with the following components implemented:

1. **Core Server Structure**
   - Main MCP server implementation
   - Tools, resources, and prompts registration
   - Command-line interface

2. **Credentials Management**
   - Secure storage and retrieval of provider credentials
   - Encryption for sensitive data

3. **Framework Handlers**
   - Wasp framework support
   - Framework detection logic
   - Deployment preparation for different providers

4. **Provider Handlers**
   - Support for Netlify, Vercel, shared hosting, and Hostm.com
   - Credential validation
   - Deployment implementation
   - Log analysis for troubleshooting

5. **Debugging Tools**
   - Debugging guide

## Project Structure

```
arc_mcp/
├── __init__.py           # Package initialization
├── __main__.py           # Entry point
├── server.py             # Main server implementation
├── credentials.py        # Credential management
├── frameworks/           # Framework handlers
│   ├── __init__.py       # Framework registry
│   ├── base.py           # Base framework handler
│   └── wasp.py           # Wasp framework implementation
├── providers/            # Provider handlers
│   ├── __init__.py       # Provider registry
│   ├── base.py           # Base provider handler
│   ├── netlify.py        # Netlify implementation
│   ├── vercel.py         # Vercel implementation
│   ├── shared_hosting.py # Shared hosting implementation
│   └── hostm.py          # Hostm.com implementation
└── debugging/            # Debugging tools
    └── DEBUG_GUIDE.md    # Debugging guide
```

## Development Roadmap

### Short-term Goals

1. **Complete Debugging Tools**
   - Implement `mcp_inspector.py` for interactive server testing
   - Implement `credential_validator.py` for validating provider credentials
   - Implement `deployment_analyzer.py` for analyzing deployment logs

2. **Add Additional Framework Support**
   - Implement Next.js framework handler
   - Implement Astro framework handler

3. **Testing Infrastructure**
   - Add unit tests for all components
   - Add integration tests for end-to-end testing
   - Set up CI/CD pipeline

### Medium-term Goals

1. **Enhanced Provider Support**
   - Add AWS Amplify provider
   - Add GitHub Pages provider
   - Add Firebase Hosting provider

2. **Expanded Framework Support**
   - Add support for SvelteKit
   - Add support for Remix
   - Add support for Nuxt.js

3. **Additional Features**
   - Add domain management
   - Add SSL certificate management
   - Add deployment monitoring

### Long-term Goals

1. **Web Interface**
   - Develop a web-based dashboard for managing deployments
   - Add real-time logs
   - Add deployment analytics

2. **CI/CD Integration**
   - Integrate with GitHub Actions
   - Integrate with GitLab CI
   - Integrate with CircleCI

## Contributing

### Development Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/elblanco2/arc-mcp.git
   cd arc-mcp
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

### Testing

Run tests with pytest:

```bash
python -m pytest
```

### Debugging

For debugging, use the tools in the `debugging` directory and follow the DEBUG_GUIDE.md instructions.

### Code Style

This project follows PEP 8 style guidelines. Use flake8 and black for linting and formatting:

```bash
flake8 arc_mcp
black arc_mcp
```

## Using with Claude Desktop

1. Edit your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add Arc MCP server configuration:
   ```json
   {
     "mcpServers": {
       "arc": {
         "command": "python",
         "args": [
           "-m",
           "arc_mcp",
           "--debug"
         ]
       }
     }
   }
   ```

3. Restart Claude Desktop

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
