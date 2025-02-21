# Chat Module Documentation
- Somewhat outdated - jlarbale@ucsc.edu
## File Structure

### Core Files (Currently Used)
- `chatbot.py`: Main implementation of the chat system, including the ChatProcessor, PlanningAgent, and UserFacingAgent
- `views.py`: Main Django views for handling chat requests and SSE streaming
- `models.py`: Database models for Chat, Message, and Sequence
- `urls.py`: URL routing for chat endpoints
- `tool_wrappers.py`: Monitoring and caching wrappers for tools
- `cache.py`: Caching implementation for tool results
- `db_access.py`: Database access layer for chat history
- `event_manager.py`: Manages SSE event streaming
- `prompts.py`: System prompts for Claude agents

### MCP (Model Context Protocol) Implementation - this is not in use via MCP server, true MCP would requier seperate MCP server process 
- `mcp_client.py`: Core MCP client implementation with request/response types
- `mcp_manager.py`: Manages MCP server connections and tool registry

### Tool Implementation
- `tools/`: Directory containing tool implementations
  - `rna_database/`: tRNA database tool
  - `stdio_processor/`: Standard I/O processing tool - this would mediate communication with seperate MCP server processes

### Testing and Admin
- `test_mcp.py`: Tests for MCP implementation
- `admin.py`: Django admin interface configuration
- `tests.py`: Django test cases

### Legacy/Deprecated Files (Can be Removed)
- `mcp_chat.py`: Old MCP chat implementation
- `mcp_chat_v3.py`: Another version of MCP chat
- `views_mcp.py`: Alternative views using old MCP implementation
- `cache_new.py`: Unused new cache implementation

### File Dependencies
1. Main Request Flow:
   ```
   urls.py → views.py → chatbot.py → tools/* → models.py
   ```

2. Tool Execution Flow:
   ```
   chatbot.py → tool_wrappers.py → specific tool → cache.py
   ```

3. Data Access Flow:
   ```
   views.py → db_access.py → models.py
   ```

### Cleanup Recommendations
1. Remove deprecated files:
   - `mcp_chat.py`
   - `mcp_chat_v3.py`
   - `views_mcp.py`
   - `cache_new.py`

2. Consolidate MCP implementation:
   - Keep `mcp_client.py` and `mcp_manager.py`
   - Remove old versions

3. Update imports:
   - Ensure all imports use current files
   - Remove references to deprecated files

## Overview
The chat module implements an AI-powered chat system with tool integration capabilities. It uses a two-agent architecture:
1. Planning Agent: Determines what tools to use and in what order
2. User-Facing Agent: Generates human-readable responses using the collected data

## Architecture

### Core Components
- `ChatManager`: Global singleton managing chat sessions
- `ChatProcessor`: Handles individual chat sessions and tool execution
- `PlanningAgent`: Makes decisions about tool usage
- `UserFacingAgent`: Generates final responses
- `RNADatabaseTool`: Example tool for querying tRNA data

### Data Flow
1. User makes request to `/api/chat/` endpoint
2. Request handled by `ChatView`
3. Single SSE connection established for entire interaction
4. Planning agent determines tool needs
5. Tools execute and store data in PostgreSQL
6. Tool data sent through SSE connection
7. Final response generated and streamed
8. Connection closes

## Database Integration

### PostgreSQL Tables

#### Sequences Table
```sql
CREATE TABLE sequences (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    chat_id UUID NOT NULL,
    message_id UUID NOT NULL,
    gene_symbol VARCHAR(255),
    anticodon VARCHAR(10),
    isotype VARCHAR(10),
    general_score FLOAT,
    isotype_score FLOAT,
    model_agreement BOOLEAN,
    features JSONB,
    locus JSONB,
    sequences JSONB,
    overview JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (chat_id) REFERENCES chats(id),
    FOREIGN KEY (message_id) REFERENCES messages(id)
);
```

