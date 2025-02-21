"""Test MCP implementation"""
import asyncio
import logging
from typing import Dict, Any, List
from mcp.server import Server
import mcp.types as types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

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

async def test_client():
    """Test MCP client"""
    exit_stack = AsyncExitStack()
    
    try:
        # Connect to server
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "chat.tools.test_server"]
        )
        
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        session = await exit_stack.enter_async_context(ClientSession(stdio_transport[0], stdio_transport[1]))
        
        # Initialize session
        init_result = await session.initialize()
        logger.info(f"Server capabilities: {init_result.capabilities}")
        
        # List tools
        tools_response = await session.list_tools()
        logger.info(f"Available tools: {[tool.name for tool in tools_response.tools]}")
        
        # Test echo tool
        result = await session.call_tool("echo", {"message": "Hello MCP!"})
        logger.info(f"Echo result: {result.content}")
        
    finally:
        await exit_stack.aclose()

async def main():
    """Run server and client tests"""
    # Start server
    server = TestServer()
    server_task = asyncio.create_task(server.run())
    
    try:
        # Wait for server to start
        await asyncio.sleep(1)
        
        # Run client test
        await test_client()
        
    finally:
        # Clean up server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())