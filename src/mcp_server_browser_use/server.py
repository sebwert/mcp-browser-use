import asyncio
from typing import Any, Dict, List, Optional
from contextlib import closing
from pydantic import AnyUrl
import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import os

# browser-use imports
from browser_use.browser.browser import BrowserConfig
from browser_use.agent.service import Agent
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from .custom_browser import CustomBrowser
from .agent.custom_agent import CustomAgent

# Environment variables
CHROME_PATH = os.getenv(
    "CHROME_PATH", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)
CHROME_USER_DATA = os.getenv("CHROME_USER_DATA")
CHROME_DEBUGGING_PORT = int(os.getenv("CHROME_DEBUGGING_PORT", "9222"))
CHROME_DEBUGGING_HOST = os.getenv("CHROME_DEBUGGING_HOST", "localhost")
CHROME_PERSISTENT_SESSION = (
    os.getenv("CHROME_PERSISTENT_SESSION", "true").lower() == "true"
)
RESOLUTION_WIDTH = int(os.getenv("RESOLUTION_WIDTH", "1920"))
RESOLUTION_HEIGHT = int(os.getenv("RESOLUTION_HEIGHT", "1080"))
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def safe_log(level: str, data: str) -> None:
    """Safely log messages, catching any exceptions to prevent crashes."""
    try:
        app.request_context.session.send_log_message(level=level, data=data)
    except Exception:
        print(f"Error logging message: {data}")
        pass  # Silently handle any logging failures


PROMPT_TEMPLATE = """
Welcome to the Browser-Use MCP Demo!
This prompt helps illustrate how to launch a browser session, navigate pages, and execute tasks with the help of an LLM.

We provide you with specialized tools to configure an LLM, launch a browser session, manage tasks, validate results, and even enable vision-based interactions.
Feel free to explore these tools by sending a tool call in your conversation.

Let's get started!
"""


class BrowserUseServerState:
    """
    Manages in-memory state for the browser MCP server, including references to
    a launched browser, any agent tasks, and a textual 'history' resource that
    can be read.
    """

    def __init__(self):
        self.browser: Optional[CustomBrowser] = None
        self.history_log: List[str] = []
        self.llm: Optional[ChatOpenAI] = None
        self.vision_enabled: bool = False

    def add_history(self, message: str):
        safe_log("debug", f"Adding to history log: {message}")
        self.history_log.append(message)

    def get_history(self) -> str:
        safe_log(
            "debug", f"Retrieving history log with {len(self.history_log)} entries"
        )
        if not self.history_log:
            return "No actions have been taken yet."
        return "\n".join(self.history_log)


app = Server("browser-use-mcp-server")
state = BrowserUseServerState()


@app.list_resources()
async def list_resources_handler() -> List[types.Resource]:
    """
    Expose a single resource that holds the textual history log.
    """
    safe_log("info", "Handling list_resources request")
    resources = [
        types.Resource(
            uri=AnyUrl("history://actions"),
            name="Browser-Use Action History",
            description="A record of actions performed during the browser session",
            mimeType="text/plain",
        )
    ]
    safe_log("info", f"Returning {len(resources)} resources")
    return resources


@app.read_resource()
async def read_resource_handler(uri: AnyUrl) -> str:
    """
    Return the aggregated browser action log if the user asks for history://actions
    """
    safe_log("info", f"Handling read_resource request for URI: {uri}")
    if str(uri) == "history://actions":
        history = state.get_history()
        safe_log("info", f"Returning history with {len(history)} characters")
        return history
    error_msg = f"Unknown resource URI requested: {uri}"
    safe_log("error", error_msg)
    raise ValueError(error_msg)


@app.list_prompts()
async def list_prompts_handler() -> List[types.Prompt]:
    """
    Provide one demo prompt, mcp-demo, for exploring browser capabilities.
    """
    safe_log("info", "Handling list_prompts request")
    prompts = [
        types.Prompt(
            name="mcp-demo",
            description="A prompt that walks the user through launching a browser and performing tasks",
            arguments=[],
        )
    ]
    safe_log("info", f"Returning {len(prompts)} prompts")
    return prompts


@app.get_prompt()
async def get_prompt_handler(
    name: str, arguments: Dict[str, str]
) -> types.GetPromptResult:
    """
    Return a text prompt. We don't expect arguments for the basic mcp-demo.
    """
    safe_log(
        "info",
        f"Handling get_prompt request for prompt: {name} with arguments: {arguments}",
    )
    if name != "mcp-demo":
        error_msg = f"Unknown prompt requested: {name}"
        safe_log("error", error_msg)
        raise ValueError(error_msg)

    prompt = PROMPT_TEMPLATE.strip()
    safe_log("info", "Returning demo prompt")
    return types.GetPromptResult(
        description="Demo prompt for browser-based tasks",
        messages=[
            types.PromptMessage(
                role="user", content=types.TextContent(type="text", text=prompt)
            )
        ],
    )


