"""Tool wrapper implementations for monitoring and caching."""

import time
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from .mcp_client import MCPRequest, MCPResponse
from .cache import cache

logger = logging.getLogger(__name__)

@dataclass
class ToolMetrics:
    """Metrics for tool usage."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_time: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    def record_success(self, duration: float) -> None:
        """Record a successful tool execution."""
        self.total_calls += 1
        self.successful_calls += 1
        self.total_time += duration
        
    def record_error(self, error: str) -> None:
        """Record a failed tool execution."""
        self.total_calls += 1
        self.failed_calls += 1
        self.last_error = error
        self.last_error_time = datetime.utcnow()
        
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
        
    @property
    def average_time(self) -> float:
        """Calculate average execution time."""
        if self.successful_calls == 0:
            return 0.0
        return self.total_time / self.successful_calls

class MonitoredTool:
    """Wrapper for monitoring tool execution."""
    
    def __init__(self, tool: Any):
        self.tool = tool
        self.metrics = ToolMetrics()
        
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """Process request with monitoring."""
        start_time = time.time()
        try:
            response = await self.tool.process_request(request)
            duration = time.time() - start_time
            
            if response.status == "success":
                self.metrics.record_success(duration)
            else:
                error_msg = response.error.get("message", "Unknown error") if response.error else "Unknown error"
                self.metrics.record_error(error_msg)
                
            return response
            
        except Exception as e:
            self.metrics.record_error(str(e))
            return MCPResponse(
                status="error",
                error={
                    "code": "MONITORED_TOOL_ERROR",
                    "message": str(e)
                }
            )

class CachedTool:
    """Wrapper for caching tool results."""
    
    def __init__(self, tool: Any, cache_ttl: int = 3600):
        self.tool = tool
        self.cache_ttl = cache_ttl
        
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """Process request with caching."""
        # Generate cache key
        cache_key = f"tool:{self.tool.__class__.__name__}:{hash(f'{request.method}:{request.params}')}"
        
        # Try to get from cache
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response
            
        # Execute tool
        response = await self.tool.process_request(request)
        
        # Cache successful responses
        if response.status == "success":
            cache.set(cache_key, response, expiry=self.cache_ttl)
            
        return response

def wrap_tool(tool: Any, enable_monitoring: bool = True, enable_caching: bool = True, 
              cache_ttl: int = 3600) -> Any:
    """Wrap a tool with monitoring and/or caching."""
    wrapped_tool = tool
    
    if enable_monitoring:
        wrapped_tool = MonitoredTool(wrapped_tool)
        
    if enable_caching:
        wrapped_tool = CachedTool(wrapped_tool, cache_ttl)
        
    return wrapped_tool