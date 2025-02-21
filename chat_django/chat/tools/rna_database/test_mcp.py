"""Integration tests for RNA Database MCP server"""
import asyncio
import pytest
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

@pytest.fixture
async def client():
    """Create MCP client connected to server"""
    exit_stack = AsyncExitStack()
    try:
        # Start server process
        server_path = str(Path(__file__).parent / "server.py")
        server_params = StdioServerParameters(
            command="python",
            args=[server_path],
            env=None
        )
        
        # Connect client
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await exit_stack.enter_async_context(ClientSession(stdio, write))
        
        # Initialize session
        await session.initialize()
        
        yield session
        
    finally:
        await exit_stack.aclose()

@pytest.fixture
def context():
    """Test context for persistence"""
    return {
        "user_id": "test_user",
        "chat_id": "test_chat",
        "message_id": "test_message"
    }

@pytest.mark.asyncio
async def test_list_tools(client):
    """Test tool discovery"""
    response = await client.list_tools()
    tools = response.tools
    
    assert len(tools) == 2
    tool_names = {tool.name for tool in tools}
    assert "search_rna" in tool_names
    assert "get_sequence" in tool_names

@pytest.mark.asyncio
async def test_search_rna(client, context):
    """Test RNA sequence search"""
    # Search with isotype
    result = await client.call_tool("search_rna", {
        "species": "human",
        "isotype": "SeC",
        "context": context
    })
    
    assert len(result.content) > 0
    sequences = result.content
    for sequence in sequences:
        assert sequence["isotype"] == "SeC"
    
    # Search with score filter
    result = await client.call_tool("search_rna", {
        "species": "human",
        "min_score": 80.0,
        "context": context
    })
    
    assert len(result.content) > 0
    sequences = result.content
    for sequence in sequences:
        assert sequence["general_score"] >= 80.0

@pytest.mark.asyncio
async def test_get_sequence(client, context):
    """Test sequence retrieval"""
    # First get a gene symbol through search
    search_result = await client.call_tool("search_rna", {
        "species": "human",
        "isotype": "SeC",
        "context": context
    })
    
    assert len(search_result.content) > 0
    gene_symbol = search_result.content[0]["gene_symbol"]
    
    # Get sequence details
    result = await client.call_tool("get_sequence", {
        "gene_symbol": gene_symbol,
        "context": context
    })
    
    sequence = result.content
    assert sequence["gene_symbol"] == gene_symbol
    assert "sequences" in sequence
    assert "overview" in sequence

@pytest.mark.asyncio
async def test_invalid_inputs(client, context):
    """Test error handling"""
    # Invalid gene symbol
    with pytest.raises(Exception):
        await client.call_tool("get_sequence", {
            "gene_symbol": "invalid-symbol",
            "context": context
        })
    
    # Invalid species
    result = await client.call_tool("search_rna", {
        "species": "invalid",
        "context": context
    })
    assert len(result.content) == 0

if __name__ == "__main__":
    asyncio.run(pytest.main([__file__]))