"""Simple MCP test server"""
import asyncio
import logging
from typing import Dict, Any, List
from mcp.server import Server
import mcp.types as types

logger = logging.getLogger(__name__)

class TestServer:
    def __init__(self):
        self.app = Server("test-server")
        self._register_handlers()
        logger.info("Test MCP Server initialized")

    def _register_handlers(self):
        @self.app.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="echo",
                    description="Echo back the input message",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Message to echo back"
                            }
                        },
                        "required": ["message"]
                    }
                )
            ]

        @self.app.call_tool()
        async def call_tool(
            name: str,
            arguments: Dict[str, Any]
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool execution"""
            if name == "echo":
                message = arguments["message"]
                logger.info(f"Echo tool called with message: {message}")
                return [types.TextContent(type="text", text=message)]
            else:
                raise types.McpError(
                    code="UNKNOWN_TOOL",
                    message=f"Unknown tool: {name}"
                )

    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Test MCP Server")
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as streams:
            await self.app.run(
                streams[0],
                streams[1],
                self.app.create_initialization_options()
            )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = TestServer()
    asyncio.run(server.run())