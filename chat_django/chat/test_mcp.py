"""Test MCP implementation with multiple servers"""
import asyncio
import logging
from pathlib import Path

from .mcp_client import ChatMCPClient, ChatContext
from .mcp_manager import ServerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Test MCP implementation with RNA database and filesystem servers"""
    client = ChatMCPClient()
    
    try:
        # Add RNA database server
        await client.add_server(ServerConfig(
            name="rna",
            command="python",
            args=[str(Path(__file__).parent / "tools/rna_database/mcp_server.py")]
        ))
        
        # Add filesystem server
        await client.add_server(ServerConfig(
            name="fs",
            command="npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                str(Path.home())
            ]
        ))
        
        # Set up chat context
        context = ChatContext(
            user_id="test_user",
            chat_id="test_chat",
            message_id="test_message"
        )
        
        # Test queries that use both servers
        queries = [
            "Find all selenocysteine tRNAs and save the results to a file called trna_results.txt",
            "Look for any tRNAs with a score above 90 and create a directory called high_scoring_trnas with their details",
            "Search for alanine tRNAs and create a summary report"
        ]
        
        for query in queries:
            logger.info(f"\nProcessing query: {query}")
            response = await client.process_query(query, context)
            print(f"\nResponse:\n{response}\n")
            
    except Exception as e:
        logger.error(f"Error in test: {e}")
        raise
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())