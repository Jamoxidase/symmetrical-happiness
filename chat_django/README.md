# Chat Application

A Django-based chat application with AI capabilities, implementing the Model Context Protocol (MCP) for extensible tool integration.

## Features

- AI-powered chat using Claude
- Full MCP 1.2.0 protocol implementation
- Dynamic tRNA data analysis through MCP tools
- Optional Redis caching for production
- RESTful API endpoints
- CORS support
- Environment-based configuration

## MCP Integration

The application implements the Model Context Protocol (MCP) 1.2.0 specification, providing a standardized way to connect Claude with various tools and data sources:

### MCP Client
- Full protocol compliance with proper initialization
- Support for tool discovery and execution
- Proper transport handling (stdio and SSE)
- Context preservation across interactions
- Proper error handling and logging

### MCP Servers
Currently includes:

1. RNA Database Server
   - Search tRNA sequences by various criteria
   - Get detailed sequence information
   - Full MCP tool implementation
   - Django model integration for persistence

### Tool Integration
Tools are exposed through standardized MCP interfaces:

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

### Data Flow
1. User query is processed by Claude
2. Claude identifies required tools
3. MCP client executes tool calls through appropriate servers
4. Results are stored in PostgreSQL and returned to Claude
5. Claude provides natural language responses

### Data Storage
- Sequence data is stored in PostgreSQL
- Each sequence entry includes:
  - Basic fields (gene_symbol, anticodon, etc.)
  - Sequence data (genomic, mature tRNA)
  - Structure information
  - Overview and metadata

## Documentation

- [Cache Configuration](docs/CACHE.md)

## Environment Variables

The application can be configured using environment variables:

### Core Settings
- `DJANGO_SECRET_KEY`: Django secret key (default: 'your-secret-key-here')
- `DJANGO_DEBUG`: Enable debug mode (default: 'True')
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts (default: '*')
- `FRONTEND_URL`: Frontend application URL (default: 'http://localhost:3000')

### Database Configuration
- `DATABASE_URL`: Full database URL (optional, falls back to SQLite if not provided)
- `POSTGRES_SSL_MODE`: PostgreSQL SSL mode (default: 'prefer')

### Cache Configuration
See [Cache Documentation](docs/CACHE.md) for details.

### API Keys
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude access

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Production Deployment

For production deployment:

1. Set `DJANGO_DEBUG=false`
2. Set `USE_REDIS=true` and configure `REDIS_URL`
3. Configure a proper database using `DATABASE_URL`
4. Set appropriate `DJANGO_ALLOWED_HOSTS`
5. Use a production-grade server like Gunicorn
6. Set up proper SSL/TLS