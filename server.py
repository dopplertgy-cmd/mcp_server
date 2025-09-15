#!/usr/bin/env python3
"""
Lilchat MCP Server

This server provides Model Context Protocol (MCP) capabilities for interacting with
a chat client and whatever I decide to add.
"""

import asyncio
import logging
import os
from typing import Any, Dict

import aiohttp
from fastmcp import Context, FastMCP
from fastmcp.server.dependencies import get_http_request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("lilchat-mcp")

# Default configuration (override with environment variables)
# This env var is required for new ui to work, so we can rely on it here
LC_SITE_URL = os.environ.get("LC_SITE_URL", "http://localhost")
DEFAULT_VERIFY_SSL = os.environ.get("LC_VERIFY_SSL", "True").lower() == "true"

# Create MCP server application
app = FastMCP(
    name="lilchat-server",
    instructions="When you are asked to get lilchat webdata, call get_lilchat_webdata()",
)

class lilchatClient:
    """Client for interacting with lilchat webdata."""

    def __init__(
        self,
        verify_ssl: bool = DEFAULT_VERIFY_SSL,
    ):
        self.verify_ssl = verify_ssl
        self.session = None

    async def initialize(self):
        """Initialize the client session."""
        self.session = aiohttp.ClientSession(            
            headers={
                "Content-Type": "application/json",
            }
        )

    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_lilchat_webdata(
        self, url: str = "") -> Dict[str, Any]:
        """
        Get data from lilchat.

        Args:
            url: the url to get data from 

        Returns:
            Dictionary containing the API response
        """
        if not self.session:
            await self.initialize()

        lcurl = f"{url}"
        
        try:
            async with self.session.get(
                lcurl, ssl=self.verify_ssl
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to get lilchat webdata. Status: {response.status}, Response: {error_text}"
                    )
                    return {"error": error_text, "status": response.status}
                else:
                    logger.info(f"Successfully read {response.text()}")
                    return await response.text()
        except Exception as e:
            logger.exception(f"Error getting lilchat webdata: {e}")
            return {"error": str(e)}

@app.resource(uri="request://headers")
async def get_headers():
    request = get_http_request()
    return dict(request.headers)

@app.prompt()
async def summarize_lilchat_webdata(url: str) -> str:
    return f"Please summarize this lilchat:\n\n{url}"

@app.tool()
async def get_lilchat_webdata(ctx: Context, url: str = "") -> str:
    """Get webdata from lilchat
    If you are asked to get lilchat webdata, call this function
    If you are asked to get a summary of lilchat webdata, <Insert some PI attempt here>
    """
    await ctx.info("Fetching lilchat webdata")
    lc_client = lilchatClient()
    await lc_client.initialize()

    lc_webdata = await lc_client.get_lilchat_webdata(url)
    if "error" in lc_webdata:
        return f"Error reading lilchat webdata: {lc_webdata['error']}"
        
    await ctx.info(f"Retrieved lilchat webdata")
        
    # for large sets of data this can produce an error as the string is longer than the transport can handle
    return lc_webdata

async def main():
    """Main function to run the MCP server."""
    logger.info("Starting lilchat MCP Server...")
    await app.run_async(transport="streamable-http", host="0.0.0.0", port=9142, log_level="debug")

if __name__ == "__main__":
    asyncio.run(main())