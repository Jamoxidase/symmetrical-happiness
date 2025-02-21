# API Documentation for Frontend Engineers

## MCP Integration

The chat application implements the Model Context Protocol (MCP) 1.2.0 specification for tool integration. This enables standardized communication between the chat interface and various tools.

### MCP Server Configuration

MCP servers are configured in the Django settings:

```python
MCP_SERVERS = {
    "rna_database": {
        "command": "python",
        "args": ["tools/rna_database/server.py"],
        "env": {
            "DATABASE_URL": os.getenv("RNA_DATABASE_URL")
        }
    }
}
```

### MCP Message Flow

1. User sends message to chat endpoint
2. Backend processes message through Claude
3. Claude identifies required tools
4. MCP client executes tool calls:
   - Tool discovery through `tools/list`
   - Tool execution through `tools/call`
5. Results are processed and returned to Claude
6. Final response streamed to frontend

### MCP Tool Integration Example

```python
# Backend tool execution
result = await mcp_client.call_tool("search_rna", {
    "species": "human",
    "isotype": "SeC",
    "context": {
        "user_id": user_id,
        "chat_id": chat_id,
        "message_id": message_id
    }
})

# Tool response format
{
    "content": [
        {
            "gene_symbol": "tRNA-SeC-TCA-1-1",
            "anticodon": "TCA",
            "isotype": "SeC",
            "general_score": 95.2
        }
    ]
}
```

## CORS Configuration

### Setting Up CORS for Development
1. In your Django project, locate `/workspace/chat_app/core/settings.py`
2. Find the CORS settings section:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default port
    "http://localhost:5173",  # Vite default port
    os.getenv('FRONTEND_URL', 'http://localhost:3000')  # From environment
]
```
3. Add your frontend URL to this list OR set the FRONTEND_URL environment variable in your Django .env file:
```bash
FRONTEND_URL=http://your-frontend-url
```

## Base URL and Environment Setup
- Development: `http://localhost:8000`
- Production: Configure via environment variable

### Environment Variables
Frontend environment variables needed:
```bash
# .env for frontend
VITE_API_URL=http://localhost:8000  # or your Django server URL
```

## Chat Flow and Streaming Architecture

### Overview
This application uses Server-Sent Events (SSE) for real-time chat streaming, NOT WebSocket. Here's how it works:

1. Initial Request Flow:
   - Frontend sends POST request to create chat
   - Backend creates chat session
   - Backend establishes SSE connection
   - Frontend receives streamed response

2. Message Processing Flow:
   - Message sent to backend
   - Backend processes in chunks
   - Each chunk streamed via SSE
   - Frontend receives and displays chunks
   - Connection closes after completion

### Important Considerations
- SSE connections are one-way (server to client)
- Automatic reconnection is handled by the browser
- Each chat message creates a new SSE connection
- Connections timeout after 60 seconds of inactivity
- Messages are saved even if connection drops
- Partial responses are preserved in database

### Detailed Message Flow Example
1. Frontend initiates chat:
```javascript
// First, create a chat with initial message
const response = await fetch('http://localhost:8000/api/chat/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
        title: 'New Chat',
        content: 'Initial message'  // Optional
    })
});

// If content was provided, handle SSE response
if (content) {
    const eventSource = new EventSource(
        `http://localhost:8000/api/chat/${chatId}/stream/`,
        {
            withCredentials: true,
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );

    let currentMessage = '';

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
            case 'start':
                // Chat started, initialize UI
                console.log('Chat started:', data.chat.id);
                break;
                
            case 'token':
                // Append new token to message
                currentMessage += data.content;
                // Update UI with current message
                console.log('Received token:', data.content);
                break;
                
            case 'end':
                // Message complete, clean up
                console.log('Chat ended:', data.message_id);
                eventSource.close();
                break;
                
            case 'error':
                console.error('Error:', data.error);
                eventSource.close();
                break;
        }
    };

    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
    };
}
```

2. Backend processes request:
```python
# In chat/views.py
async def _stream_chat_response(self, chat: Chat, message: Message, user_id: str):
    try:
        # Start streaming
        yield 'data: {"type": "start", ...}\n\n'
        
        # Process message in chunks
        async for chunk in chat_manager.process_message(user_id, message.content):
            # Save to database every 0.5 seconds
            if time_to_update():
                await save_message(chunk)
            
            # Stream to client
            yield f'data: {{"type": "token", "content": "{chunk}"}}\n\n'
        
        # End streaming
        yield 'data: {"type": "end", ...}\n\n'
        
    except Exception as e:
        yield f'data: {{"type": "error", "error": "{str(e)}"}}\n\n'
```

### Error Handling Requirements
Frontend must handle these scenarios:

1. Connection Drops
```javascript
function createEventSource(url, token) {
    const es = new EventSource(url, { withCredentials: true });
    
    es.onerror = (error) => {
        // Save current state
        savePartialMessage(currentMessage);
        
        // Close current connection
        es.close();
        
        // Attempt to reconnect after 1 second
        setTimeout(() => {
            const newEs = createEventSource(url, token);
            // Handle new connection
        }, 1000);
    };
    
    return es;
}
```

2. Timeout Handling
```javascript
// Set timeout for response
const timeout = setTimeout(() => {
    eventSource.close();
    handleTimeout();
}, 60000);  // 60 seconds

