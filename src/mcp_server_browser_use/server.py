import os
import traceback

import mcp.server.stdio
import mcp.types as types
from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl

# Import the custom agent & relevant code
from .agent.custom_agent import CustomAgent
from .browser.custom_browser import CustomBrowser
from .controller.custom_controller import CustomController
from .utils import utils
from .utils.agent_state import AgentState

# We will maintain global references for a single "running agent" approach
# If you want more concurrency, you'd track sessions in a dictionary or similar.
_global_agent = None
_global_browser = None
_global_browser_context = None
_global_agent_state = AgentState()

# Create the MCP server instance
server = Server("browser-automation")


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    Return an empty list of resources by default.
    (In a more advanced scenario, you could list "browser" as a resource, or
     track each session as a resource.)
    """
    return []


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Not used in this minimal example. If your design includes a resource representation
    for the browser or agent state, you could retrieve it here.
    """
    raise ValueError("No resource reading available in this server.")


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    Not used. In some MCP flows, you might define advanced "prompts" for the agent.
    We'll rely on 'call_tool' for launching tasks.
    """
    return []


@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Not used. We won't implement dynamic prompt composition.
    If needed, you can adapt logic from the existing code.
    """
    raise ValueError("No prompts are defined for this server.")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    We provide two main tools:
    1) run-browser-agent: Start the browser (optionally persistent) and run a single agent "task"
    2) stop-browser-agent: Request the agent to stop & close the browser
    """
    return [
        types.Tool(
            name="run-browser-agent",
            description="Launch or reuse a browser and run a custom agent with a specified task (plus optional info). Returns final result or any error info.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "add_infos": {"type": "string"},
                },
                "required": ["task"],
            },
        ),
        types.Tool(
            name="stop-browser-agent",
            description="Stop the currently running agent and close the browser context if open. Frees resources.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """
    Handle tool calls from an MCP client.
    For run-browser-agent, launch the custom agent with requested config.
    For stop-browser-agent, request the agent to stop and close the browser.
    """
    global _global_agent, _global_browser, _global_browser_context, _global_agent_state

    if name == "run-browser-agent":
        # Extract arguments
        task = arguments.get("task", "")
        add_infos = arguments.get("add_infos", "")
        model_provider = os.getenv("MCP_MODEL_PROVIDER", "openai")
        model_name = os.getenv("MCP_MODEL_NAME", "gpt-4")
        temperature = float(os.getenv("MCP_TEMPERATURE", "0.7"))
        max_steps = int(os.getenv("MCP_MAX_STEPS", "15"))
        use_vision = os.getenv("MCP_USE_VISION", "true").lower() == "true"
        max_actions_per_step = int(os.getenv("MCP_MAX_ACTIONS_PER_STEP", "5"))
        tool_call_in_content = (
            os.getenv("MCP_TOOL_CALL_IN_CONTENT", "true").lower() == "true"
        )

        try:
            # Clear any previous agent stop signals
            _global_agent_state.clear_stop()

            # Prepare LLM
            llm = utils.get_llm_model(
                provider=model_provider, model_name=model_name, temperature=temperature
            )

            # Decide if we want persistent session (from env)
            # or ephemeral. If CHROME_PERSISTENT_SESSION is "true" or "True", keep it
            persistent_session = (
                os.getenv("CHROME_PERSISTENT_SESSION", "").lower() == "true"
            )
            chrome_path = os.getenv("CHROME_PATH", None)
            if chrome_path == "":
                chrome_path = None
            # user data dir from env
            user_data_dir = os.getenv("CHROME_USER_DATA", None)

            # Create the (or reuse) browser
            if not _global_browser:
                _global_browser = CustomBrowser(
                    config=BrowserConfig(
                        headless=False,
                        disable_security=False,
                        chrome_instance_path=chrome_path,
                        extra_chromium_args=[],
                        wss_url=None,
                        proxy=None,
                    )
                )
            if not _global_browser_context:
                _global_browser_context = await _global_browser.new_context(
                    config=BrowserContextConfig(
                        trace_path=None, save_recording_path=None, no_viewport=False
                    )
                )

            # Create a custom controller
            controller = CustomController()

            # Instantiate the custom agent
            _global_agent = CustomAgent(
                task=task,
                add_infos=add_infos,
                use_vision=use_vision,
                llm=llm,
                browser=_global_browser,
                browser_context=_global_browser_context,
                controller=controller,
                max_actions_per_step=max_actions_per_step,
                tool_call_in_content=tool_call_in_content,
                agent_state=_global_agent_state,
            )

            # Run the agent
            history = await _global_agent.run(max_steps=max_steps)

            # Provide final result to the client
            final_result = history.final_result()
            if final_result is None:
                final_result = "No final result. Possibly incomplete."

            return [types.TextContent(type="text", text=final_result)]

        except Exception as e:
            error_message = (
                f"run-browser-agent error: {str(e)}\n{traceback.format_exc()}"
            )
            return [types.TextContent(type="text", text=error_message)]

    elif name == "stop-browser-agent":
        # Stop agent and close browser
        try:
            _global_agent_state.request_stop()
            if _global_browser_context:
                await _global_browser_context.close()
                _global_browser_context = None
            if _global_browser:
                await _global_browser.close()
                _global_browser = None
            _global_agent = None
            return [
                types.TextContent(
                    type="text", text="Agent and browser stopped successfully."
                )
            ]
        except Exception as e:
            error_message = (
                f"stop-browser-agent error: {str(e)}\n{traceback.format_exc()}"
            )
            return [types.TextContent(type="text", text=error_message)]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """
    Main entry point.
    Launches the MCP server on stdin/stdout or whichever streams are provided.
    """
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="browser-automation",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
