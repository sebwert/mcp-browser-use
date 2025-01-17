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
from browser_use.browser.context import BrowserContextConfig, BrowserContextWindowSize
from browser_use.agent.service import Agent
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from .custom_browser import CustomBrowser
from .agent.custom_agent import CustomAgent

# Environment variables with defaults
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
SAVE_TRACES_PATH = os.getenv("SAVE_TRACES_PATH", "./tmp/traces")
SAVE_RECORDINGS_PATH = os.getenv("SAVE_RECORDINGS_PATH", "./tmp/record_videos")
DEFAULT_MAX_STEPS = int(os.getenv("DEFAULT_MAX_STEPS", "20"))
DEFAULT_ACTIONS_PER_STEP = int(os.getenv("DEFAULT_ACTIONS_PER_STEP", "5"))

def safe_log(level: str, data: str) -> None:
    """Safely log messages, catching any exceptions to prevent crashes."""
    try:
        app.request_context.session.send_log_message(level=level, data=data)
    except Exception:
        print(f"Error logging message: {data}")
        pass

class BrowserUseServerState:
    """Manages server state including browser, context, and history."""
    def __init__(self):
        self.browser: Optional[CustomBrowser] = None
        self.browser_context: Optional[Any] = None
        self.llm: Optional[ChatOpenAI] = None
        self.history: List[Dict[str, Any]] = []
        self.recording_enabled: bool = False
        self.tracing_enabled: bool = False
        self.vision_enabled: bool = False

    def add_history_entry(self, entry_type: str, details: Dict[str, Any]) -> None:
        """Add a timestamped entry to history."""
        entry = {
            "timestamp": asyncio.get_event_loop().time(),
            "type": entry_type,
            **details,
        }
        self.history.append(entry)
        safe_log("debug", f"Added history entry: {entry}")

    async def cleanup(self) -> None:
        """Cleanup resources when shutting down."""
        if self.browser_context:
            await self.browser_context.close()
            self.browser_context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        self.llm = None

    async def setup_browser_context(self) -> None:
        """Setup or refresh browser context with current settings."""
        if self.browser_context:
            await self.browser_context.close()

        if not self.browser:
            return

        self.browser_context = await self.browser.new_context(
            config=BrowserContextConfig(
                trace_path=SAVE_TRACES_PATH if self.tracing_enabled else None,
                save_recording_path=(
                    SAVE_RECORDINGS_PATH if self.recording_enabled else None
                ),
                no_viewport=False,
                browser_window_size=BrowserContextWindowSize(
                    width=RESOLUTION_WIDTH, height=RESOLUTION_HEIGHT
                ),
            )
        )


app = Server("browser-use-mcp-server")
state = BrowserUseServerState()

@app.list_tools()
async def list_tools_handler() -> List[types.Tool]:
    """Provide the minimal set of required tools."""
    return [
        types.Tool(
            name="browser_launch",
            description="Launch or attach to a browser session",
            inputSchema={
                "type": "object",
                "properties": {
                    "headless": {"type": "boolean"},
                    "disableSecurity": {"type": "boolean"},
                },
            },
        ),
        types.Tool(
            name="task_execute",
            description="Execute a task in the browser with LLM guidance",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "maxSteps": {"type": "number"},
                    "visionEnabled": {"type": "boolean"},
                },
            },
        ),
        types.Tool(
            name="session_manage",
            description="Configure recording and tracing for the session",
            inputSchema={
                "type": "object",
                "properties": {
                    "enableRecording": {"type": "boolean"},
                    "enableTracing": {"type": "boolean"},
                },
            },
        ),
    ]

@app.call_tool()
async def call_tool_handler(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool calls with proper state management."""
    safe_log("info", f"Handling tool call: {name} with arguments: {arguments}")
    try:
        if name == "browser_launch":
            headless = arguments.get("headless", False)
            disable_security = arguments.get("disableSecurity", False)

            # Cleanup existing browser if any
            await state.cleanup()

            state.browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    chrome_instance_path=CHROME_PATH,
                    disable_security=disable_security,
                    extra_chromium_args=[
                        f"--window-size={RESOLUTION_WIDTH},{RESOLUTION_HEIGHT}"
                    ],
                )
            )

            await state.setup_browser_context()

            msg = "Browser launched successfully"
            state.add_history_entry(
                "browser_launch",
                {"headless": headless, "disable_security": disable_security},
            )
            return [types.TextContent(type="text", text=msg)]

        elif name == "task_execute":
            if not state.browser or not state.browser_context:
                raise ValueError("Browser not initialized. Call browser_launch first.")

            description = arguments.get("description", "")
            max_steps = arguments.get("maxSteps", DEFAULT_MAX_STEPS)
            vision_enabled = arguments.get("visionEnabled", False)

            # Initialize LLM if not already done
            if not state.llm:
                state.llm = ChatOpenAI(
                    api_key=SecretStr(OPENAI_API_KEY),
                    base_url=OPENAI_ENDPOINT,
                    model="gpt-4",
                )

            agent = CustomAgent(
                task=description,
                llm=state.llm,
                use_vision=vision_enabled,
                browser=state.browser,
                browser_context=state.browser_context,
                max_actions_per_step=DEFAULT_ACTIONS_PER_STEP,
                tool_call_in_content=True,
            )

            safe_log("info", f"Starting task execution with max_steps={max_steps}")
            result = await agent.run(max_steps=max_steps)

            state.add_history_entry(
                "task_execute",
                {
                    "description": description,
                    "max_steps": max_steps,
                    "vision_enabled": vision_enabled,
                    "result": str(result),
                },
            )

            return [types.TextContent(type="text", text=str(result))]

        elif name == "session_manage":
            enable_recording = arguments.get("enableRecording", False)
            enable_tracing = arguments.get("enableTracing", False)

            state.recording_enabled = enable_recording
            state.tracing_enabled = enable_tracing

            # Refresh browser context with new settings
            if state.browser:
                await state.setup_browser_context()

            state.add_history_entry(
                "session_manage",
                {
                    "recording_enabled": enable_recording,
                    "tracing_enabled": enable_tracing,
                },
            )

            return [
                types.TextContent(
                    type="text",
                    text=f"Session updated: recording={'enabled' if enable_recording else 'disabled'}, "
                    f"tracing={'enabled' if enable_tracing else 'disabled'}",
                )
            ]

        else:
            raise ValueError(f"Unknown tool name: {name}")

    except Exception as e:
        error_msg = f"Error in {name}: {str(e)}"
        safe_log("error", error_msg)
        state.add_history_entry("error", {"tool": name, "error": str(e)})
        return [types.TextContent(type="text", text=error_msg)]

async def run_server_stdio():
    """Run the server using stdio transport."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        try:
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
        finally:
            await state.cleanup()

if __name__ == "__main__":
    asyncio.run(run_server_stdio())
