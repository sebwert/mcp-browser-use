# browser-use MCP server

[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)

AI-driven browser automation server implementing the Model Context Protocol (MCP) for natural language browser control and web research.

## Features

-   🧠 **MCP Integration** - Full protocol implementation for AI agent communication.
-   🌐 **Browser Automation** - Page navigation, form filling, element interaction via natural language.
-   👁️ **Visual Understanding** - Optional screenshot analysis for vision-capable LLMs.
-   🔄 **State Persistence** - Manages a browser session across multiple MCP calls.
-   🔌 **Multi-LLM Support** - Integrates with OpenAI, Anthropic, Azure, DeepSeek, Google, Mistral, Ollama, OpenRouter, Alibaba, Moonshot, Unbound AI.
-   🔍 **Deep Research Tool** - Dedicated tool for multi-step web research and report generation.
-   ⚙️ **Environment Variable Configuration** - Fully configurable via environment variables.

## Quick Start

### Prerequisites

-   Python 3.11 or higher
-   `uv` (fast Python package installer): `pip install uv`
-   Chrome/Chromium browser installed
-   Install Playwright browsers: `uv run playwright install`

### Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/mcp-browser-use.git # Replace with actual repo URL
    cd mcp-browser-use
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    ```

3.  **Configure Environment Variables:**
    *   Copy the example environment file: `cp .env.example .env`
    *   Edit the `.env` file and add your API keys and desired settings (see [Configuration](#configuration-environment-variables) section below).

4.  **Run the server:**
    ```bash
    uv run mcp-server-browser-use
    ```
    The server will start and listen for MCP connections.

### Integration with MCP Clients (e.g., Claude Desktop)

You can configure clients like Claude Desktop to connect to this server. Add the following structure to the client's configuration (e.g., `claude_desktop_config.json`), adjusting the path and environment variables as needed:

```json
// Example for Claude Desktop config
"mcpServers": {
    "browser-use": {
      // Option 1: Run installed package
      // "command": "uvx",
      // "args": ["mcp-server-browser-use"],

      // Option 2: Run from local development source
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/mcp-browser-use", // <--- CHANGE THIS PATH
        "mcp-server-browser-use"
      ],
      "env": {
        // --- CRITICAL: Add required API keys here ---
        "OPENAI_API_KEY": "YOUR_KEY_HERE_IF_USING_OPENAI",
        "ANTHROPIC_API_KEY": "YOUR_KEY_HERE_IF_USING_ANTHROPIC",
        // ... add other keys based on MCP_MODEL_PROVIDER ...

        // --- Optional Overrides (defaults are usually fine) ---
        "MCP_MODEL_PROVIDER": "openai", // Change provider if needed
        "MCP_MODEL_NAME": "gpt-4o",     // Change model if needed
        "BROWSER_HEADLESS": "false",    // Set to true to hide browser window
        "BROWSER_USE_LOGGING_LEVEL": "INFO",

        // Ensure Python uses UTF-8
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
        "PYTHONUTF8": "1"
      }
    }
}
```

**Important:** Ensure the `command` and `args` correctly point to how you want to run the server (either the installed package or from the source directory). Set the necessary API keys in the `env` section.

## MCP Tools

This server exposes the following tools via the Model Context Protocol:

### Synchronous Tools (Wait for Completion)

1.  **`run_browser_agent`**
    *   **Description:** Executes a browser automation task based on natural language instructions and waits for it to complete.
    *   **Arguments:**
        *   `task` (string, required): The primary task or objective.
        *   `add_infos` (string, optional): Additional context or hints for the agent.
    *   **Returns:** (string) The final result extracted by the agent or an error message.

2.  **`run_deep_research`**
    *   **Description:** Performs in-depth web research on a topic, generates a report, and waits for completion.
    *   **Arguments:**
        *   `research_task` (string, required): The topic or question for the research.
        *   `max_search_iterations` (integer, optional, default: 10): Max search cycles.
        *   `max_query_per_iteration` (integer, optional, default: 3): Max search queries per cycle.
    *   **Returns:** (string) The generated research report in Markdown format or an error message.

## Configuration (Environment Variables)

Configure the server using environment variables. You can set these in your system or place them in a `.env` file in the project root.

| Variable                        | Description                                                                 | Required? | Default Value                     | Example Value                     |
| :------------------------------ | :-------------------------------------------------------------------------- | :-------- | :-------------------------------- | :-------------------------------- |
| **LLM Settings**                |                                                                             |           |                                   |                                   |
| `MCP_MODEL_PROVIDER`            | LLM provider to use. See options below.                                     | **Yes**   | `openai`                          | `anthropic`                       |
| `MCP_MODEL_NAME`                | Specific model name for the chosen provider.                                | No        | Provider-specific (e.g., `gpt-4o`) | `claude-3-5-sonnet-20240620`      |
| `MCP_TEMPERATURE`               | LLM temperature (0.0-2.0). Controls randomness.                             | No        | `0.3`                             | `0.7`                             |
| `MCP_TOOL_CALLING_METHOD`       | Method for tool invocation ('auto', 'json_schema', 'function_calling').     | No        | `auto`                            | `json_schema`                     |
| **Provider API Keys**           | **Required based on `MCP_MODEL_PROVIDER`**                                  |           |                                   |                                   |
| `OPENAI_API_KEY`                | API Key for OpenAI.                                                         | If Used   | -                                 | `sk-...`                          |
| `ANTHROPIC_API_KEY`             | API Key for Anthropic.                                                      | If Used   | -                                 | `sk-ant-...`                      |
| `GOOGLE_API_KEY`                | API Key for Google AI (Gemini).                                             | If Used   | -                                 | `AIza...`                         |
| `AZURE_OPENAI_API_KEY`          | API Key for Azure OpenAI.                                                   | If Used   | -                                 | `...`                             |
| `DEEPSEEK_API_KEY`              | API Key for DeepSeek.                                                       | If Used   | -                                 | `sk-...`                          |
| `MISTRAL_API_KEY`               | API Key for Mistral AI.                                                     | If Used   | -                                 | `...`                             |
| `OPENROUTER_API_KEY`            | API Key for OpenRouter.                                                     | If Used   | -                                 | `sk-or-...`                       |
| `ALIBABA_API_KEY`               | API Key for Alibaba Cloud (DashScope).                                      | If Used   | -                                 | `sk-...`                          |
| `MOONSHOT_API_KEY`              | API Key for Moonshot AI.                                                    | If Used   | -                                 | `sk-...`                          |
| `UNBOUND_API_KEY`               | API Key for Unbound AI.                                                     | If Used   | -                                 | `...`                             |
| **Provider Endpoints**          | Optional: Override default API endpoints.                                   |           |                                   |                                   |
| `OPENAI_ENDPOINT`               | OpenAI API endpoint URL.                                                    | No        | `https://api.openai.com/v1`       |                                   |
| `ANTHROPIC_ENDPOINT`            | Anthropic API endpoint URL.                                                 | No        | `https://api.anthropic.com`       |                                   |
| `AZURE_OPENAI_ENDPOINT`         | **Required if using Azure.** Your Azure resource endpoint.                  | If Used   | -                                 | `https://res.openai.azure.com/` |
| `AZURE_OPENAI_API_VERSION`      | Azure API version.                                                          | No        | `2024-05-01-preview`              | `2023-12-01-preview`              |
| `DEEPSEEK_ENDPOINT`             | DeepSeek API endpoint URL.                                                  | No        | `https://api.deepseek.com`        |                                   |
| `MISTRAL_ENDPOINT`              | Mistral API endpoint URL.                                                   | No        | `https://api.mistral.ai/v1`       |                                   |
| `OLLAMA_ENDPOINT`               | Ollama API endpoint URL.                                                    | No        | `http://localhost:11434`          | `http://ollama.local:11434`       |
| `OPENROUTER_ENDPOINT`           | OpenRouter API endpoint URL.                                                | No        | `https://openrouter.ai/api/v1`    |                                   |
| `ALIBABA_ENDPOINT`              | Alibaba (DashScope) API endpoint URL.                                       | No        | `https://dashscope...v1`          |                                   |
| `MOONSHOT_ENDPOINT`             | Moonshot API endpoint URL.                                                  | No        | `https://api.moonshot.cn/v1`      |                                   |
| `UNBOUND_ENDPOINT`              | Unbound AI API endpoint URL.                                                | No        | `https://api.getunbound.ai`       |                                   |
| **Ollama Specific**             |                                                                             |           |                                   |                                   |
| `OLLAMA_NUM_CTX`                | Context window size for Ollama models.                                      | No        | `32000`                           | `8192`                            |
| `OLLAMA_NUM_PREDICT`            | Max tokens to predict for Ollama models.                                    | No        | `1024`                            | `2048`                            |
| **Agent Settings**              |                                                                             |           |                                   |                                   |
| `MCP_MAX_STEPS`                 | Max steps per agent run.                                                    | No        | `100`                             | `50`                              |
| `MCP_USE_VISION`                | Enable vision capabilities (screenshot analysis).                           | No        | `true`                            | `false`                           |
| `MCP_MAX_ACTIONS_PER_STEP`      | Max actions per agent step.                                                 | No        | `5`                               | `10`                              |
| `MCP_MAX_INPUT_TOKENS`          | Max input tokens for LLM context.                                           | No        | `128000`                          | `64000`                           |
| `MCP_GENERATE_GIF`              | Generate GIF recording of agent run (sync only).                            | No        | `false`                           | `true`                            |
| `MCP_AGENT_HISTORY_PATH`        | Directory to save agent history JSON files.                                 | No        | -                                 | `./tmp/agent_history`             |
| **Deep Research Settings**      |                                                                             |           |                                   |                                   |
| `MCP_RESEARCH_MAX_ITERATIONS`   | Max search iterations for deep research.                                    | No        | `10`                              | `5`                               |
| `MCP_RESEARCH_MAX_QUERY`        | Max search queries per iteration.                                           | No        | `3`                               | `5`                               |
| `MCP_RESEARCH_USE_OWN_BROWSER`  | Use a separate browser instance for research.                               | No        | `false`                           | `true`                            |
| `MCP_RESEARCH_SAVE_DIR`         | Directory to save research artifacts (report, results).                     | No        | `./tmp/deep_research/{task_id}`   | `./research_output`               |
| `MCP_RESEARCH_AGENT_MAX_STEPS`  | Max steps for sub-agents within deep research.                              | No        | `10`                              | `15`                              |
| **Browser Settings**            |                                                                             |           |                                   |                                   |
| `BROWSER_HEADLESS`              | Run browser without visible UI.                                             | No        | `false`                           | `true`                            |
| `BROWSER_DISABLE_SECURITY`      | Disable browser security features (use cautiously).                         | No        | `false`                           | `true`                            |
| `CHROME_PATH`                   | Path to Chrome/Chromium executable.                                         | No        | -                                 | `/usr/bin/chromium-browser`       |
| `CHROME_USER_DATA`              | Path to Chrome user data directory (for persistent sessions).               | No        | -                                 | `~/.config/google-chrome/Profile 1` |
| `CHROME_CDP`                    | Connect to existing Chrome via DevTools Protocol URL.                       | No        | -                                 | `http://localhost:9222`           |
| `BROWSER_TRACE_PATH`            | Directory to save Playwright trace files.                                   | No        | -                                 | `./tmp/traces`                    |
| `BROWSER_RECORDING_PATH`        | Directory to save Playwright recording files (videos).                      | No        | -                                 | `./tmp/recordings`                |
| `BROWSER_WINDOW_WIDTH`          | Browser window width (pixels).                                              | No        | `1280`                            | `1920`                            |
| `BROWSER_WINDOW_HEIGHT`         | Browser window height (pixels).                                             | No        | `720`                             | `1080`                            |
| **Server & Logging**            |                                                                             |           |                                   |                                   |
| `BROWSER_USE_LOGGING_LEVEL`     | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).            | No        | `INFO`                            | `DEBUG`                           |
| `ANONYMIZED_TELEMETRY`          | Enable/disable anonymized telemetry (`true`/`false`).                       | No        | `true`                            | `false`                           |

