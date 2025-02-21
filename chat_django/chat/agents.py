import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging
import anthropic
from .prompts import PLANNING_PROMPT, USER_FACING_PROMPT
from .chat_types import ChatMessage

logger = logging.getLogger(__name__)

class PlanningAgent:
    """Stateless planning agent that determines next steps in chat processing"""
    
    def __init__(self, api_key: str, model_name: str, base_url: str):
        logger.debug(f"Initializing PlanningAgent with model: {model_name}")
        if not model_name:
            raise ValueError("Model name must be specified")
            
        self.client = anthropic.Anthropic(
            base_url=base_url,
            api_key=api_key
        )
        self.model_name = model_name

    def _format_planning_prompt(
        self,
        user_input: str,
        accumulated_data: List[Any],
        last_response: Optional[str],
        recent_messages: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Format the planning prompt with all context"""
        content_parts = [f"Original query: {user_input}"]
        
        # Add recent context if available
        if recent_messages and len(recent_messages) >= 2:
            last_pair = recent_messages[-2:]
            history_context = [
                f"{msg['role']}: {msg['content']}" 
                for msg in last_pair
                if msg['content'].strip()
            ]
            if history_context:
                content_parts.append("Last chat exchange:\n" + "\n".join(history_context))
        
        # Add accumulated data
        if accumulated_data:
            data_str = "\n".join(str(data) for data in accumulated_data)
            content_parts.append(f"Data collected so far:\n{data_str}")
        
        # Add last planning response
        if last_response:
            content_parts.append(f"Last planning step:\n{last_response}")
        
        return "\n\n".join(content_parts)

    def get_next_step(
        self,
        user_input: str,
        accumulated_data: List[Any],
        last_response: Optional[str] = None,
        recent_messages: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Get the next step in processing the request"""
        messages = [{
            "role": "user", 
            "content": self._format_planning_prompt(
                user_input, 
                accumulated_data, 
                last_response,
                recent_messages
            )
        }]
        
        logger.debug(f"Making planning request with model: {self.model_name}")
        logger.debug(f"Using base_url: {self.client.base_url}")
        
        request_payload = {
            'model': self.model_name,
            'max_tokens': 1000,
            'temperature': 0,
            'system': PLANNING_PROMPT,
            'messages': messages
        }
        logger.debug(f"Request payload: {json.dumps(request_payload, indent=2)}")
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                temperature=0,
                system=PLANNING_PROMPT,
                messages=messages
            )
        except Exception as e:
            logger.error(f"Error making API request: {str(e)}")
            logger.error(f"Request details: base_url={self.client.base_url}, model={self.model_name}")
            raise
            
        return response.content[0].text

class UserFacingAgent:
    """Stateless agent for generating user-facing responses"""
    
    def __init__(self, api_key: str, model_name: str, base_url: str):
        logger.debug(f"Initializing UserFacingAgent with model: {model_name}")
        if not model_name:
            raise ValueError("Model name must be specified")
            
        self.client = anthropic.Anthropic(
            base_url=base_url,
            api_key=api_key
        )
        self.model_name = model_name

    def _get_system_prompt(self, tool_results: List[Any]) -> str:
        """Get system prompt with tool results context"""
        return f"{USER_FACING_PROMPT}\n\nTool results:\n{json.dumps(tool_results, indent=2)}"

    async def stream_response(
        self,
        user_input: str,
        chat_history: List[Dict[str, Any]],
        tool_results: List[Any]
    ) -> AsyncGenerator[str, None]:
        """Stream a response for the user's input"""
        try:
            # Format messages with recent history
            messages = []
            if chat_history:
                # Use last 3 pairs (6 messages) for context
                recent_history = chat_history[-6:]
                for msg in recent_history:
                    if msg['content'].strip():
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # Add current user input
            messages.append({"role": "user", "content": user_input})
            
            # Start response
            yield json.dumps({
                'type': 'start_response',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Stream the response
            logger.debug(f"Starting user response stream with model: {self.model_name}")
            with self.client.messages.stream(
                model=self.model_name,  # Use model from request
                max_tokens=1500,
                temperature=0.7,
                system=self._get_system_prompt(tool_results),
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    yield json.dumps({
                        'type': 'token',
                        'content': text,
                        'timestamp': datetime.utcnow().isoformat()
                    })
            
            # End response
            yield json.dumps({
                'type': 'end_response',
                'timestamp': datetime.utcnow().isoformat()
            })
                    
        except Exception as e:
            logger.error(f"Error streaming response: {str(e)}")
            yield json.dumps({
                'type': 'error',
                'content': f"Error generating response: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            })