"""Test RNA Database MCP Server directly"""
import asyncio
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

logger = logging.getLogger(__name__)

async def main():
    """Test RNA database server"""
    exit_stack = AsyncExitStack()
    
    try:
        # Connect to server
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "chat.tools.rna_database.mcp_server_v2"]
        )
        
        # Create transport and session
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        session = await exit_stack.enter_async_context(ClientSession(stdio_transport[0], stdio_transport[1]))
        
        # Initialize session
        init_result = await session.initialize()
        logger.info(f"Server capabilities: {init_result.capabilities}")
        
        # List tools
        tools = await session.list_tools()
        logger.info(f"Available tools: {[tool.name for tool in tools.tools]}")
        
        # Test search_rna
        logger.info("\nTesting search_rna:")
        result = await session.call_tool("search_rna", {"isotype": "SeC"})
        logger.info(f"Found sequences: {result.content}")
        
        # Test get_sequence
        logger.info("\nTesting get_sequence:")
        result = await session.call_tool("get_sequence", {"gene_symbol": "tRNA-Sec-TCA-1-1"})
        logger.info(f"Sequence details: {result.content}")
        
    finally:
        await exit_stack.aclose()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())