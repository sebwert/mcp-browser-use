# browser-use MCP server

MCP server for browser-use

<a href="https://glama.ai/mcp/servers/dz6dy5hw59"><img width="380" height="200" src="https://glama.ai/mcp/servers/dz6dy5hw59/badge" alt="Browser-Use Server MCP server" /></a>

## Components

### Resources

The server implements a browser automation system with:
- Integration with browser-use library
- Custom browser automation capabilities
- Agent-based interaction system

### Requirements

- Python 3.11 or higher
- Dependencies listed in pyproject.toml including:
  - browser-use==0.1.19
  - OpenAI API access

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development Configuration</summary>

```json
"mcpServers": {
    "mcp_server_browser_use": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/project",
        "run",
        "mcp-server-browser-use",
      ]
    }
}
```
</details>

## Development

Sync dependencies and update lockfile:
```bash
uv sync
```

### Debugging

For debugging, use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/project run fastmcp run /path/to/project/src/mcp_server_browser_use/server.py
```

The Inspector will display a URL for the debugging interface.
