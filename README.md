# My MCP Server (Browser-Use Edition)

This repository provides a **Model Context Protocol (MCP)** server that integrates the [browser-use](https://github.com/agi-ant/browser-use) Python library. It allows programmatic browser control and web automation via MCP clients such as Claude Desktop.

## Features

1. **Resource**: Exposes a dynamic resource that can provide a summary of recent browser actions.
2. **Prompts**: Offers a prompt named `mcp-demo` that guides users through launching a browser, navigating pages, and performing tasks.
3. **Tools**: Implements core browser-focused tools, including:
   - `browser_launch` to start or attach to a browser session
   - `task_execute` to run multi-step tasks with optional LLM guidance
   - `session_manage` to manage session persistence
   - and additional convenience tools: `llm_configure`, `history_export`, `task_validate`, and `vision_toggle`

## Requirements

- Python 3.10+
- The `browser-use` library for controlling the browser
- `mcp` library for the Model Context Protocol

## Installation

```bash
# From the project root directory
pip install .
```

## Usage (Local)

```bash
# Using uvicorn
uvicorn my_mcp_server.main:app --port 8031 --host 127.0.0.1
# or
python -m my_mcp_server.main
```

After running, you can connect an MCP client via SSE or stdio if you integrate with a suitable front end (like Claude Desktop or your own custom client).

## Docker

```bash
docker build -t my_mcp_server .
docker run --rm -p 8031:8031 my_mcp_server
```

## Notes

- For local development, ensure you have a running Chrome/Chromium if you wish to do real browser automation.
- This server can still function in "headless" mode if configured. See the `browser_launch` tool usage.

## License

This project is licensed under the MIT License.