<img src="./assets/web-ui.png" alt="Browser Use Web UI" width="full"/>

<br/>

# browser-use MCP server & CLI
[![Documentation](https://img.shields.io/badge/Documentation-📕-blue)](https://docs.browser-use.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **Project Note**: This MCP server implementation builds upon the [browser-use/web-ui](https://github.com/browser-use/web-ui) foundation. Core browser automation logic and configuration patterns are adapted from the original project.

AI-driven browser automation server implementing the Model Context Protocol (MCP) for natural language browser control and web research. Also provides CLI access to its core functionalities.

<a href="https://glama.ai/mcp/servers/@Saik0s/mcp-browser-use"><img width="380" height="200" src="https://glama.ai/mcp/servers/@Saik0s/mcp-browser-use/badge" alt="Browser-Use MCP server" /></a>

## Features

-   🧠 **MCP Integration** - Full protocol implementation for AI agent communication.
-   🌐 **Browser Automation** - Page navigation, form filling, element interaction via natural language (`run_browser_agent` tool).
-   👁️ **Visual Understanding** - Optional screenshot analysis for vision-capable LLMs.
-   🔄 **State Persistence** - Option to manage a server browser session across multiple MCP calls or connect to user's browser.
-   🔌 **Multi-LLM Support** - Integrates with OpenAI, Anthropic, Azure, DeepSeek, Google, Mistral, Ollama, OpenRouter, Alibaba, Moonshot, Unbound AI.
-   🔍 **Deep Research Tool** - Dedicated tool for multi-step web research and report generation (`run_deep_research` tool).
-   ⚙️ **Environment Variable Configuration** - Fully configurable via environment variables using a structured Pydantic model.
-   🔗 **CDP Connection** - Ability to connect to and control a user-launched Chrome/Chromium instance via Chrome DevTools Protocol.
-   ⌨️ **CLI Interface** - Access core agent functionalities (`run_browser_agent`, `run_deep_research`) directly from the command line for testing and scripting.

## Quick Start

### Prerequisites

-   Python 3.11 or higher
-   `uv` (fast Python package installer): `pip install uv`
-   Chrome/Chromium browser installed
-   Install Playwright browsers: `uv sync` and then `uv run playwright install`

### Integration with MCP Clients (e.g., Claude Desktop)

You can configure clients like Claude Desktop to connect to this server. Add the following structure to the client's configuration (e.g., `claude_desktop_config.json`), adjusting the path and environment variables as needed:

```json
// Example for Claude Desktop config
"mcpServers": {
    "browser-use": {
      // Option 1: Run installed package
      "command": "uvx",
      "args": ["mcp-server-browser-use@latest"],

      // Option 2: Run from local development source
      // "command": "uv",
      // "args": [
      //   "--directory",
      //   "/path/to/mcp-server-browser-use",
      //   "run",
      //   "mcp-server-browser-use"
      // ],
      "env": {
        // --- CRITICAL: Add required API keys here ---
        "MCP_LLM_OPENROUTER_API_KEY": "YOUR_OPENROUTER_API_KEY",
        // "MCP_LLM_OPENAI_API_KEY": "YOUR_KEY_HERE_IF_USING_OPENAI",
        // "MCP_LLM_ANTHROPIC_API_KEY": "YOUR_KEY_HERE_IF_USING_ANTHROPIC",
        // ... add other keys based on MCP_LLM_PROVIDER ...

        // --- Optional Overrides (defaults are usually fine) ---
        "MCP_LLM_PROVIDER": "openrouter", // Use OpenRouter as provider
        "MCP_LLM_MODEL_NAME": "google/gemini-1.5-pro", // Example OpenRouter model
        "MCP_BROWSER_HEADLESS": "true",    // Default: run browser without UI

        // --- Example for connecting to your own browser ---
        // "MCP_BROWSER_USE_OWN_BROWSER": "true",
        // "MCP_BROWSER_CDP_URL": "http://localhost:9222",

        // Ensure Python uses UTF-8
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
        "PYTHONUTF8": "1"
      }
    }
}
```

**Important:** Ensure the `command` and `args` correctly point to how you want to run the server. Set the necessary API keys in the `env` section using the new structured variable names (e.g., `MCP_LLM_PROVIDER`, `MCP_LLM_OPENAI_API_KEY`).

## MCP Tools

This server exposes the following tools via the Model Context Protocol:

### Synchronous Tools (Wait for Completion)

1.  **`run_browser_agent`**
    *   **Description:** Executes a browser automation task based on natural language instructions and waits for it to complete. Uses settings from `MCP_AGENT_TOOL_*`, `MCP_LLM_*`, and `MCP_BROWSER_*` environment variables.
    *   **Arguments:**
        *   `task` (string, required): The primary task or objective.
        *   `add_infos` (string, optional): Additional context or hints for the agent.
    *   **Returns:** (string) The final result extracted by the agent or an error message.

2.  **`run_deep_research`**
    *   **Description:** Performs in-depth web research on a topic, generates a report, and waits for completion. Uses settings from `MCP_RESEARCH_TOOL_*`, `MCP_LLM_*`, and `MCP_BROWSER_*` environment variables.
    *   **Arguments:**
        *   `research_task` (string, required): The topic or question for the research.
        *   `max_parallel_browsers` (integer, optional): Overrides `MCP_RESEARCH_TOOL_MAX_PARALLEL_BROWSERS` from environment.
    *   **Returns:** (string) The generated research report in Markdown format, including the file path, or an error message.

## CLI Usage

This package also provides a command-line interface `mcp-browser-cli` for direct testing and scripting.

**Global Options:**
*   `--env-file PATH, -e PATH`: Path to a `.env` file to load configurations from.
*   `--log-level LEVEL, -l LEVEL`: Override the logging level (e.g., `DEBUG`, `INFO`).

**Commands:**

1.  **`mcp-browser-cli run-browser-agent [OPTIONS] TASK`**
    *   **Description:** Runs a browser agent task.
    *   **Arguments:**
        *   `TASK` (string, required): The primary task for the agent.
    *   **Options:**
        *   `--add-infos TEXT, -a TEXT`: Additional context or hints.
    *   **Example:**
        ```bash
        mcp-browser-cli run-browser-agent "Go to example.com and find the title." -e .env
        ```

2.  **`mcp-browser-cli run-deep-research [OPTIONS] RESEARCH_TASK`**
    *   **Description:** Performs deep web research.
    *   **Arguments:**
        *   `RESEARCH_TASK` (string, required): The topic or question for research.
    *   **Options:**
        *   `--max-parallel-browsers INTEGER, -p INTEGER`: Override `MCP_RESEARCH_TOOL_MAX_PARALLEL_BROWSERS`.
    *   **Example:**
        ```bash
        mcp-browser-cli run-deep-research "What are the latest advancements in AI-driven browser automation?" --max-parallel-browsers 5 -e .env
        ```

All other configurations (LLM keys, paths, browser settings) are picked up from environment variables (or the specified `.env` file) as detailed in the Configuration section.

## Configuration (Environment Variables)

Configure the server and CLI using environment variables. You can set these in your system or place them in a `.env` file in the project root (use `--env-file` for CLI). Variables are structured with prefixes.

| Variable Group (Prefix)             | Example Variable                               | Description                                                                                                | Default Value                     |
| :---------------------------------- | :--------------------------------------------- | :--------------------------------------------------------------------------------------------------------- | :-------------------------------- |
| **Main LLM (MCP_LLM_)**             |                                                | Settings for the primary LLM used by agents.                                                               |                                   |
|                                     | `MCP_LLM_PROVIDER`                             | LLM provider. Options: `openai`, `azure_openai`, `anthropic`, `google`, `mistral`, `ollama`, etc.         | `anthropic`                       |
|                                     | `MCP_LLM_MODEL_NAME`                           | Specific model name for the provider.                                                                      | `claude-3-7-sonnet-20250219`      |
|                                     | `MCP_LLM_TEMPERATURE`                          | LLM temperature (0.0-2.0).                                                                                 | `0.0`                             |
|                                     | `MCP_LLM_BASE_URL`                             | Optional: Generic override for LLM provider's base URL.                                                    | Provider-specific                 |
|                                     | `MCP_LLM_API_KEY`                              | Optional: Generic LLM API key (takes precedence).                                                          | -                                 |
|                                     | `MCP_LLM_OPENAI_API_KEY`                       | API Key for OpenAI (if provider is `openai`).                                                              | -                                 |
|                                     | `MCP_LLM_ANTHROPIC_API_KEY`                    | API Key for Anthropic.                                                                                     | -                                 |
|                                     | `MCP_LLM_GOOGLE_API_KEY`                       | API Key for Google AI (Gemini).                                                                            | -                                 |
|                                     | `MCP_LLM_AZURE_OPENAI_API_KEY`                 | API Key for Azure OpenAI.                                                                                  | -                                 |
|                                     | `MCP_LLM_AZURE_OPENAI_ENDPOINT`                | **Required if using Azure.** Your Azure resource endpoint.                                                 | -                                 |
|                                     | `MCP_LLM_OLLAMA_ENDPOINT`                      | Ollama API endpoint URL.                                                                                   | `http://localhost:11434`          |
|                                     | `MCP_LLM_OLLAMA_NUM_CTX`                       | Context window size for Ollama models.                                                                     | `32000`                           |
| **Planner LLM (MCP_LLM_PLANNER_)**  |                                                | Optional: Settings for a separate LLM for agent planning. Defaults to Main LLM if not set.                |                                   |
|                                     | `MCP_LLM_PLANNER_PROVIDER`                     | Planner LLM provider.                                                                                      | Main LLM Provider                 |
|                                     | `MCP_LLM_PLANNER_MODEL_NAME`                   | Planner LLM model name.                                                                                    | Main LLM Model                    |
| **Browser (MCP_BROWSER_)**          |                                                | General browser settings.                                                                                  |                                   |
|                                     | `MCP_BROWSER_HEADLESS`                         | Run browser without UI (general setting).                                                                  | `true`                            |
|                                     | `MCP_BROWSER_DISABLE_SECURITY`                 | Disable browser security features (general setting, use cautiously).                                       | `false`                           |
|                                     | `MCP_BROWSER_BINARY_PATH`                      | Path to Chrome/Chromium executable.                                                                        | -                                 |
|                                     | `MCP_BROWSER_USER_DATA_DIR`                    | Path to Chrome user data directory.                                                                        | -                                 |
|                                     | `MCP_BROWSER_WINDOW_WIDTH`                     | Browser window width (pixels).                                                                             | `1280`                            |
|                                     | `MCP_BROWSER_WINDOW_HEIGHT`                    | Browser window height (pixels).                                                                            | `720`                             |
|                                     | `MCP_BROWSER_USE_OWN_BROWSER`                  | Connect to user's browser via CDP URL.                                                                     | `false`                           |
|                                     | `MCP_BROWSER_CDP_URL`                          | CDP URL (e.g., `http://localhost:9222`). Required if `MCP_BROWSER_USE_OWN_BROWSER=true`.                  | -                                 |
|                                     | `MCP_BROWSER_KEEP_OPEN`                        | Keep server-managed browser open between MCP calls (if `MCP_BROWSER_USE_OWN_BROWSER=false`).               | `false`                           |
|                                     | `MCP_BROWSER_TRACE_PATH`                       | Directory to save Playwright trace files.                                                                  | `./tmp/trace`                     |
| **Agent Tool (MCP_AGENT_TOOL_)**    |                                                | Settings for the `run_browser_agent` tool.                                                                 |                                   |
|                                     | `MCP_AGENT_TOOL_MAX_STEPS`                     | Max steps per agent run.                                                                                   | `100`                             |
|                                     | `MCP_AGENT_TOOL_MAX_ACTIONS_PER_STEP`          | Max actions per agent step.                                                                                | `5`                               |
|                                     | `MCP_AGENT_TOOL_TOOL_CALLING_METHOD`           | Method for tool invocation ('auto', 'json_schema', 'function_calling').                                    | `auto`                            |
|                                     | `MCP_AGENT_TOOL_MAX_INPUT_TOKENS`              | Max input tokens for LLM context.                                                                          | `128000`                          |
|                                     | `MCP_AGENT_TOOL_USE_VISION`                    | Enable vision capabilities (screenshot analysis).                                                          | `true`                            |
|                                     | `MCP_AGENT_TOOL_HEADLESS`                      | Override `MCP_BROWSER_HEADLESS` for this tool (true/false/empty).                                          | ` ` (uses general)                |
|                                     | `MCP_AGENT_TOOL_DISABLE_SECURITY`              | Override `MCP_BROWSER_DISABLE_SECURITY` for this tool (true/false/empty).                                  | ` ` (uses general)                |
|                                     | `MCP_AGENT_TOOL_ENABLE_RECORDING`              | Enable Playwright video recording.                                                                         | `false`                           |
|                                     | `MCP_AGENT_TOOL_SAVE_RECORDING_PATH`           | Path to save recordings (Required if `MCP_AGENT_TOOL_ENABLE_RECORDING=true`).                              | -                                 |
|                                     | `MCP_AGENT_TOOL_HISTORY_PATH`                  | Directory to save agent history JSON files.                                                                | `./tmp/agent_history`             |
| **Research Tool (MCP_RESEARCH_TOOL_)** |                                             | Settings for the `run_deep_research` tool.                                                                 |                                   |
|                                     | `MCP_RESEARCH_TOOL_MAX_PARALLEL_BROWSERS`      | Max parallel browser instances for deep research.                                                          | `3`                               |
|                                     | `MCP_RESEARCH_TOOL_SAVE_DIR`                   | Base directory to save research artifacts. Task ID will be appended.                                       | `./tmp/deep_research`             |
| **Paths (MCP_PATHS_)**              |                                                | General path settings.                                                                                     |                                   |
|                                     | `MCP_PATHS_DOWNLOADS`                          | Directory for downloaded files.                                                                            | `./tmp/downloads`                 |
| **Server (MCP_SERVER_)**            |                                                | Server-specific settings.                                                                                  |                                   |
|                                     | `MCP_SERVER_LOG_FILE`                          | Path for the server log file. Empty for stdout.                                                            | `mcp_server_browser_use.log`      |
|                                     | `MCP_SERVER_LOGGING_LEVEL`                     | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).                                           | `INFO`                            |
|                                     | `MCP_SERVER_ANONYMIZED_TELEMETRY`              | Enable/disable anonymized telemetry (`true`/`false`).                                                      | `true`                            |
|                                     | `MCP_SERVER_MCP_CONFIG`                        | Optional: JSON string for MCP client config used by the internal controller.                               | `null`                            |

**Supported LLM Providers (`MCP_LLM_PROVIDER`):**
`openai`, `azure_openai`, `anthropic`, `google`, `mistral`, `ollama`, `deepseek`, `openrouter`, `alibaba`, `moonshot`, `unbound`

*(Refer to `.env.example` for a comprehensive list of all supported environment variables and their specific provider keys/endpoints.)*

## Connecting to Your Own Browser (CDP)

Instead of having the server launch and manage its own browser instance, you can connect it to a Chrome/Chromium browser that you launch and manage yourself.

**Steps:**

1.  **Launch Chrome/Chromium with Remote Debugging Enabled:**
    (Commands for macOS, Linux, Windows as previously listed, e.g., `google-chrome --remote-debugging-port=9222`)

2.  **Configure Environment Variables:**
    Set the following environment variables:
    ```dotenv
    MCP_BROWSER_USE_OWN_BROWSER=true
    MCP_BROWSER_CDP_URL=http://localhost:9222 # Use the same port
    # Optional: MCP_BROWSER_USER_DATA_DIR=/path/to/your/profile
    ```

3.  **Run the MCP Server or CLI:**
    Start the server (`uv run mcp-server-browser-use`) or CLI (`mcp-browser-cli ...`) as usual.

**Important Considerations:**
*   The browser launched with `--remote-debugging-port` must remain open.
*   Settings like `MCP_BROWSER_HEADLESS` and `MCP_BROWSER_KEEP_OPEN` are ignored when `MCP_BROWSER_USE_OWN_BROWSER=true`.

## Development

```bash
# Install dev dependencies and sync project deps
uv sync --dev

# Install playwright browsers
uv run playwright install
# Run MCP server with debugger (Example connecting to own browser via CDP)
# 1. Launch Chrome: google-chrome --remote-debugging-port=9222
# 2. Run inspector command with environment variables:
npx @modelcontextprotocol/inspector@latest \
  -e MCP_LLM_OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  -e MCP_LLM_PROVIDER=openrouter \
  -e MCP_LLM_MODEL_NAME=anthropic/claude-3.7-sonnet \
  -e MCP_BROWSER_USE_OWN_BROWSER=true \
  -e MCP_BROWSER_CDP_URL=http://localhost:9222 \
  uv --directory . run mcp-server-browser-use
# Note: Change timeout in inspector's config panel if needed (default is 10 seconds)

# Run CLI example
# Create a .env file with your settings or use environment variables
uv run mcp-browser-cli run-browser-agent "What is the title of example.com?"
```

## Troubleshooting

-   **Browser Conflicts**: If *not* using CDP (`MCP_BROWSER_USE_OWN_BROWSER=false`), ensure no conflicting Chrome instances are running with the same user data directory if `MCP_BROWSER_USER_DATA_DIR` is specified.
-   **CDP Connection Issues**: If using `MCP_BROWSER_USE_OWN_BROWSER=true`:
    *   Verify Chrome was launched with `--remote-debugging-port`.
    *   Ensure the port in `MCP_BROWSER_CDP_URL` matches.
    *   Check firewalls and ensure the browser is running.
-   **API Errors**: Double-check API keys (`MCP_LLM_<PROVIDER>_API_KEY` or `MCP_LLM_API_KEY`) and endpoints (e.g., `MCP_LLM_AZURE_OPENAI_ENDPOINT` for Azure).
-   **Vision Issues**: Ensure `MCP_AGENT_TOOL_USE_VISION=true` and your LLM supports vision.
-   **Dependency Problems**: Run `uv sync` and `uv run playwright install`.
-   **Logging**: Check the log file (`MCP_SERVER_LOG_FILE`) or console output. Increase `MCP_SERVER_LOGGING_LEVEL` to `DEBUG` for more details. For CLI, use `--log-level DEBUG`.

## License

MIT - See [LICENSE](LICENSE) for details.
