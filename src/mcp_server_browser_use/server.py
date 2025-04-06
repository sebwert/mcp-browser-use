import logging
import os
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional, Tuple

from mcp.server import Server
from mcp.server.fastmcp import Context, FastMCP

logging.basicConfig(level=logging.ERROR)

# Configure logging
logger = logging.getLogger("mcp_server_browser_use")


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean value from environment variable."""
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")


# --- Server Setup ---


def serve() -> FastMCP:
    from browser_use import BrowserConfig
    from browser_use.browser.context import (
        BrowserContextConfig,
        BrowserContextWindowSize,
    )
    from langchain_core.language_models.chat_models import BaseChatModel

    from mcp_server_browser_use.agent.custom_agent import CustomAgent
    from mcp_server_browser_use.agent.custom_prompts import (
        CustomAgentMessagePrompt,
        CustomSystemPrompt,
    )

    # Import necessary components directly
    from mcp_server_browser_use.browser.custom_browser import CustomBrowser
    from mcp_server_browser_use.browser.custom_context import CustomBrowserContext
    from mcp_server_browser_use.controller.custom_controller import CustomController
    from mcp_server_browser_use.utils import utils
    from mcp_server_browser_use.utils.agent_state import AgentState
    from mcp_server_browser_use.utils.deep_research import deep_research

    @asynccontextmanager
    async def server_lifespan(server_instance: Server) -> AsyncIterator[Dict[str, Any]]:
        """Manage shared resources like the browser."""
        browser: Optional[CustomBrowser] = None
        browser_context: Optional[CustomBrowserContext] = None

        logger.info("Initializing server resources...")
        try:
            # --- Browser Configuration ---
            headless = get_env_bool("BROWSER_HEADLESS", False)
            disable_security = get_env_bool("BROWSER_DISABLE_SECURITY", False)
            chrome_instance_path = os.getenv("CHROME_PATH")  # Corrected env var name
            window_w = int(os.getenv("BROWSER_WINDOW_WIDTH", "1280"))
            window_h = int(os.getenv("BROWSER_WINDOW_HEIGHT", "720"))
            trace_path = os.getenv("BROWSER_TRACE_PATH")
            recording_path = os.getenv("BROWSER_RECORDING_PATH")
            extra_chromium_args = [f"--window-size={window_w},{window_h}"]
            chrome_user_data = os.getenv("CHROME_USER_DATA")
            if chrome_user_data:
                extra_chromium_args.append(f"--user-data-dir={chrome_user_data}")

            # --- Initialize Browser ---
            if not os.getenv("CHROME_CDP"):
                logger.info(f"Initializing managed browser instance (headless={headless})")
                browser = CustomBrowser(
                    config=BrowserConfig(
                        headless=headless,
                        disable_security=disable_security,
                        chrome_instance_path=chrome_instance_path,
                        extra_chromium_args=extra_chromium_args,
                    )
                )
                logger.debug("CustomBrowser initialized.")

                browser_context = await browser.new_context(
                    config=BrowserContextConfig(
                        trace_path=trace_path,
                        save_recording_path=recording_path,
                        no_viewport=False,
                        browser_window_size=BrowserContextWindowSize(width=window_w, height=window_h),
                    )
                )
                logger.debug("CustomBrowserContext initialized.")
            else:
                logger.info(f"Skipping managed browser initialization, expecting connection via CHROME_CDP={os.getenv('CHROME_CDP')}")

            # Yield the resources - Removed global_agent_state
            yield {"browser": browser, "browser_context": browser_context}

        except Exception as e:
            logger.error(f"Fatal error during server initialization: {e}\n{traceback.format_exc()}")
            # Cleanup attempt before raising
            if browser_context:
                try:
                    await browser_context.close()
                except Exception as bc_close_e:
                    logger.error(f"Error closing context during init failure: {bc_close_e}")
            if browser:
                try:
                    await browser.close()
                except Exception as b_close_e:
                    logger.error(f"Error closing browser during init failure: {b_close_e}")
            raise
        finally:
            # --- Cleanup Logic ---
            logger.info("Starting server resource cleanup...")
            # Close browser context
            if browser_context:
                try:
                    logger.debug("Closing browser context...")
                    await browser_context.close()
                    logger.debug("Browser context closed.")
                except Exception as e:
                    logger.error(f"Error closing browser context during cleanup: {e}")
            # Close browser
            if browser:
                try:
                    logger.debug("Closing browser...")
                    await browser.close()
                    logger.debug("Browser closed.")
                except Exception as e:
                    logger.error(f"Error closing browser during cleanup: {e}")
            logger.info("Server resource cleanup finished.")

    server = FastMCP("mcp_server_browser_use", lifespan=server_lifespan)

    # --- Helper to get LLM ---
    def _get_llm_from_env() -> BaseChatModel:
        """Initializes the LLM based on environment variables."""
        provider = os.getenv("MCP_MODEL_PROVIDER", "openai")
        model_name = os.getenv("MCP_MODEL_NAME")
        temperature = float(os.getenv("MCP_TEMPERATURE", "0.3"))

        # Construct kwargs, filtering out None values before passing
        llm_kwargs = {
            "temperature": temperature,
            "model_name": model_name,  # Pass None if not set, get_llm_model handles defaults
            "api_key": os.getenv(f"{provider.upper()}_API_KEY"),  # Use standard key first
            "base_url": os.getenv(f"{provider.upper()}_ENDPOINT"),  # Use standard endpoint first
            "num_ctx": (int(os.getenv("OLLAMA_NUM_CTX", "32000")) if provider == "ollama" else None),
            "num_predict": (int(os.getenv("OLLAMA_NUM_PREDICT", "1024")) if provider == "ollama" else None),
            "api_version": (os.getenv("AZURE_OPENAI_API_VERSION") if provider == "azure_openai" else None),
        }
        # Override with specific MCP vars if they exist
        if os.getenv(f"{provider.upper()}_API_KEY_OVERRIDE"):
            llm_kwargs["api_key"] = os.getenv(f"{provider.upper()}_API_KEY_OVERRIDE")
        if os.getenv(f"{provider.upper()}_ENDPOINT_OVERRIDE"):
            llm_kwargs["base_url"] = os.getenv(f"{provider.upper()}_ENDPOINT_OVERRIDE")
        if provider == "azure_openai" and os.getenv("AZURE_OPENAI_API_VERSION_OVERRIDE"):
            llm_kwargs["api_version"] = os.getenv("AZURE_OPENAI_API_VERSION_OVERRIDE")

        llm_kwargs_filtered = {k: v for k, v in llm_kwargs.items() if v is not None}

        logger.debug(f"Initializing LLM: provider={provider}, args={llm_kwargs_filtered}")
        try:
            return utils.get_llm_model(provider=provider, **llm_kwargs_filtered)
        except utils.MissingAPIKeyError as e:
            logger.error(f"LLM Initialization Failed: {e}")
            raise  # Re-raise to prevent tool execution without LLM

    # --- Internal Helper for Browser Agent Execution ---
    async def _execute_browser_agent_logic(
        task: str,
        add_infos: str,
        llm: BaseChatModel,
        browser: CustomBrowser,
        browser_context: CustomBrowserContext,
        agent_config: Dict[str, Any],
    ) -> Tuple[str, Optional[str]]:
        """Encapsulates the logic to run the CustomAgent."""
        try:
            controller = CustomController()
            agent = CustomAgent(
                task=task,
                add_infos=add_infos,
                llm=llm,
                browser=browser,
                browser_context=browser_context,
                controller=controller,
                system_prompt_class=CustomSystemPrompt,
                agent_prompt_class=CustomAgentMessagePrompt,
                use_vision=agent_config.get("use_vision", True),
                max_actions_per_step=agent_config.get("max_actions_per_step", 5),
                tool_calling_method=agent_config.get("tool_calling_method", "auto"),
                max_input_tokens=agent_config.get("max_input_tokens", 128000),
                generate_gif=agent_config.get("generate_gif", False),
            )

            history = await agent.run(max_steps=agent_config.get("max_steps", 100))

            # Save history if path provided
            history_path = agent_config.get("save_agent_history_path")
            if history_path:
                os.makedirs(history_path, exist_ok=True)
                history_file = os.path.join(history_path, f"{agent.state.agent_id}.json")
                try:
                    agent.save_history(history_file)
                    logger.info(f"Agent history saved to {history_file}")
                except Exception as save_err:
                    logger.error(f"Failed to save agent history: {save_err}")

            final_result = history.final_result()
            errors = history.errors()  # This returns a string or None

            return (
                final_result or "Task completed, but no specific result extracted.",
                errors,
            )

        except Exception as e:
            logger.error(f"Error during agent execution logic: {e}\n{traceback.format_exc()}")
            return f"Agent execution failed: {str(e)}", str(e)

    # --- Synchronous MCP Tools ---

    @server.tool()
    async def run_browser_agent(ctx: Context, task: str, add_infos: str = "") -> str:
        """Runs a browser agent task synchronously and waits for the result."""
        lifespan_ctx = ctx.request_context.lifespan_context
        browser = lifespan_ctx.get("browser")
        browser_context = lifespan_ctx.get("browser_context")

        # Check if browser/context are available (unless using CHROME_CDP)
        if not browser or not browser_context:
            if os.getenv("CHROME_CDP"):
                # Allow execution if CHROME_CDP is set, assuming connection happens elsewhere
                # We pass None for browser/context, the logic inside might need adjustment
                # or we assume the agent/controller handles CDP connection internally.
                # For now, let's log a warning and proceed, assuming internal handling.
                logger.warning("Running browser agent with CHROME_CDP set, but no managed browser/context. Assuming internal CDP connection.")
                # Set browser/context to None explicitly for the call
                browser = None
                browser_context = None
            else:
                msg = "Managed browser/context not initialized and CHROME_CDP not set. Cannot execute task."
                logger.error(msg)
                return f"Error: {msg}"

        try:
            logger.info(f"Starting synchronous browser task: {task}")
            llm = _get_llm_from_env()  # Can raise MissingAPIKeyError

            agent_config = {
                "use_vision": get_env_bool("MCP_USE_VISION", True),
                "max_steps": int(os.getenv("MCP_MAX_STEPS", "100")),
                "max_actions_per_step": int(os.getenv("MCP_MAX_ACTIONS_PER_STEP", "5")),
                "tool_calling_method": os.getenv("MCP_TOOL_CALLING_METHOD", "auto"),
                "max_input_tokens": int(os.getenv("MCP_MAX_INPUT_TOKENS", "128000")),
                "generate_gif": get_env_bool("MCP_GENERATE_GIF", False),
                "save_agent_history_path": os.getenv("MCP_AGENT_HISTORY_PATH"),
                # Add browser trace path for potential use in agent logic if needed
                "save_trace_path": os.getenv("BROWSER_TRACE_PATH"),
            }

            # Call the internal helper function
            result, error = await _execute_browser_agent_logic(
                task=task,
                add_infos=add_infos,
                llm=llm,
                browser=browser,  # Can be None if CHROME_CDP is used
                browser_context=browser_context,  # Can be None if CHROME_CDP is used
                agent_config=agent_config,
            )

            if error:
                logger.error(f"Synchronous browser task '{task}' failed: {error}")
                # Return result even if there's an error, as it might contain partial info
                return f"Task failed: {error}\n\nResult: {result}"
            else:
                logger.info(f"Synchronous browser task '{task}' completed.")
                return result

        except utils.MissingAPIKeyError as e:
            logger.error(f"Cannot run browser agent task '{task}': {e}")
            return f"Configuration Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error running sync browser agent task '{task}': {e}\n{traceback.format_exc()}")
            return f"Error during task execution: {str(e)}"

    @server.tool()
    async def run_deep_research(
        ctx: Context,
        research_task: str,
        max_search_iterations: Optional[int] = 10,
        max_query_per_iteration: Optional[int] = 3,
    ) -> str:
        """Performs deep research synchronously and waits for the report."""
        # Deep research manages its own browser/state.
        # Create a temporary AgentState for cancellation signal specific to this task.
        task_agent_state = AgentState()

        try:
            task_agent_state.clear_stop()  # Ensure clean state
            logger.info(f"Starting synchronous deep research task: {research_task}")
            llm = _get_llm_from_env()  # Can raise MissingAPIKeyError

            # Gather config for deep_research from environment variables
            research_config = {
                # Tool inputs override env vars if provided
                "max_search_iterations": max_search_iterations or int(os.getenv("MCP_RESEARCH_MAX_ITERATIONS", "10")),
                "max_query_num": max_query_per_iteration or int(os.getenv("MCP_RESEARCH_MAX_QUERY", "3")),  # Note: deep_research uses max_query_num
                # Other config from env
                "use_vision": get_env_bool("MCP_USE_VISION", False),  # Research might not need vision by default
                "headless": get_env_bool("BROWSER_HEADLESS", True),  # Research often runs headless
                "use_own_browser": get_env_bool("MCP_RESEARCH_USE_OWN_BROWSER", False),
                "chrome_cdp": os.getenv("CHROME_CDP"),
                "chrome_path": os.getenv("CHROME_PATH"),
                "chrome_user_data": os.getenv("CHROME_USER_DATA"),
                "disable_security": get_env_bool("BROWSER_DISABLE_SECURITY", True),  # Often needed for automation
                "window_w": int(os.getenv("BROWSER_WINDOW_WIDTH", "1280")),
                "window_h": int(os.getenv("BROWSER_WINDOW_HEIGHT", "720")),
                "save_dir": os.getenv("MCP_RESEARCH_SAVE_DIR"),
                "max_steps": int(os.getenv("MCP_RESEARCH_AGENT_MAX_STEPS", "10")),
            }
            # Filter out None values before passing
            research_config_filtered = {k: v for k, v in research_config.items() if v is not None}

            # Directly call the deep_research function from utils
            report_content, file_path_or_error = await deep_research(
                task=research_task,
                llm=llm,
                agent_state=task_agent_state,
                **research_config_filtered,  # Pass filtered config as kwargs
            )

            # Check if deep_research indicated an error in its return tuple structure
            # (Assuming it returns (content, error_message_or_None) or similar)
            # Based on deep_research implementation, it returns (report_content, file_path) on success
            # and (error_report_content, None) or raises an exception on failure.
            # Let's refine error checking based on its actual return signature.
            # It seems to return (report_content_with_error_msg, None) on error during report generation
            # and potentially raises exceptions earlier.

            # A simple check: if file_path_or_error is None and report_content contains error indicators
            error_occurred = False
            error_message = ""
            if file_path_or_error is None:
                # Check common error patterns in the returned content
                if "Error generating report:" in report_content or "Research Incomplete" in report_content:
                    error_occurred = True
                    error_message = report_content  # The content itself is the error message/partial report
            elif (
                isinstance(file_path_or_error, str) and "Error:" in file_path_or_error
            ):  # Handle case where error string might be returned instead of path
                error_occurred = True
                error_message = file_path_or_error
                report_content = f"Deep research failed: {error_message}"  # Overwrite content with error

            if error_occurred:
                logger.error(f"Synchronous deep research task '{research_task}' failed or was incomplete: {error_message}")
                # Return the potentially partial report content which includes the error message
                return report_content
            else:
                logger.info(f"Synchronous deep research task '{research_task}' completed. Report saved to {file_path_or_error}")
                return report_content  # Return the full report content

        except utils.MissingAPIKeyError as e:
            logger.error(f"Cannot run deep research task '{research_task}': {e}")
            return f"Configuration Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error running sync deep research task '{research_task}': {e}\n{traceback.format_exc()}")
            # Attempt to generate a partial report if possible, otherwise return error string
            # The deep_research function's final `except` block handles partial report generation.
            # So, if an exception reaches here, it's likely before or during the final report generation attempt.
            return f"Error during deep research execution: {str(e)}"

    # Tool registration is handled by the @server.tool decorator

    return server


server = serve()


def main():
    server.run()


if __name__ == "__main__":
    main()
