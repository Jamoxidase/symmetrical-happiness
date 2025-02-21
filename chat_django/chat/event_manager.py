import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder

class EventManager:
    """Manages SSE event queue for a chat session."""
    
    def __init__(self):
        self.queue = asyncio.Queue()
        
    async def add_event(self, event_type: str, data: Dict[str, Any]):
        """Add an event to the queue."""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.queue.put(self._format_sse_event(event))
    
    def _format_sse_event(self, event: Dict[str, Any]) -> str:
        """Format event as SSE data."""
        return f"data: {json.dumps(event, cls=DjangoJSONEncoder)}\n\n"
    
    async def get_events(self) -> AsyncGenerator[str, None]:
        """Stream events from the queue."""
        while True:
            try:
                event = await self.queue.get()
                yield event
                self.queue.task_done()
            except asyncio.CancelledError:
                break

# Global event manager registry
_event_managers = {}

def get_event_manager(chat_id: str) -> EventManager:
    """Get or create event manager for a chat session."""
    if chat_id not in _event_managers:
        _event_managers[chat_id] = EventManager()
    return _event_managers[chat_id]

def cleanup_event_manager(chat_id: str):
    """Remove event manager when chat is complete."""
    if chat_id in _event_managers:
        del _event_managers[chat_id]