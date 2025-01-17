import os
import json
import logging
import subprocess
import requests
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, Any
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from playwright.async_api import (
    Playwright,
    Browser as PlaywrightBrowser,
    BrowserContext as PlaywrightBrowserContext,
)

logger = logging.getLogger(__name__)


@dataclass
class BrowserPersistenceConfig:
    """Configuration for browser persistence"""

    persistent_session: bool = False
    user_data_dir: Optional[str] = None
    debugging_port: Optional[int] = None
    debugging_host: Optional[str] = None

    @classmethod
    def from_env(cls) -> "BrowserPersistenceConfig":
        """Create config from environment variables"""
        return cls(
            persistent_session=os.getenv("CHROME_PERSISTENT_SESSION", "").lower()
            == "true",
            user_data_dir=os.getenv("CHROME_USER_DATA"),
            debugging_port=int(os.getenv("CHROME_DEBUGGING_PORT", "9222")),
            debugging_host=os.getenv("CHROME_DEBUGGING_HOST", "localhost"),
        )


class CustomBrowserContext(BrowserContext):
    def __init__(
        self, browser: "Browser", config: BrowserContextConfig = BrowserContextConfig()
    ):
        super(CustomBrowserContext, self).__init__(browser=browser, config=config)

    async def _create_context(
        self, browser: PlaywrightBrowser
    ) -> PlaywrightBrowserContext:
        """Creates a new browser context with anti-detection measures and loads cookies if available."""
        # If we have a context, return it directly

        # Check if we should use existing context for persistence
        if self.browser.config.chrome_instance_path and len(browser.contexts) > 0:
            # Connect to existing Chrome instance instead of creating new one
            context = browser.contexts[0]
        else:
            # Original code for creating new context
            context = await browser.new_context(
                viewport=self.config.browser_window_size,
                no_viewport=False,
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
                ),
                java_script_enabled=True,
                bypass_csp=self.config.disable_security,
                ignore_https_errors=self.config.disable_security,
                record_video_dir=self.config.save_recording_path,
                record_video_size=self.config.browser_window_size,
            )

        if self.config.trace_path:
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)

        # Load cookies if they exist
        if self.config.cookies_file and os.path.exists(self.config.cookies_file):
            with open(self.config.cookies_file, "r") as f:
                cookies = json.load(f)
                logger.info(
                    f"Loaded {len(cookies)} cookies from {self.config.cookies_file}"
                )
                await context.add_cookies(cookies)

        # Expose anti-detection scripts
        await context.add_init_script(
            """
            // Webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Chrome runtime
            window.chrome = { runtime: {} };

            // Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            """
        )

        return context


class CustomBrowser(Browser):
    def __init__(self, config: BrowserConfig):
        super().__init__(config=config)
        self.persistence_config = BrowserPersistenceConfig.from_env()

    async def new_context(
        self, config: BrowserContextConfig = BrowserContextConfig()
    ) -> CustomBrowserContext:
        return CustomBrowserContext(config=config, browser=self)

    async def _setup_browser(self, playwright: Playwright):
        """Sets up and returns a Playwright Browser instance with persistent context."""
        if self.config.wss_url:
            browser = await playwright.chromium.connect(self.config.wss_url)
            return browser
        elif self.config.chrome_instance_path:
            try:
                # Check if browser is already running
                response = requests.get(
                    f"http://{self.persistence_config.debugging_host}:{self.persistence_config.debugging_port}/json/version",
                    timeout=2,
                )
                if response.status_code == 200:
                    logger.info("Reusing existing Chrome instance")
                    browser = await playwright.chromium.connect_over_cdp(
                        endpoint_url=f"http://{self.persistence_config.debugging_host}:{self.persistence_config.debugging_port}",
                        timeout=20000,  # 20 second timeout for connection
                    )
                    return browser
            except requests.ConnectionError:
                logger.debug("No existing Chrome instance found, starting a new one")

            # Start a new Chrome instance
            subprocess.Popen(
                [
                    self.config.chrome_instance_path,
                    f"--remote-debugging-port={self.persistence_config.debugging_port}",
                    f"--user-data-dir={self.persistence_config.user_data_dir or os.path.join(os.getcwd(), 'user_data')}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Attempt to connect again after starting a new instance
            for _ in range(10):
                try:
                    response = requests.get(
                        f"http://{self.persistence_config.debugging_host}:{self.persistence_config.debugging_port}/json/version",
                        timeout=2,
                    )
                    if response.status_code == 200:
                        break
                except requests.ConnectionError:
                    pass
                await asyncio.sleep(1)

            try:
                browser = await playwright.chromium.connect_over_cdp(
                    endpoint_url=f"http://{self.persistence_config.debugging_host}:{self.persistence_config.debugging_port}",
                    timeout=20000,  # 20 second timeout for connection
                )
                return browser
            except Exception as e:
                logger.error(f"Failed to start a new Chrome instance.: {str(e)}")
                raise RuntimeError(
                    "To start chrome in Debug mode, you need to close all existing Chrome instances and try again otherwise we can not connect to the instance."
                )
        else:
            try:
                disable_security_args = []
                if self.config.disable_security:
                    disable_security_args = [
                        "--disable-web-security",
                        "--disable-site-isolation-trials",
                        "--disable-features=IsolateOrigins,site-per-process",
                    ]

                # Use launch_persistent_context if persistence is enabled
                if self.persistence_config.persistent_session:
                    user_data_dir = (
                        self.persistence_config.user_data_dir
                        or os.path.join(os.getcwd(), "user_data")
                    )
                    browser_context = (
                        await playwright.chromium.launch_persistent_context(
                            user_data_dir=user_data_dir,
                            headless=self.config.headless,
                            args=[
                                "--no-sandbox",
                                "--disable-blink-features=AutomationControlled",
                                "--disable-infobars",
                                "--disable-background-timer-throttling",
                                "--disable-popup-blocking",
                                "--disable-backgrounding-occluded-windows",
                                "--disable-renderer-backgrounding",
                                "--disable-window-activation",
                                "--disable-focus-on-load",
                                "--no-first-run",
                                "--no-default-browser-check",
                                "--no-startup-window",
                                "--window-position=0,0",
                            ]
                            + disable_security_args
                            + self.config.extra_chromium_args,
                            proxy=self.config.proxy,
                        )
                    )
                    return browser_context
                else:
                    browser = await playwright.chromium.launch(
                        headless=self.config.headless,
                        args=[
                            "--no-sandbox",
                            "--disable-blink-features=AutomationControlled",
                            "--disable-infobars",
                            "--disable-background-timer-throttling",
                            "--disable-popup-blocking",
                            "--disable-backgrounding-occluded-windows",
                            "--disable-renderer-backgrounding",
                            "--disable-window-activation",
                            "--disable-focus-on-load",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--no-startup-window",
                            "--window-position=0,0",
                        ]
                        + disable_security_args
                        + self.config.extra_chromium_args,
                        proxy=self.config.proxy,
                    )
                    return browser
            except Exception as e:
                logger.error(f"Failed to initialize Playwright browser: {str(e)}")
                raise