#### Messages Table
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    chat_id UUID NOT NULL,
    content TEXT,
    role VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);
```

#### Chats Table
```sql
CREATE TABLE chats (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## API Endpoints

### POST /api/chat/
Creates a new chat and optionally starts a conversation.

Request:
```json
{
    "title": "Chat Title",
    "content": "Initial message"  // Optional
}
```

Response: Server-Sent Events stream with events:
```json
// Start Event
{
    "type": "start",
    "chat": {
        "id": "uuid",
        "title": "Chat Title"
    },
    "timestamp": "ISO-8601"
}

// Sequence Data Event (when tools retrieve data)
{
    "type": "sequence_data",
    "data": {
        "id": "uuid",
        "gene_symbol": "tRNA-SeC-TCA-1-1",
        "anticodon": "TCA",
        "isotype": "SeC",
        // ... other sequence fields
    }
}

// Token Event (chat response)
{
    "type": "token",
    "content": "chunk of text",
    "message_id": "uuid",
    "timestamp": "ISO-8601"
}

// End Event
{
    "type": "end",
    "message_id": "uuid",
    "timestamp": "ISO-8601"
}
```

## Tool Integration

### GET_TRNA Tool Workflow
The GET_TRNA tool provides access to tRNA sequence data through a structured workflow:

1. Planning Agent Decision:
   ```python
   # Example planning agent response
   "GET_TRNA Isotype_from_Anticodon:\"Ala\" Anticodon:\"AGC\" General_tRNA_Model_Score_min:50"
   ```

2. Tool Call Processing:
   - ChatProcessor routes GET_TRNA commands to RNADatabaseMCP
   - Parameters are parsed from the command string
   - Context (user_id, chat_id, message_id) is maintained

3. Database Query Flow:
   ```python
   # a. Parameter parsing
   params = {
       'isotype': 'Ala',
       'anticodon': 'AGC',
       'min_score': 50.0,
   }

   # b. MCP request creation
   request = MCPRequest(
       method="search_rna",
       params=params
   )

   # c. SQL query execution
   "SELECT * FROM human WHERE Isotype_from_Anticodon = ? AND Anticodon = ? AND General_tRNA_Model_Score >= ?"
   ```

4. Result Processing:
   - Results are fetched from SQLite
   - Each result is stored in PostgreSQL Sequence table
   - Data includes:
     - gene_symbol
     - anticodon
     - isotype
     - general_score
     - isotype_score
     - model_agreement
     - features
     - locus
     - sequences
     - overview

5. Response Format:
   ```python
   MCPResponse(
       status="success",
       data={
           "sequences": [...],  # List of found sequences
           "metadata": {
               "count": len(sequences),
               "query": params
           }
       }
   )
   ```

Key Features:
- Search by isotype, anticodon, and score threshold
- Automatic result persistence in PostgreSQL
- Full context preservation (user_id, chat_id, message_id)
- Comprehensive error handling
- Results can be referenced in later conversation

### Tool Interface
Tools should:
1. Accept user_id, chat_id, and message_id
2. Store results in PostgreSQL
3. Return data in a standardized format

Example Tool Implementation:
```python
class RNADatabaseTool:
    def __init__(self, user_id: str, chat_id: Optional[str] = None, 
                 message_id: Optional[str] = None):
        self.user_id = user_id
        self.chat_id = chat_id
        self.message_id = message_id

    async def search_rna(self, query: str) -> Tuple[str, List[Dict]]:
        # 1. Parse query
        # 2. Execute search
        # 3. Store in PostgreSQL
        # 4. Return results
```

### Adding New Tools
1. Create tool class in `/chat/tools/`
2. Add tool type to `ToolType` enum in chatbot.py
3. Update planning prompt to include new tool
4. Add tool initialization in ChatProcessor

## Configuration

### Environment Variables
- `PLANNING_LOOP_MAX`: Maximum planning iterations (default: 5)
- `ANTHROPIC_API_KEY`: API key for Claude
- Other Django settings (see core/settings.py)

### Prompts
Located in `/chat/prompts/`:
- `planning.py`: Guides tool selection
- `user_facing.py`: Formats responses

## External Dependencies

### Authentication
- Uses JWT tokens from authentication module
- Token must be included in Authorization header
- User ID extracted from token for data ownership

### Database
- Uses Django ORM for PostgreSQL
- Shared database with other modules
- Sequences linked to users, chats, and messages

### AI Service
- Uses Anthropic's Claude API
- Two instances per chat:
  1. Planning agent (temperature=0)
  2. User-facing agent (temperature=0.7)

## Error Handling

### Database Errors
- Failed sequence storage doesn't halt chat
- Errors logged but not exposed to user
- Partial results still returned

### Tool Errors
- Individual tool failures logged
- Planning agent can retry or skip
- User notified of tool failures

### Connection Handling
- SSE connection auto-reconnects
- Partial responses preserved
- Database consistency maintained

## System Coupling and Dependencies

### Core Dependencies
1. Authentication System
   - Only dependency is through JWT token validation
   - Chat views expect Authorization header with valid token
   - Token decoded to get user_id
   - Easy to modify by changing auth middleware or token handling

2. Database Models
   - Uses Django ORM but minimal model dependencies
   - Only requires User model for foreign key relationships
   - Sequence model is chat-specific, not used by other modules
   - Can be modified/replaced by updating model definitions and migrations

3. URL Configuration
   - Single entry point in core/urls.py: `path('api/chat/', include('chat.urls'))`
   - All chat routes prefixed with /api/chat/
   - Self-contained URL patterns
   - Can be remapped or restructured without affecting other modules

### Loose Coupling Points
1. Views Layer
   - ChatView and ChatHistoryView are independent
   - No dependencies on other app views
   - Uses standard Django view patterns
   - Can be replaced/modified without affecting core functionality

2. Tool System
   - Tools are self-contained in chat/tools/
   - No external dependencies beyond their own requirements
   - Tool interface is defined within chat module
   - New tools can be added without modifying existing code

3. AI Integration
   - Anthropic Claude integration is isolated in agent classes
   - Could be replaced with different AI service
   - Prompt system is self-contained
   - No dependencies on specific AI features outside chat module

### Restructuring Considerations
1. Safe to Modify
   - Internal chat logic and flow
   - Tool implementations
   - Database schema for chat-specific tables
   - Response formats and streaming
   - Agent architecture and prompts

2. Requires Coordination
   - Authentication integration points
   - Core database model relationships
   - Main URL routing
   - API contract with frontend

3. Migration Path
   ```python
   # Example of minimal core/urls.py integration
   urlpatterns = [
       # Other URLs...
       path('api/chat/', include('chat.urls')),  # Only touch point
   ]

   # Example of minimal model dependency
   class Sequence(models.Model):
       user = models.ForeignKey(
           settings.AUTH_USER_MODEL,  # Only external model dependency
           on_delete=models.CASCADE
       )
       # Chat-specific fields...
   ```

4. Potential Breaking Changes
   - Changing SSE event format
   - Modifying authentication requirements
   - Altering database relationships
   - Changing API endpoints

### Isolation Strategy
The chat module is designed for high cohesion and low coupling. To maintain this:
1. Keep all chat logic within the module
2. Use interfaces for external dependencies
3. Maintain clear API boundaries
4. Document integration points
5. Use dependency injection where possible

## Testing
```bash
# Run test script
./test_chat.sh

# Expected output includes:
# 1. Authentication success
# 2. Chat creation
# 3. SSE events (start, data, tokens, end)
```

## Common Issues

### SSE Connection
- Ensure proper CORS configuration
- Check for proxy buffering
- Verify client supports SSE

### Database
- Check PostgreSQL connection
- Verify migrations applied
- Check user permissions

### Tool Integration
- Verify tool initialization
- Check error handling
- Validate data formats