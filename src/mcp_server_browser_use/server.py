import asyncio
import os
import sys
import traceback
from typing import List

import logging

logging.basicConfig(level=logging.INFO)

from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from fastmcp import FastMCP
from mcp.types import TextContent

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

app = FastMCP("mcp_server_browser_use")


async def _safe_cleanup():
    """Safely clean up browser resources"""
    global _global_browser, _global_agent_state, _global_browser_context, _global_agent

    try:
        if _global_agent_state:
            try:
                await _global_agent_state.request_stop()
            except Exception:
                pass

        if _global_browser_context:
            try:
                await _global_browser_context.close()
            except Exception:
                pass

        if _global_browser:
            try:
                await _global_browser.close()
            except Exception:
                pass

    except Exception as e:
        # Log the error, but don't re-raise
        print(f"Error during cleanup: {e}", file=sys.stderr)
    finally:
        # Reset global variables
        _global_browser = None
        _global_browser_context = None
        _global_agent_state = None
        _global_agent = AgentState()


@app.tool()
async def run_browser_agent(task: str, add_infos: str = "") -> str:
    """Handle run-browser-agent tool calls."""
    global _global_agent, _global_browser, _global_browser_context, _global_agent_state

    try:
        # Clear any previous agent stop signals
        _global_agent_state.clear_stop()

        # Get environment variables with defaults
        model_provider = os.getenv("MCP_MODEL_PROVIDER", "openai")
        model_name = os.getenv("MCP_MODEL_NAME", "gpt-4o")
        temperature = float(os.getenv("MCP_TEMPERATURE", "0.7"))
        max_steps = int(os.getenv("MCP_MAX_STEPS", "100"))
        use_vision = os.getenv("MCP_USE_VISION", "true").lower() == "true"
        max_actions_per_step = int(os.getenv("MCP_MAX_ACTIONS_PER_STEP", "5"))
        tool_call_in_content = (
            os.getenv("MCP_TOOL_CALL_IN_CONTENT", "true").lower() == "true"
        )

        # Prepare LLM
        llm = utils.get_llm_model(
            provider=model_provider, model_name=model_name, temperature=temperature
        )

        chrome_path = os.getenv("CHROME_PATH", "") or None

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
        final_result = (
            history.final_result() or f"No final result. Possibly incomplete. {history}"
        )

        return final_result

    except Exception as e:
        raise ValueError(f"run-browser-agent error: {str(e)}\n{traceback.format_exc()}")

    finally:
        await _safe_cleanup()


def main():
    try:
        app.run()
    except Exception as e:
        print(
            f"Error running MCP server: {e}\n{traceback.format_exc()}", file=sys.stderr
        )
    finally:
        # Use a separate event loop to ensure cleanup
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_safe_cleanup())
            loop.close()
        except Exception as cleanup_error:
            print(f"Cleanup error: {cleanup_error}", file=sys.stderr)


if __name__ == "__main__":
    main()
