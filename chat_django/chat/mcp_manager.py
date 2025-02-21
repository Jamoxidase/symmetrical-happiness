"""MCP Server Manager for Chat Application"""
import asyncio
import logging
from typing import Dict, Optional, List, Any
from contextlib import AsyncExitStack
from dataclasses import dataclass, field

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import mcp.types as types

logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    capabilities: Dict[str, Any] = field(default_factory=dict)

class MCPManager:
    """Manages multiple MCP server connections"""
    
    def __init__(self):
        """Initialize the MCP manager"""
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.capabilities: Dict[str, Dict[str, Any]] = {}
        
    async def connect_server(self, config: ServerConfig) -> None:
        """Connect to an MCP server
        
        Args:
            config: Server configuration
        """
        logger.info(f"Connecting to MCP server: {config.name}")
        
        try:
            # Initialize server process
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env
            )
            
            # Create transport
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            
            # Create and initialize session
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio_transport[0], stdio_transport[1])
            )
            
            # Initialize MCP session
            init_result = await session.initialize()
            self.capabilities[config.name] = init_result.capabilities
            
            # Store session
            self.sessions[config.name] = session
            
            logger.info(f"Successfully connected to {config.name}")
            logger.debug(f"Server capabilities: {init_result.capabilities}")
            
        except Exception as e:
            logger.error(f"Failed to connect to {config.name}: {e}")
            raise
    
    async def list_tools(self, server_name: str) -> List[types.Tool]:
        """List available tools from a server
        
        Args:
            server_name: Name of the server
            
        Returns:
            List of available tools
        """
        if server_name not in self.sessions:
            raise ValueError(f"Server not found: {server_name}")
            
        session = self.sessions[server_name]
        response = await session.list_tools()
        return response.tools
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Call a tool on a server
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tool execution results
        """
        if server_name not in self.sessions:
            raise ValueError(f"Server not found: {server_name}")
            
        session = self.sessions[server_name]
        
        try:
            # Set up progress handling if callback provided
            if progress_callback:
                session.set_notification_handler(
                    "$/progress",
                    lambda notification: progress_callback(
                        notification.params["message"],
                        notification.params["percentage"]
                    )
                )
            
            # Call tool
            result = await session.call_tool(tool_name, arguments)
            return result.content
            
        except types.McpError as e:
            logger.error(f"MCP error in {server_name}.{tool_name}: {e.code} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"Error in {server_name}.{tool_name}: {e}")
            raise
    
    def get_server_capabilities(self, server_name: str) -> Dict[str, Any]:
        """Get capabilities of a server
        
        Args:
            server_name: Name of the server
            
        Returns:
            Server capabilities
        """
        if server_name not in self.capabilities:
            raise ValueError(f"Server not found: {server_name}")
            
        return self.capabilities[server_name]
    
    async def cleanup(self):
        """Clean up all server connections"""
        await self.exit_stack.aclose()