// Clear timeout when message completes
eventSource.addEventListener('end', () => {
    clearTimeout(timeout);
});
```

3. Message Buffering
```javascript
let messageBuffer = '';
let lastUpdate = Date.now();

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'token') {
        messageBuffer += data.content;
        
        // Update UI at most every 100ms
        if (Date.now() - lastUpdate > 100) {
            updateUI(messageBuffer);
            lastUpdate = Date.now();
        }
    }
};
```

## Authentication

### Authentication Flow
1. User registers or logs in
2. Server returns JWT token
3. Frontend stores token securely
4. Token included in all subsequent requests
5. Token expires after 24 hours

### Register New User
```javascript
// Frontend request
const response = await fetch('http://localhost:8000/auth/register/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        email: "user@example.com",
        password: "secure_password"  // At least 8 characters
    })
});

// Successful response
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",  // JWT token
    "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "user@example.com"
    }
}

// Error response (400)
{
    "error": "Email already exists"
}
```

### Login
```javascript
// Frontend request
const response = await fetch('http://localhost:8000/auth/login/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        email: "user@example.com",
        password: "secure_password"
    })
});

// Successful response
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",  // JWT token
    "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "user@example.com"
    }
}

// Error response (401)
{
    "error": "Invalid credentials"
}
```

### Token Management
1. Store token securely:
```javascript
// Using secure HttpOnly cookie (recommended)
document.cookie = `token=${token}; HttpOnly; Secure; SameSite=Strict`;

// Or in localStorage (less secure)
localStorage.setItem('token', token);
```

2. Include token in requests:
```javascript
// Using fetch
const response = await fetch(url, {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});

// Using axios
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
```

3. Handle token expiration:
```javascript
// Check response status
if (response.status === 401) {
    // Token expired or invalid
    // Redirect to login
    window.location.href = '/login';
}
```

### Security Requirements
1. HTTPS required in production
2. Passwords must be at least 8 characters
3. Tokens expire after 24 hours
4. Use HttpOnly cookies when possible
5. Include CSRF protection for cookie-based auth
```

## Chat Endpoints

### List Chats
```http
GET /api/chat/
Authorization: Bearer jwt_token_here
```

Response:
```json
{
    "chats": [
        {
            "id": "uuid",
            "title": "Chat Title",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

### Create New Chat
```http
POST /api/chat/
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
    "title": "New Chat",
    "content": "Initial message (optional)"
}
```

Response (without initial message):
```json
{
    "chat_id": "uuid",
    "title": "New Chat"
}
```

Response (with initial message):
Server-Sent Events stream with the following event types:

1. Start Event:
```json
{
    "type": "start",
    "chat": {
        "id": "uuid",
        "title": "Chat Title"
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

2. Token Events (multiple):
```json
{
    "type": "token",
    "content": "chunk of text",
    "message_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

3. End Event:
```json
{
    "type": "end",
    "message_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

4. Error Event (if something goes wrong):
```json
{
    "type": "error",
    "error": "Error message",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Get Chat History
```http
GET /api/chat/{chat_id}/
Authorization: Bearer jwt_token_here
```

Response:
```json
{
    "chat": {
        "id": "uuid",
        "title": "Chat Title",
        "created_at": "2024-01-01T00:00:00Z"
    },
    "messages": [
        {
            "id": "uuid",
            "role": "user",
            "content": "User message",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "uuid",
            "role": "assistant",
            "content": "Assistant response",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

## Frontend Implementation Guide

### Authentication
1. Store JWT token securely (e.g., in HttpOnly cookie or secure localStorage)
2. Include token in Authorization header for all API requests
3. Handle token expiration and refresh (tokens expire in 24 hours)

### Chat Implementation
1. Use Server-Sent Events (SSE) for streaming responses:
```javascript
// Example using EventSource
const eventSource = new EventSource(
    `/api/chat/?token=${jwt_token}`,
    { withCredentials: true }
);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch (data.type) {
        case 'start':
            // Initialize chat UI
            break;
        case 'token':
            // Append token to current message
            break;
        case 'end':
            // Finalize message, cleanup
            break;
        case 'error':
            // Handle error
            break;
    }
};

eventSource.onerror = (error) => {
    // Handle connection errors
};
```

2. Handle disconnections gracefully:
   - Save partial messages
   - Implement reconnection logic
   - Show appropriate UI feedback

### CORS Configuration
1. Add your frontend URL to CORS settings in Django:
   - Set `FRONTEND_URL` environment variable
   - Or add directly to `CORS_ALLOWED_ORIGINS` in settings.py

2. Ensure your frontend includes credentials:
```javascript
// Fetch API
fetch(url, {
    credentials: 'include',
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

// Axios
axios.defaults.withCredentials = true;
```

### Error Handling
Common error codes:
- 400: Bad request (invalid input)
- 401: Unauthorized (invalid/expired token)
- 404: Not found (invalid chat/message ID)
- 500: Server error

### Rate Limiting
- Current limit: None (to be implemented)
- Future limits will be communicated via response headers

### Development Setup
1. Configure frontend environment:
```bash
# .env
VITE_API_URL=http://localhost:8000  # or your Django server URL
```

2. Enable CORS for your domain:
   - Add your frontend URL to `CORS_ALLOWED_ORIGINS`
   - Or set `FRONTEND_URL` environment variable in Django

3. Handle SSE reconnection:
```javascript
function createEventSource(url, token) {
    const es = new EventSource(url, { withCredentials: true });
    
    es.onerror = (error) => {
        es.close();
        setTimeout(() => createEventSource(url, token), 1000);
    };
    
    return es;
}
```

### Production Considerations
1. Use secure WebSocket when available
2. Implement proper error boundaries
3. Add request timeouts
4. Handle token refresh
5. Implement proper loading states
6. Cache chat history appropriately