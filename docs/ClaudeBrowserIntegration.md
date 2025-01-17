# Integrating `my_mcp_server` with Claude Browser Interface

This guide provides detailed steps for setting up and integrating the **my_mcp_server** project with Claude's browser interface. By following these instructions, you will enable seamless communication between Claude and this MCP server for interactive browser-based automation.

---

## Overview

- **my_mcp_server**: A Python-based MCP server that leverages FastAPI and SSE to provide browser-oriented tools and resources.
- **Claude (Desktop / Browser)**: The AI client that can connect to MCP servers and use the provided tools (e.g., launching a browser, executing tasks).

This document covers local usage with Python and Docker setups, Claude configuration, and usage examples.

---

## 1. Prerequisites

1. **Python 3.10+**
   Ensure you have Python 3.10 or later installed on your system if you plan to run **my_mcp_server** locally without Docker.

2. **Claude for Desktop** (or your chosen Claude environment supporting MCP)
   - Download and install Claude for Desktop from its official site.
   - Confirm you can locate its configuration file for MCP integrations.

3. **Browser** (Chrome or Chromium recommended)
   - For real browser automation tasks, ensure you have a Chrome/Chromium install.
   - If you only want to demonstrate or test the server's endpoints, an actual browser can remain optional, but most use-cases benefit from a real browser for tasks.

4. **Node.js** (optional)
   - If you plan to run the server within a Node-based environment or test with certain tools. Not strictly required unless your environment demands it.

---

## 2. Cloning and Installing `my_mcp_server`

### 2.1 Local Python Installation

1. **Clone the repository** (or copy the my_mcp_server directory into your project):
   ```bash
   git clone https://github.com/your-username/my_mcp_server.git
   cd my_mcp_server
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # For Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt  # If provided
   # or:
   pip install .
   ```

   The `pyproject.toml` ensures that all needed packages (like `mcp`, `browser-use`, `fastapi`, etc.) are installed.

4. **Run the server**:
   ```bash
   python -m my_mcp_server.main
   ```
   By default, it starts a FastAPI server on port 8031 (see [main.py](../main.py)).
   - SSE endpoint: `http://127.0.0.1:8031/sse`
   - JSON-RPC messages endpoint: `http://127.0.0.1:8031/message`

### 2.2 Docker Installation

If you prefer a containerized setup:

1. **Build the Docker image** from the root of `my_mcp_server`:
   ```bash
   docker build -t my_mcp_server .
   ```

2. **Run the container**:
   ```bash
   docker run --rm -p 8031:8031 my_mcp_server
   ```
   This exposes the same SSE and JSON-RPC endpoints on port `8031`.

---

## 3. Configuring Claude to Use `my_mcp_server`

> **Note**: Claude for Desktop is among the clients supporting MCP. Below instructions show how to add `my_mcp_server` to Claude’s configuration.

