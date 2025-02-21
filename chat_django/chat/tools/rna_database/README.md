# RNA Database MCP Server

A Model Context Protocol (MCP) server that provides access to tRNA sequence data through standardized tools.

## Features

- Search tRNA sequences by:
  - Isotype (e.g., "SeC", "Ala", "Gly")
  - Anticodon
  - Model scores
- Get detailed sequence information
- Full MCP protocol compliance
- Compatible with both standalone and Django environments

## Tools

### search_rna
Search for tRNA sequences matching criteria:

```python
@app.tool()
async def search_rna(
    species: str = "human",
    isotype: Optional[str] = None,
    anticodon: Optional[str] = None,
    min_score: Optional[float] = None,
    context: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]
```

Example usage:
```python
# Using MCP client
result = await client.call_tool("search_rna", {
    "species": "human",
    "isotype": "SeC",
    "min_score": 80.0,
    "context": {
        "user_id": "user123",
        "chat_id": "chat456",
        "message_id": "msg789"  # Required for data association
    }
})
```

### get_sequence
Get detailed information for a specific sequence:

```python
@app.tool()
async def get_sequence(
    gene_symbol: str,
    context: Optional[Dict[str, str]] = None
) -> Dict[str, Any]
```

Example usage:
```python
# Using MCP client
result = await client.call_tool("get_sequence", {
    "gene_symbol": "tRNA-SeC-TCA-1-1",
    "context": {
        "user_id": "user123",
        "chat_id": "chat456",
        "message_id": "msg789"  # Required for data association
    }
})
```

## Installation

```bash
# Install dependencies
pip install mcp httpx

# Run the server
python server.py
```

## Usage

### As a standalone server
```python
from server import RNADatabaseServer

# Initialize and run server
server = RNADatabaseServer()
server.run()
```

### With Django integration
The server automatically integrates with Django models when available:

```python
# Django models are automatically detected and used for persistence
# No additional configuration needed
```

## Testing

Run the test suite:
```bash
python -m pytest test_mcp.py
```

## Protocol Compliance

This server implements the Model Context Protocol (MCP) 1.2.0 specification:

- Standard tool definitions with JSON Schema
- Proper initialization and capability negotiation
- Standard transport support (stdio and SSE)
- Proper error handling and status codes
- Context preservation for persistence

## Security Considerations

- Input validation on all parameters
- SQL injection prevention
- Rate limiting support
- Proper error handling
- Context isolation between users