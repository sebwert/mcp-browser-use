from . import server
import asyncio
import argparse


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description="browser-use MCP Server")

    # args = parser.parse_args()
    asyncio.run(server.run_server_stdio())


# Optionally expose other important items at package level
__all__ = ["main", "server"]
