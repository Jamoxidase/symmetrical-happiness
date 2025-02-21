"""MCP Client Implementation for Chat App"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from anthropic import Anthropic
from .mcp_manager import MCPManager, ServerConfig

@dataclass
class MCPRequest:
    """MCP-style request format"""
    method: str
    params: Dict[str, Any]

@dataclass
class MCPResponse:
    """MCP-style response format"""
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None

logger = logging.getLogger(__name__)

@dataclass
class ChatContext:
    """Context information for chat interactions"""
    user_id: str
    chat_id: Optional[str] = None
    message_id: Optional[str] = None

class ChatMCPClient:
    """MCP-compliant chat client implementation that supports multiple MCP servers"""
    
    def __init__(self):
        """Initialize the chat client"""
        self.mcp = MCPManager()
        self.anthropic = Anthropic()
        self.servers: Dict[str, Dict[str, Any]] = {}
        
    async def add_server(self, config: ServerConfig) -> None:
        """Add and connect to an MCP server
        
        Args:
            config: Server configuration
        """
        await self.mcp.connect_server(config)
        self.servers[config.name] = {
            "config": config,
            "capabilities": self.mcp.get_server_capabilities(config.name)
        }
        logger.info(f"Added server {config.name} with capabilities: {self.servers[config.name]['capabilities']}")
    
    async def process_query(self, query: str, context: ChatContext) -> str:
        """Process a query using Claude and available tools
        
        Args:
            query: The user's query
            context: Chat context information
            
        Returns:
            Formatted response string
        """
        if not self.servers:
            raise RuntimeError("No MCP servers connected")

        messages = [{"role": "user", "content": query}]

        # Get available tools from all servers
        available_tools = []
        for server_name in self.servers:
            tools = await self.mcp.list_tools(server_name)
            for tool in tools:
                available_tools.append({
                    "name": f"{server_name}.{tool.name}",
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })

        # Initial Claude call
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        final_text = []
        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
            elif content.type == 'tool_use':
                # Parse server and tool name
                server_name, tool_name = content.name.split('.', 1)
                tool_args = content.input
                
                # Add context to tool args
                if isinstance(tool_args, dict):
                    tool_args['context'] = {
                        'user_id': context.user_id,
                        'chat_id': context.chat_id,
                        'message_id': context.message_id
                    }
                
                try:
                    # Execute tool with progress handling
                    final_text.append(
                        f"[Calling {server_name}.{tool_name} with args {tool_args}]"
                    )
                    
                    def progress_callback(msg: str, pct: float):
                        final_text.append(
                            f"[{server_name}.{tool_name} Progress: {msg} ({pct*100:.0f}%)]"
                        )
                    
                    result = await self.mcp.call_tool(
                        server_name,
                        tool_name,
                        tool_args,
                        progress_callback=progress_callback
                    )

                    # Continue conversation with results
                    messages.extend([
                        {
                            "role": "assistant",
                            "content": content.text
                        } if hasattr(content, 'text') and content.text else None,
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": result
                                }
                            ]
                        }
                    ])

                    # Get next response
                    response = self.anthropic.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        messages=[m for m in messages if m is not None],
                        tools=available_tools
                    )
                    final_text.append(response.content[0].text)
                    
                except Exception as e:
                    error_msg = f"Error in {server_name}.{tool_name}: {str(e)}"
                    logger.error(error_msg)
                    final_text.append(f"[{error_msg}]")

        return "\n".join(final_text)

    async def cleanup(self):
        """Clean up all server connections"""
        await self.mcp.cleanup()