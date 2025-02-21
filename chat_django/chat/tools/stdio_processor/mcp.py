from typing import Dict, Any, Optional, AsyncGenerator
import json
import asyncio
import logging
from dataclasses import dataclass
from ...mcp_client import MCPRequest, MCPResponse

logger = logging.getLogger(__name__)

@dataclass
class StdioMCP:
    """MCP for processing data through stdio"""
    
    def __init__(self, user_id: str, chat_id: Optional[str] = None, message_id: Optional[str] = None):
        self.user_id = user_id
        self.chat_id = chat_id
        self.message_id = message_id
        self.capabilities = {
            "process": {
                "input_types": ["text"],
                "output_types": ["stream"]
            }
        }
        
    async def process_stdio(self, command: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process data through stdio and yield results
        
        Args:
            command: Command to execute
            
        Yields:
            Dictionary containing processed data chunks
        """
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Process stdout
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                    
                try:
                    # Try to parse as JSON
                    data = json.loads(line)
                except json.JSONDecodeError:
                    # If not JSON, wrap as text
                    data = {"text": line.decode().strip()}
                    
                yield {
                    "type": "stdio_data",
                    "data": data,
                    "metadata": {
                        "user_id": self.user_id,
                        "chat_id": self.chat_id,
                        "message_id": self.message_id
                    }
                }
            
            # Process stderr
            stderr_data = await process.stderr.read()
            if stderr_data:
                yield {
                    "type": "stdio_error",
                    "data": {"error": stderr_data.decode().strip()},
                    "metadata": {
                        "user_id": self.user_id,
                        "chat_id": self.chat_id,
                        "message_id": self.message_id
                    }
                }
            
            # Wait for process to complete
            await process.wait()
            
        except Exception as e:
            logger.error(f"Error in stdio processing: {e}")
            yield {
                "type": "stdio_error",
                "data": {"error": str(e)},
                "metadata": {
                    "user_id": self.user_id,
                    "chat_id": self.chat_id,
                    "message_id": self.message_id
                }
            }
    
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """Process an MCP-style request
        
        Args:
            request: The MCP request containing method and params
            
        Returns:
            MCPResponse with results or error
        """
        try:
            if request.method == "get_capabilities":
                return MCPResponse(
                    status="success",
                    data={"capabilities": self.capabilities}
                )
                
            elif request.method == "process_stdio":
                command = request.params.get("command")
                if not command:
                    return MCPResponse(
                        status="error",
                        error={
                            "code": "MISSING_PARAM",
                            "message": "command parameter is required"
                        }
                    )
                
                # Start processing - this will be handled by the streaming interface
                return MCPResponse(
                    status="success",
                    data={
                        "message": "Processing started",
                        "command": command
                    }
                )
                
            else:
                return MCPResponse(
                    status="error",
                    error={
                        "code": "INVALID_METHOD",
                        "message": f"Unknown method: {request.method}"
                    }
                )
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return MCPResponse(
                status="error",
                error={
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            )