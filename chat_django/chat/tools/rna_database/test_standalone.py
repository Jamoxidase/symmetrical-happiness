"""Standalone tests for RNA Database MCP server"""
import asyncio
import pytest
from pathlib import Path
from server import RNADatabaseServer

class MockModel:
    """Mock Django model for standalone testing"""
    objects = type('MockManager', (), {
        'acreate': staticmethod(lambda **kwargs: type('MockInstance', (), kwargs)())
    })()

@pytest.fixture
def server():
    """Create server instance for testing"""
    return RNADatabaseServer()

@pytest.mark.asyncio
async def test_search_rna():
    """Test RNA sequence search"""
    server = RNADatabaseServer()
    
    # Test search with isotype
    results = await server.app.tools["search_rna"](
        species="human",
        isotype="SeC"
    )
    assert len(results) > 0
    for result in results:
        assert result["isotype"] == "SeC"

    # Test search with score filter
    results = await server.app.tools["search_rna"](
        species="human",
        min_score=80.0
    )
    assert len(results) > 0
    for result in results:
        assert result["general_score"] >= 80.0

@pytest.mark.asyncio
async def test_get_sequence():
    """Test sequence retrieval"""
    server = RNADatabaseServer()
    
    # First get a gene symbol through search
    results = await server.app.tools["search_rna"](species="human", isotype="SeC")
    assert len(results) > 0
    gene_symbol = results[0]["gene_symbol"]
    
    # Test sequence retrieval
    sequence = await server.app.tools["get_sequence"](gene_symbol=gene_symbol)
    assert sequence["gene_symbol"] == gene_symbol
    assert "sequences" in sequence
    assert "overview" in sequence

@pytest.mark.asyncio
async def test_invalid_inputs():
    """Test error handling for invalid inputs"""
    server = RNADatabaseServer()
    
    # Test invalid gene symbol
    with pytest.raises(ValueError):
        await server.app.tools["get_sequence"](gene_symbol="invalid-symbol")
    
    # Test invalid species
    results = await server.app.tools["search_rna"](species="invalid")
    assert len(results) == 0

if __name__ == "__main__":
    asyncio.run(pytest.main([__file__]))