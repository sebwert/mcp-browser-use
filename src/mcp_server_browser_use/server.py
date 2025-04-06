import asyncio
import logging
import os
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional

from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContextConfig, BrowserContextWindowSize
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from mcp_server_browser_use.agent.custom_agent import CustomAgent
from mcp_server_browser_use.agent.custom_prompts import (
    CustomAgentMessagePrompt,
    CustomSystemPrompt,
)
from mcp_server_browser_use.browser.custom_browser import CustomBrowser
from mcp_server_browser_use.controller.custom_controller import CustomController
from mcp_server_browser_use.utils import utils
from mcp_server_browser_use.utils.agent_state import AgentState

logging.basicConfig(level=logging.ERROR)

# Global references for single "running agent" approach
_global_agent: Optional[CustomAgent] = None
_global_browser: Optional[CustomBrowser] = None
_global_browser_context: Optional[BrowserContextConfig] = None
_global_agent_state = AgentState()


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean value from environment variable."""
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")


class RunBrowserAgentArgs(BaseModel):
    """Arguments for the run_browser_agent tool."""

    task: str = Field(..., description="The primary task or objective for the browser agent.")
    add_infos: str = Field("", description="Additional information or context to provide to the agent.")


def serve() -> FastMCP:
    def mcp_log(level: str, message: str) -> None:
        """
        Send a log message via MCP notification system if possible.

        Args:
            level: Log level string, e.g., 'info', 'debug', 'warning', 'error'
            message: The log message text
        """
        try:
            ctx = server.request_context
            if ctx and ctx.session:
                ctx.session.send_log_message(level=level, data=message)
        except Exception:
            # Fail silently if no context/session or during startup/shutdown
            pass

    async def _safe_cleanup():
        """Safely clean up browser resources"""
        global _global_browser, _global_agent_state, _global_browser_context, _global_agent
        mcp_log("info", "Starting browser cleanup...")
        try:
            if _global_agent_state:
                try:
                    mcp_log("debug", "Requesting agent stop...")
                    await _global_agent_state.request_stop()
                    mcp_log("debug", "Agent stop requested.")
                except Exception as e:
                    mcp_log("error", f"Error requesting agent stop: {e}")

            if _global_browser_context:
                try:
                    mcp_log("debug", "Closing browser context...")
                    await _global_browser_context.close()
                    mcp_log("debug", "Browser context closed.")
                except Exception as e:
                    mcp_log("error", f"Error closing browser context: {e}")

            if _global_browser:
                try:
                    mcp_log("debug", "Closing browser...")
                    await _global_browser.close()
                    mcp_log("debug", "Browser closed.")
                except Exception as e:
                    mcp_log("error", f"Error closing browser: {e}")

        except Exception as e:
            mcp_log("error", f"Error during cleanup: {e}")
        finally:
            mcp_log("info", "Resetting global browser variables.")
            _global_browser = None
            _global_browser_context = None
            _global_agent_state = AgentState()
            _global_agent = None
            mcp_log("info", "Browser cleanup finished.")

    @asynccontextmanager
    async def server_lifespan(server_instance: Server) -> AsyncIterator[None]:
        """Manage the browser lifecycle tied to the server's lifespan."""
        global _global_browser, _global_browser_context
        # Cannot use mcp_log here, no request context during lifespan startup
        try:
            headless = get_env_bool("BROWSER_HEADLESS", True)
            disable_security = get_env_bool("BROWSER_DISABLE_SECURITY", False)
            chrome_instance_path = os.getenv("BROWSER_CHROME_INSTANCE_PATH", None)
            window_w = int(os.getenv("BROWSER_WINDOW_WIDTH", "1280"))
            window_h = int(os.getenv("BROWSER_WINDOW_HEIGHT", "720"))
            extra_chromium_args = [f"--window-size={window_w},{window_h}"]

            _global_browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=disable_security,
                    chrome_instance_path=chrome_instance_path,
                    extra_chromium_args=extra_chromium_args,
                )
            )

            _global_browser_context = await _global_browser.new_context(
                config=BrowserContextConfig(
                    trace_path=os.getenv("BROWSER_TRACE_PATH"),
                    save_recording_path=os.getenv("BROWSER_RECORDING_PATH"),
                    no_viewport=False,
                    browser_window_size=BrowserContextWindowSize(width=window_w, height=window_h),
                )
            )

            yield

        except Exception:
            # Cannot use mcp_log here
            await _safe_cleanup()
            raise
        finally:
            # Cannot use mcp_log here
            await _safe_cleanup()

    server = FastMCP("mcp_server_browser_use", lifespan=server_lifespan)

    @server.tool()
    async def run_browser_agent(task: str, add_infos: str = "") -> str:
        """Core logic for running the browser agent task."""
        global _global_agent, _global_browser, _global_browser_context, _global_agent_state

        if not _global_browser or not _global_browser_context:
            mcp_log("error", "Browser or context not initialized. Cannot execute task.")
            return "Error: Browser environment not properly initialized."

        try:
            _global_agent_state.clear_stop()
            mcp_log("info", f"Starting browser task: {task}")

            model_provider = os.getenv("MCP_MODEL_PROVIDER", "anthropic")
            model_name = os.getenv("MCP_MODEL_NAME", "claude-3-5-sonnet-20241022")
            temperature = float(os.getenv("MCP_TEMPERATURE", "0.7"))
            max_steps = int(os.getenv("MCP_MAX_STEPS", "100"))
            use_vision = get_env_bool("MCP_USE_VISION", True)
            max_actions_per_step = int(os.getenv("MCP_MAX_ACTIONS_PER_STEP", "5"))
            tool_calling_method = os.getenv("MCP_TOOL_CALLING_METHOD", "auto")

            llm = utils.get_llm_model(provider=model_provider, model_name=model_name, temperature=temperature)
            mcp_log(
                "debug",
                f"LLM configured: provider={model_provider}, model={model_name}",
            )

            controller = CustomController()
            _global_agent = CustomAgent(
                task=task,
                add_infos=add_infos,
                use_vision=use_vision,
                llm=llm,
                browser=_global_browser,
                browser_context=_global_browser_context,
                controller=controller,
                system_prompt_class=CustomSystemPrompt,
                agent_prompt_class=CustomAgentMessagePrompt,
                max_actions_per_step=max_actions_per_step,
                agent_state=_global_agent_state,
                tool_calling_method=tool_calling_method,
            )
            mcp_log("debug", "CustomAgent initialized.")

            try:
                mcp_log(
                    "info",
                    f"Running agent for task '{task}' with max_steps={max_steps}",
                )
                history = await _global_agent.run(max_steps=max_steps)
                final_result = history.final_result() or f"No final result. Possibly incomplete. History: {history}"
                mcp_log(
                    "info",
                    f"Agent finished task '{task}'. Final result length: {len(final_result)}",
                )
                return final_result
            except asyncio.CancelledError:
                mcp_log("warning", f"Task '{task}' was cancelled.")
                return "Task was cancelled"
            except Exception as e:
                mcp_log(
                    "error",
                    f"Agent run error for task '{task}': {str(e)}\n{traceback.format_exc()}",
                )
                return f"Error during task execution: {str(e)}"

        except Exception as e:
            mcp_log(
                "error",
                f"Error setting up browser agent task '{task}': {str(e)}\n{traceback.format_exc()}",
            )
            return f"Error setting up task execution: {str(e)}"

    return server


server = serve()


def main():
    server.run()


if __name__ == "__main__":
    main()