**Supported LLM Providers (`MCP_MODEL_PROVIDER`):**

`openai`, `azure_openai`, `anthropic`, `google`, `mistral`, `ollama`, `deepseek`, `openrouter`, `alibaba`, `moonshot`, `unbound`

## Development

```bash
# Install dev dependencies and sync project deps
uv sync --dev

# Install playwright browsers
uv run playwright install

# Run type checking
uv run pyright

# Run linting/formatting checks
uv run ruff check .
uv run ruff format .

# Run with debugger
# Don't forget to change timeout in inspector's config panel, default is 10 seconds
npx @modelcontextprotocol/inspector@latest -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY -e MCP_MODEL_PROVIDER=anthropic -e MCP_MODEL_NAME=claude-3-7-sonnet-20250219  uv --directory . run mcp run src/mcp_server_browser_use/server.py
```

## Troubleshooting

-   **Browser Conflicts**: If using a managed browser (`CHROME_CDP` not set), ensure no other conflicting Chrome instances are running with the same user data directory if specified.
-   **API Errors**: Double-check that the correct API key environment variable is set for your chosen `MCP_MODEL_PROVIDER`. Verify keys and endpoints.
-   **Vision Issues**: Ensure `MCP_USE_VISION=true` if using vision features and that your selected LLM model supports vision.
-   **Dependency Problems**: Run `uv sync` to ensure all dependencies are correctly installed.

## License

MIT - See [LICENSE](LICENSE) for details.
