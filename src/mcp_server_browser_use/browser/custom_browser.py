import logging

from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContextConfig

from mcp_server_browser_use.browser.custom_context import CustomBrowserContext

logger = logging.getLogger(__name__)


class CustomBrowser(Browser):
    async def new_context(self, config: BrowserContextConfig = BrowserContextConfig()) -> CustomBrowserContext:
        return CustomBrowserContext(config=config, browser=self)
