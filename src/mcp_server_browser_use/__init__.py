import sys
import asyncio
import argparse
import os

import logging

file_handler = logging.FileHandler("browser_use.log")
logging.getLogger("browser_use").addHandler(file_handler)
logging.getLogger().addHandler(file_handler)


from . import server

def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description="browser-use MCP Server")

    # args = parser.parse_args()
    asyncio.run(server.run_server_stdio())


# Optionally expose other important items at package level
__all__ = ["main", "server"]
