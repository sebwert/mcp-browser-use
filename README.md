<img src="./assets/web-ui.png" alt="Browser Use Web UI" width="full"/>

<br/>


# browser-use MCP server
[![Documentation](https://img.shields.io/badge/Documentation-📕-blue)](https://docs.browser-use.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

MCP server for browser-use - a powerful browser automation system that enables AI agents to interact with web browsers through natural language.

## Features

- 🤖 **AI-Driven Browser Control**: Natural language interface for browser automation
- 🔍 **Smart Navigation**: Intelligent webpage analysis and interaction
- 📸 **Visual Understanding**: Vision-based element detection and interaction
- 🔄 **State Management**: Persistent browser sessions and context management
- 🛠️ **Extensible**: Custom browser automation capabilities
- 🤝 **MCP Integration**: Seamless integration with Model Context Protocol

## Components

### Resources

The server implements a browser automation system with:
- Integration with browser-use library for advanced browser control
- Custom browser automation capabilities
- Agent-based interaction system with vision capabilities
- Persistent state management
- Customizable model settings

### Requirements

- Python 3.11 or higher
- uv (fast Python package installer)
- Chrome/Chromium browser

### Quick Start

1. Install the package:
```bash
pip install mcp-server-browser-use
```

2. Set up your environment variables (see Configuration section)

3. Run the server:
```bash
mcp-server-browser-use
```

### Configuration

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
      ],
      "env": {
        "OPENAI_ENDPOINT": "https://api.openai.com/v1",
        "OPENAI_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "GOOGLE_API_KEY": "",
        "AZURE_OPENAI_ENDPOINT": "",
        "AZURE_OPENAI_API_KEY": "",
        "DEEPSEEK_ENDPOINT": "https://api.deepseek.com",
        "DEEPSEEK_API_KEY": "",
        # Set to false to disable anonymized telemetry
        "ANONYMIZED_TELEMETRY": "true",
        # Chrome settings
        "CHROME_PATH": "",
        "CHROME_USER_DATA": "",
        "CHROME_DEBUGGING_PORT": "9222",
        "CHROME_DEBUGGING_HOST": "localhost",
        # Set to true to keep browser open between AI tasks
        "CHROME_PERSISTENT_SESSION": "false",
        # Model settings
        "MCP_MODEL_PROVIDER": "anthropic",
        "MCP_MODEL_NAME": "claude-3-5-sonnet-20241022",
        "MCP_TEMPERATURE": "0.3",
        "MCP_MAX_STEPS": "30",
        "MCP_USE_VISION": "true",
        "MCP_MAX_ACTIONS_PER_STEP": "5",
        "MCP_TOOL_CALL_IN_CONTENT": "true"
    }
}
```
</details>

### Environment Variables

Key environment variables:

```bash
# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Chrome Configuration
CHROME_PATH=/path/to/chrome  # Optional: Path to Chrome executable
CHROME_USER_DATA=/path/to/user/data  # Optional: Chrome user data directory
CHROME_DEBUGGING_PORT=9222  # Default: 9222
CHROME_DEBUGGING_HOST=localhost  # Default: localhost
CHROME_PERSISTENT_SESSION=false  # Keep browser open between tasks

# Model Settings
MCP_MODEL_PROVIDER=anthropic  # Options: anthropic, openai, azure, deepseek
MCP_MODEL_NAME=claude-3-5-sonnet-20241022
MCP_TEMPERATURE=0.3
MCP_MAX_STEPS=30
MCP_USE_VISION=true
MCP_MAX_ACTIONS_PER_STEP=5
```

## Development

### Setup

1. Clone the repository:
```bash
git clone https://github.com/saik0s/mcp-browser-use.git
cd mcp-browser-use
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv sync
```

### Debugging

For debugging, use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/project run mcp-server-browser-use
```

The Inspector will display a URL for the debugging interface.

## Browser Actions

The server supports various browser actions through natural language:

- Navigation: Go to URLs, back/forward, refresh
- Interaction: Click, type, scroll, hover
- Forms: Fill forms, submit, select options
- State: Get page content, take screenshots
- Tabs: Create, close, switch between tabs
- Vision: Find elements by visual appearance
- Cookies & Storage: Manage browser state

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