@app.list_tools()
async def list_tools_handler() -> List[types.Tool]:
    """
    Provide the set of tools recommended in the reference plan for browser-use.
    """
    return [
        types.Tool(
            name="browser_launch",
            description="Launch or attach to a browser session",
            inputSchema={
                "type": "object",
                "properties": {
                    "headless": {"type": "boolean"},
                    "disableSecurity": {"type": "boolean"},
                    "windowSize": {
                        "type": "object",
                        "properties": {
                            "width": {"type": "number"},
                            "height": {"type": "number"},
                        },
                    },
                    "chromePath": {"type": "string"},
                    "persistSession": {"type": "boolean"},
                    "loadTimeouts": {
                        "type": "object",
                        "properties": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                        },
                    },
                },
            },
        ),
        types.Tool(
            name="task_execute",
            description="Execute a series of steps in the browser with optional LLM guidance",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "validation": {"type": "boolean"},
                    "maxSteps": {"type": "number"},
                    "visionEnabled": {"type": "boolean"},
                    "llmConfig": {
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string"},
                            "model": {"type": "string"},
                            "apiKey": {"type": "string"},
                            "baseUrl": {"type": "string"},
                            "apiVersion": {"type": "string"},
                        },
                    },
                },
            },
        ),
        types.Tool(
            name="session_manage",
            description="Manage browser sessions (e.g., persist or record history)",
            inputSchema={
                "type": "object",
                "properties": {
                    "persist": {"type": "boolean"},
                    "recordHistory": {"type": "boolean"},
                    "exportFormat": {"type": "string"},
                    "saveTrace": {"type": "boolean"},
                },
            },
        ),
        types.Tool(
            name="llm_configure",
            description="Configure the LLM used for guiding the browser task execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {"type": "string"},
                    "model": {"type": "string"},
                    "apiKey": {"type": "string"},
                    "baseUrl": {"type": "string"},
                    "apiVersion": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="history_export",
            description="Export the in-memory action history to JSON or GIF (stubbed).",
            inputSchema={
                "type": "object",
                "properties": {"format": {"type": "string", "enum": ["json", "gif"]}},
            },
        ),
        types.Tool(
            name="task_validate",
            description="Validate the results of a previously executed task (stubbed).",
            inputSchema={
                "type": "object",
                "properties": {"resultData": {"type": "string"}},
            },
        ),
        types.Tool(
            name="vision_toggle",
            description="Toggle the vision capabilities in the server state",
            inputSchema={
                "type": "object",
                "properties": {"enable": {"type": "boolean"}},
            },
        ),
    ]


