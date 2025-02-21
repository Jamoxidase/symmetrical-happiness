"""Simple MCP test client"""
import asyncio
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

logger = logging.getLogger(__name__)

async def main():
    """Test MCP client-server interaction"""
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())