# browser-use MCP server

MCP server for browser-use

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
  - langchain and related packages
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
        "/path/to/mcp-server-browser-use",
        "run",
        "mcp_server_browser_use"
      ]
    }
}
```
</details>

<details>
  <summary>Published Configuration</summary>

```json
"mcpServers": {
    "browser": {
      "command": "uvx",
      "args": [
        "browser"
      ]
    }
}
```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

For debugging, use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/project run mcp_server_browser_use
```

The Inspector will display a URL for the debugging interface.