@app.call_tool()
async def call_tool_handler(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """
    Integrate with the 'browser-use' library. Each tool name corresponds to a
    different chunk of logic. We'll maintain a single global Browser and an optional LLM.
    """
    safe_log("info", f"Handling tool call: {name} with arguments: {arguments}")
    try:
        if name == "browser_launch":
            safe_log("info", "Launching browser with configuration")
            headless = arguments.get("headless", False)
            disable_security = arguments.get("disableSecurity", False)
            window_size = arguments.get(
                "windowSize", {"width": RESOLUTION_WIDTH, "height": RESOLUTION_HEIGHT}
            )
            chrome_path = arguments.get("chromePath", CHROME_PATH)
            persist_session = arguments.get("persistSession", CHROME_PERSISTENT_SESSION)
            load_timeouts = arguments.get("loadTimeouts", {"min": 1, "max": 10})

            safe_log(
                "debug",
                f"Browser config: headless={headless}, disable_security={disable_security}, "
                f"window_size={window_size}, chrome_path={chrome_path}, "
                f"persist_session={persist_session}, load_timeouts={load_timeouts}",
            )

            state.browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    chrome_instance_path=chrome_path if chrome_path else None,
                    disable_security=disable_security,
                    extra_chromium_args=[],
                    proxy=None,
                )
            )
            msg = "Browser launched/attached successfully"
            safe_log("info", msg)
            state.add_history(msg)
            return [types.TextContent(type="text", text=msg)]

        elif name == "task_execute":
            safe_log("info", "Executing browser task")
            description = arguments.get("description", "")
            steps = arguments.get("steps", [])
            validation = arguments.get("validation", False)
            max_steps = arguments.get("maxSteps", 20)
            vision_enabled = arguments.get("visionEnabled", False)
            llm_config = arguments.get("llmConfig", {})

            safe_log(
                "debug",
                f"Task config: description='{description}', steps={steps}, "
                f"validation={validation}, max_steps={max_steps}, "
                f"vision_enabled={vision_enabled}, llm_config={llm_config}",
            )

            if llm_config:
                safe_log("info", "Configuring LLM for task execution")
                provider = llm_config.get("provider", "openai")
                model = llm_config.get("model", "gpt-4o")
                api_key = llm_config.get("apiKey", "")
                base_url = llm_config.get("baseUrl", "")
                api_version = llm_config.get("apiVersion", "")

                state.llm = ChatOpenAI(
                    api_key=SecretStr(api_key),
                    base_url=base_url,
                    model=model,
                    api_version=api_version,
                )
                safe_log(
                    "info", f"LLM configured with provider={provider}, model={model}"
                )

            if not state.browser:
                error_msg = (
                    "No browser session found. Launch one with browser_launch first."
                )
                safe_log("error", error_msg)
                raise ValueError(error_msg)

            agent = CustomAgent(
                task=f"{description}\n\nSteps:\n"
                + "\n".join(f"- {step}" for step in steps),
                browser=state.browser,
                llm=state.llm,
                validate_output=validation,
                use_vision=vision_enabled,
            )

            safe_log("info", f"Starting task execution with max_steps={max_steps}")
            result = await agent.run(max_steps=max_steps)
            safe_log("info", "Task execution completed")

            state.add_history(
                f"Task executed: {description}\nSteps: {steps}\nResult: {result}"
            )
            return [types.TextContent(type="text", text=str(result))]

        elif name == "session_manage":
            safe_log("info", "Managing browser session")
            persist = arguments.get("persist", False)
            record_history = arguments.get("recordHistory", False)
            export_format = arguments.get("exportFormat", None)
            save_trace = arguments.get("saveTrace", False)

            safe_log(
                "debug",
                f"Session config: persist={persist}, record_history={record_history}, "
                f"export_format={export_format}, save_trace={save_trace}",
            )

            msg = (
                f"Session manage request => persist={persist}, record={record_history}, "
                f"exportFormat={export_format}, saveTrace={save_trace}"
            )
            state.add_history(msg)
            return [types.TextContent(type="text", text=msg)]

        elif name == "llm_configure":
            safe_log("info", "Configuring LLM")
            provider = arguments.get("provider", "openai")
            model = arguments.get("model", "gpt-3.5-turbo")
            api_key = arguments.get("apiKey", OPENAI_API_KEY)
            base_url = arguments.get("baseUrl", OPENAI_ENDPOINT)
            api_version = arguments.get("apiVersion", "")

            safe_log(
                "debug",
                f"LLM config: provider={provider}, model={model}, "
                f"base_url={base_url}, api_version={api_version}",
            )

            state.llm = ChatOpenAI(
                api_key=SecretStr(api_key),
                base_url=base_url,
                model=model,
                api_version=api_version,
            )
            msg = f"LLM configured: provider={provider}, model={model}"
            safe_log("info", msg)
            state.add_history(msg)
            return [types.TextContent(type="text", text=msg)]

        elif name == "history_export":
            safe_log("info", "Exporting history")
            fmt = arguments.get("format", "json")
            msg = f"History export requested in {fmt} format. (Stubbed implementation.)"
            safe_log("info", msg)
            state.add_history(msg)
            return [types.TextContent(type="text", text=msg)]

        elif name == "task_validate":
            safe_log("info", "Validating task")
            result_data = arguments.get("resultData", "")
            msg = f"Task validation requested. Checking: {result_data}"
            safe_log("info", msg)
            state.add_history(msg)
            return [types.TextContent(type="text", text=f"Validated: {result_data}")]

        elif name == "vision_toggle":
            safe_log("info", "Toggling vision capabilities")
            enable = arguments.get("enable", False)
            state.vision_enabled = enable
            msg = f"Vision toggled to: {enable}"
            safe_log("info", msg)
            state.add_history(msg)
            return [types.TextContent(type="text", text=msg)]

        else:
            error_msg = f"Unknown tool name: {name}"
            safe_log("error", error_msg)
            raise ValueError(error_msg)

    except Exception as e:
        error_msg = f"Error in call_tool: {str(e)}"
        safe_log("error", error_msg)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def run_server_stdio():
    """
    Run the server using stdio transport. This can be used for local debugging or
    integration with CLI-based MCP clients.
    """
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="browser-use-mcp",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
