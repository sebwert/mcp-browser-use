import os
import traceback
from typing import Any, Dict, List

import logging

logging.basicConfig(level=logging.INFO)

from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from fastmcp import FastMCP
from mcp.types import Resource, TextContent, Tool
from pydantic import AnyUrl, BaseModel

from mcp_server_browser_use.agent.custom_agent import CustomAgent
from mcp_server_browser_use.browser.custom_browser import CustomBrowser
from mcp_server_browser_use.controller.custom_controller import CustomController
from mcp_server_browser_use.utils import utils
from mcp_server_browser_use.utils.agent_state import AgentState

# Global references for single "running agent" approach
_global_agent = None
_global_browser = None
_global_browser_context = None
_global_agent_state = AgentState()

app = FastMCP(title="browser-automation", version="0.1.0")


async def reset():
    global _global_agent, _global_browser, _global_browser_context, _global_agent_state
    await _global_browser.close()
    _global_agent = None
    _global_browser = None
    _global_browser_context = None
    _global_agent_state = AgentState()


@app.tool("run-browser-agent")
async def run_browser_agent(task: str, add_infos: str = "") -> List[TextContent]:
    """Handle run-browser-agent tool calls."""
    global _global_agent, _global_browser, _global_browser_context, _global_agent_state

    try:
        # Clear any previous agent stop signals
        _global_agent_state.clear_stop()

        # Get environment variables with defaults
        model_provider = os.getenv("MCP_MODEL_PROVIDER", "openai")
        model_name = os.getenv("MCP_MODEL_NAME", "gpt-4o")
        temperature = float(os.getenv("MCP_TEMPERATURE", "0.7"))
        max_steps = int(os.getenv("MCP_MAX_STEPS", "15"))
        use_vision = os.getenv("MCP_USE_VISION", "true").lower() == "true"
        max_actions_per_step = int(os.getenv("MCP_MAX_ACTIONS_PER_STEP", "5"))
        tool_call_in_content = (
            os.getenv("MCP_TOOL_CALL_IN_CONTENT", "true").lower() == "true"
        )

        # Prepare LLM
        llm = utils.get_llm_model(
            provider=model_provider, model_name=model_name, temperature=temperature
        )

        # Browser setup
        persistent_session = (
            os.getenv("CHROME_PERSISTENT_SESSION", "").lower() == "true"
        )
        chrome_path = os.getenv("CHROME_PATH", "") or None
        user_data_dir = os.getenv("CHROME_USER_DATA", None)

        # Create or reuse browser
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

        # Create controller and agent
        controller = CustomController()
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

        # Run agent
        history = await _global_agent.run(max_steps=max_steps)
        final_result = history.final_result() or "No final result. Possibly incomplete."

        await reset()

        return [TextContent(type="text", text=final_result)]

    except Exception as e:
        error_message = f"run-browser-agent error: {str(e)}\n{traceback.format_exc()}"
        await reset()
        return [TextContent(type="text", text=error_message)]