1. **Locate Claude Desktop config file**:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%/Claude/claude_desktop_config.json`

   If the file does not exist, create it.

2. **Add your server entry** to `mcpServers`:
   ```json
   {
     "mcpServers": {
       "browserUseServer": {
         "command": "python",
         "args": [
           "-m",
           "my_mcp_server.main"
         ]
       }
     }
   }
   ```
   **OR** if using Docker:
   ```json
   {
     "mcpServers": {
       "browserUseServer": {
         "command": "docker",
         "args": [
           "run",
           "--rm",
           "-p",
           "8031:8031",
           "my_mcp_server"
         ]
       }
     }
   }
   ```

3. **Restart Claude Desktop**:
   After editing `claude_desktop_config.json`, fully restart Claude for Desktop. If `my_mcp_server` is running, Claude should detect it and display the associated tools via the MCP UI elements.

---

## 4. Browser Setup and Customization

Within `server.py`, `my_mcp_server` relies on the `browser_use` library to manage tasks and automation. You may want to adjust:

- **Headless mode** (`headless=True` in the `browser_launch` tool or in the `BrowserConfig`).
- **Vision toggling** (the `vision_toggle` tool).
- **LLM configuration**:
  - By default, we rely on environment variables or arguments to provide LLM credentials (OpenAI or other).

Adjust these settings to your needs and re-run the server. For local usage, you can directly modify `[server.py](../server.py)` or pass environment variables.

---

## 5. Usage Examples

Once `my_mcp_server` is running and recognized by Claude, you can:

1. **Open Claude Desktop** and start a conversation.
2. **Request a browser-based automation**. For example:
   ```
   I'd like to open a new browser session and go to https://example.com
   ```
   Claude checks available tools from `my_mcp_server`:
   - `browser_launch` can be invoked to start a session.
   - `task_execute` might be used to navigate or click elements.

3. **Claude calls the relevant tool** and displays a permission request. You can see the logs in your `my_mcp_server` console or Docker logs.

4. **Check the action log resource**:
   - In Claude’s attachments, you might see a resource named `Browser-Use Action History`. Reading it reveals a text summary of actions performed by the browser.

### 5.1 Example: Start a Headless Browser

In Claude chat, type:

```
Claude, please launch a headless browser session.
```

Claude might respond by calling:
```json
{
  "tool": "browser_launch",
  "arguments": {
    "headless": true
  }
}
```
You will be asked to approve. `my_mcp_server` logs your new session. Then you can proceed with additional steps.

### 5.2 Example: Navigate and Validate

```
Claude, can you open https://wikipedia.org and search for 'Model Context Protocol'?
Afterwards, validate the page loaded successfully and show me the result.
```

Claude might chain calls to:
1. `task_execute` with steps to navigate and search.
2. `task_validate` to confirm results.

---

## 6. Real-World Applications

1. **Automated Web Testing**
   Use Claude to create test scripts that run in a real browser, interacting with forms and capturing results.

2. **Data Gathering**
   Prompt Claude to gather data from multiple websites, fill forms, or scrape certain details.

3. **Browser-based Demo**
   If you’re showcasing an app or website, let Claude steer the demonstration by calling these tools.

---

## 7. Advanced Customization

### 7.1 SSE vs. Stdio

**my_mcp_server** is configured to use **SSE** by default with FastAPI in `main.py`. If you prefer local testing with STDIO transport, run:
```bash
python -m my_mcp_server.server
```
which calls `run_server_stdio()`.

Claude typically uses SSE if you configure it in `claude_desktop_config.json`. You can adapt the approach if you prefer the stdio method.

### 7.2 Additional Tools

Feel free to define new tools in `server.py` with the `@app.call_tool()` and `@app.list_tools()` patterns. For instance, you might add:
```python
types.Tool(
    name="my_custom_tool",
    description="Performs custom logic",
    inputSchema={ ... }
)
```
Then handle it in the `call_tool_handler()` to offer specialized functionality.

---

## 8. Troubleshooting

1. **Claude doesn’t list tools**
   - Verify the server is running and accessible on port 8031.
   - Check logs in `Claude` for any MCP connection issues.
   - Confirm `mcpServers` configuration.

2. **Browser not launching**
   - Make sure you have Chrome installed or specify the path in `server.py`.
   - Check logs for environment or permission errors.

3. **Permission denied on Docker**
   - If Docker can’t bind port 8031 or run the container, ensure you’re using correct Docker privileges and the port is free.

4. **LLM issues**
   - If `my_mcp_server` attempts LLM calls but fails, confirm you have valid OpenAI or other provider credentials. Check environment variables like `OPENAI_API_KEY`.

---

## 9. Conclusion

With these steps, you can integrate **my_mcp_server** into Claude’s browser environment. This setup allows you to harness the power of AI-driven interactions, bridging your local or containerized server to a live browser.

**Happy automating!**

For further inquiries or deeper customizations, consult the inline comments within `server.py` and `main.py`, or review official MCP documentation for advanced usage patterns.